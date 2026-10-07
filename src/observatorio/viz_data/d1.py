"""Datasets de visualización del dashboard D1 · México en el largo plazo."""

from __future__ import annotations

import polars as pl

from observatorio.catalog import Catalog
from observatorio.paths import Paths
from observatorio.pipeline import indicator_values, load_current
from observatorio.transform import LineageStep, get_transform
from observatorio.transform.groups import resolve_group
from observatorio.viz_data.common import ChartSpec, write_chart

PIB_PC = "eco.actividad.ingreso_pc.pib_pc_ppa"
PIB_PC_REL = "eco.actividad.ingreso_pc.relativo_eeuu"
POB = "dem.poblacion.tamano.total"
DEP = "dem.poblacion.estructura.razon_dependencia"
WPP_ULTIMO_ESTIMADO = "2023"  # WPP 2024: estimaciones hasta 2023; desde 2024 todo es proyección
FOCO = "MEX"


def _named(df: pl.DataFrame, catalog: Catalog) -> pl.DataFrame:
    names = {g: catalog.geo_name(g) for g in df["geo_id"].unique().to_list()}
    return df.with_columns(pl.col("geo_id").replace_strict(names).alias("nombre"))


def _events(catalog: Catalog, geo: str) -> list[dict]:
    return [{"id": e.id, "inicio": e.fecha_inicio, "fin": e.fecha_fin, "titulo": e.titulo,
             "descripcion": e.descripcion, "fuentes": e.fuentes}
            for e in catalog.events.values() if geo in e.geo]


def build(paths: Paths, catalog: Catalog) -> list[str]:
    obs = load_current(paths)
    pib = indicator_values(obs, catalog, PIB_PC)
    pob = indicator_values(obs, catalog, POB)
    values = {PIB_PC: pib, POB: pob}

    alc = resolve_group(catalog, "G.ALC_CEPAL33", values)
    grandes = resolve_group(catalog, "G.ALC_GRANDES", values)
    contraste = resolve_group(catalog, "G.CONTRASTE", values)
    built = []

    # 1.1 · Ingreso per cápita: México dentro de la distribución de ALC
    dist_fn = get_transform("distribucion_grupo@1")
    dist = dist_fn(pib, alc, poblacion=pob, cobertura_minima=0.8)
    paises = _named(pib.filter(pl.col("geo_id").is_in(sorted(set(grandes) | {FOCO})))
                    .select("geo_id", "period", "value"), catalog)
    spec = ChartSpec(
        chart_id="d1/ingreso-pc-alc",
        question=("¿Cómo ha evolucionado el PIB per cápita de México respecto a la "
                  "distribución de los países de América Latina y el Caribe?"),
        indicators=[PIB_PC, POB],
        caveats=[
            "PIB per cápita en PPA de 2021 a precios constantes: mide producción por "
            "persona, no ingreso de los hogares ni bienestar.",
            "Mediana y cuartiles no ponderados de los 33 países de CEPAL (cada país cuenta "
            "igual). Se omiten los años en que los países con dato suman menos del 80 % de "
            "la población regional.",
            "Algunos países (p. ej., Venezuela) no tienen dato en años recientes: la "
            "composición de la distribución cambia en el tiempo.",
        ],
        transformations=[LineageStep("distribucion_grupo@1",
                                     {"grupo": "G.ALC_CEPAL33", "ponderacion": "ninguna",
                                      "cobertura_minima_poblacion": 0.8},
                                     [PIB_PC, POB]).to_dict()],
        groups={"G.ALC_CEPAL33": alc, "G.ALC_GRANDES": grandes},
    )
    write_chart(paths, catalog, spec, {"distribucion": dist, "paises": paises},
                extra={"foco": FOCO, "eventos": _events(catalog, FOCO),
                       "grupo_lineas": grandes})
    built.append(spec.chart_id)

    # 1.2 · PIB per cápita relativo a EE.UU.: México frente a países de contraste
    ratio_fn = get_transform("razon_geo@1")
    rel = ratio_fn(pib, geo_denominador="USA", escala=100)
    sel = sorted(set(contraste) | {FOCO})
    rel_sel = _named(rel.filter(pl.col("geo_id").is_in(sel)).select("geo_id", "period", "value"),
                     catalog)
    spec2 = ChartSpec(
        chart_id="d1/ingreso-relativo-contraste",
        question=("¿Cómo ha cambiado el PIB per cápita de México respecto al de Estados Unidos, "
                  "comparado con países de trayectorias muy distintas?"),
        indicators=[PIB_PC_REL],
        caveats=[
            "Indicador relativo: una caída puede deberse a menor crecimiento del país o a "
            "mayor crecimiento de Estados Unidos.",
            "Los países de contraste no son pares de México: se muestran para ampliar la "
            "perspectiva, no como modelo.",
            "La calidad estadística varía entre países (ver la nota del grupo G.CONTRASTE).",
        ],
        transformations=[LineageStep("razon_geo@1", {"geo_denominador": "USA", "escala": 100},
                                     [PIB_PC]).to_dict()],
        groups={"G.CONTRASTE": contraste},
    )
    write_chart(paths, catalog, spec2, {"relativo": rel_sel},
                extra={"foco": FOCO, "paneles": contraste,
                       "nota_grupo": catalog.groups["G.CONTRASTE"].nota})
    built.append(spec2.chart_id)

    # 1.4 · Razón de dependencia de México: estimaciones y proyección probabilística de la ONU
    def serie(code: str, name: str) -> pl.DataFrame:
        return (obs.filter((pl.col("series_id") == code) & (pl.col("geo_id") == FOCO))
                .select("period", pl.col("value").alias(name)))

    observado = (serie("wb_wdi:SP.POP.DPND", "value")
                 .filter(pl.col("period") <= WPP_ULTIMO_ESTIMADO).sort("period"))
    proyeccion = serie("onu_wpp_prob:TotalDepRatio.15-64.MED", "mediana")
    for var in ("L80", "U80", "L95", "U95"):
        proyeccion = proyeccion.join(serie(f"onu_wpp_prob:TotalDepRatio.15-64.{var}", var.lower()),
                                     on="period", how="left")
    proyeccion = proyeccion.sort("period")
    combinada = pl.concat([
        observado.select("period", "value", pl.lit(False).alias("es_proyeccion")),
        proyeccion.select("period", pl.col("mediana").alias("value"),
                          pl.lit(True).alias("es_proyeccion")),
    ])
    # Los valores de la ONU están truncados a enteros: el mínimo suele repetirse varios años.
    # Se reporta el tramo completo, no un año único (sería precisión falsa).
    vmin = combinada["value"].min()
    tramo = combinada.filter(pl.col("value") == vmin).sort("period")
    minimo = {"value": vmin, "desde": tramo["period"][0], "hasta": tramo["period"][-1],
              "es_proyeccion": bool(tramo["es_proyeccion"].all())}
    spec3 = ChartSpec(
        chart_id="d1/dependencia-mex",
        question=("¿Cómo ha cambiado la proporción entre población en edades dependientes y en edad de "
                  "trabajar en México, y cómo podría evolucionar según las proyecciones de la ONU?"),
        indicators=[DEP],
        caveats=[
            "Razón demográfica (0-14 y 65+ por cada 100 personas de 15-64): no mide quién trabaja ni "
            "quién depende económicamente de quién.",
            "Desde 2024 son proyecciones de la ONU (WPP 2024), no datos. Los intervalos de predicción "
            "provienen del modelo de la ONU y no incluyen choques no previstos ni cambios de política.",
            "WDI publica valores para 2024-2025, pero también son proyecciones de la ONU: por eso la "
            "parte estimada termina en 2023.",
            "El archivo probabilístico de la ONU trunca los valores a enteros (diferencia < 1 punto "
            "frente a WDI en 2024-2025).",
            "El mínimo marcado es el de la mediana proyectada (un tramo de años por el truncamiento a "
            "enteros); considerando los intervalos, su momento es todavía más incierto.",
        ],
        transformations=[LineageStep("empalme_por_periodo@1",
                                     {"estimacion": "wb_wdi:SP.POP.DPND hasta 2023",
                                      "proyeccion": "onu_wpp_prob mediana e intervalos desde 2024"},
                                     [DEP]).to_dict()],
        groups={},
    )
    write_chart(paths, catalog, spec3, {"observado": observado, "proyeccion": proyeccion},
                extra={"foco": FOCO, "minimo": minimo})
    built.append(spec3.chart_id)
    built += _bienestar(paths, catalog, obs, alc)
    return built


POBREZA = {"3.00": "bie.pobreza.internacional.linea_300", "4.20": "bie.pobreza.internacional.linea_420",
           "8.30": "bie.pobreza.internacional.linea_830"}
GINI = "bie.desigualdad.ingreso.gini_encuestas"


def _with_segments(df: pl.DataFrame) -> pl.DataFrame:
    """Numera tramos comparables: cada ruptura (B) inicia un tramo nuevo."""
    return df.sort("period").with_columns(
        (pl.col("obs_status") == "B").cast(pl.Int32).cum_sum().alias("tramo"))


def _bienestar(paths: Paths, catalog: Catalog, obs: pl.DataFrame, alc: list[str]) -> list[str]:
    built: list[str] = []
    if not obs.filter(pl.col("series_id").str.starts_with("wb_pip:")).height:
        return built  # PIP aún no publicado (lockfile sin wb_pip)
    # 1.5 · Pobreza en México con líneas internacionales (ingreso, cobertura nacional)
    frames = []
    for line in POBREZA:
        sid = f"wb_pip:pobreza_{line}.ingreso.nacional"
        frames.append(_with_segments(
            obs.filter((pl.col("series_id") == sid) & (pl.col("geo_id") == FOCO))
            .select("period", "value", "obs_status")).with_columns(pl.lit(line).alias("linea")))
    pobreza = pl.concat(frames)
    rupturas = (pobreza.filter(pl.col("obs_status") == "B").select("period").unique().sort("period")
                ["period"].to_list())
    breaks = [b for b in catalog.datasets["wb_pip"].rupturas_conocidas if "pobreza" in b.serie]
    spec = ChartSpec(
        chart_id="d1/pobreza-mex",
        question=("¿Qué proporción de la población de México vive bajo las líneas internacionales de "
                  "pobreza del Banco Mundial, y cómo ha cambiado?"),
        indicators=list(POBREZA.values()),
        caveats=[
            "Líneas internacionales en dólares PPA 2021 por persona y día (US$3.00, 4.20 y 8.30); no es "
            "la medición oficial de pobreza de México (multidimensional, INEGI), que usa otro concepto.",
            "Pobreza por ingreso según encuestas de hogares (ENIGH); las encuestas no captan bien los "
            "ingresos más altos ni algunos ingresos no monetarios.",
            "La línea se corta donde cambia la encuesta: entre 2014 y 2016 se pasó de la ENIGH tradicional "
            "a la ENIGH Nueva Serie. La diferencia entre ambos lados mezcla cambio real y cambio de "
            "medición, y no debe leerse como reducción de la pobreza.",
            "Solo años con encuesta (bienal); no se interpolan los años intermedios.",
        ],
        transformations=[LineageStep("tramos_comparables@1",
                                     {"criterio": "comparable_spell de PIP (obs_status B inicia tramo)"},
                                     list(POBREZA.values())).to_dict()],
    )
    write_chart(paths, catalog, spec, {"pobreza": pobreza},
                extra={"foco": FOCO, "rupturas": rupturas,
                       "notas_ruptura": [b.descripcion for b in breaks]})
    built.append(spec.chart_id)

    # 1.6 · Gini en ALC: alrededor de 2000 vs último dato (ingreso)
    filas, excluidos = [], []
    for geo in alc:
        for cobertura in ("nacional", "urbano"):
            sid = f"wb_pip:gini.ingreso.{cobertura}"
            g = obs.filter((pl.col("series_id") == sid) & (pl.col("geo_id") == geo)).sort("period")
            if g.is_empty():
                continue
            years = g["period"].cast(pl.Int32)
            ini = g.filter(years.is_between(1998, 2003)).with_columns(
                (pl.col("period").cast(pl.Int32) - 2000).abs().alias("_d")).sort("_d", "period")
            fin = g.filter(years >= 2019).tail(1)
            if ini.is_empty() or fin.is_empty():
                continue
            a, b = ini.row(0, named=True), fin.row(0, named=True)
            entre = g.filter(pl.col("period").cast(pl.Int32).is_between(int(a["period"]) + 1,
                                                                        int(b["period"])))
            filas.append({"geo_id": geo, "nombre": catalog.geo_name(geo), "cobertura": cobertura,
                          "anio_inicio": a["period"], "inicio": a["value"],
                          "anio_fin": b["period"], "fin": b["value"],
                          "ruptura": bool((entre["obs_status"] == "B").any())})
            break
        else:
            excluidos.append(catalog.geo_name(geo))
    gini = pl.DataFrame(filas).sort("fin")
    urbanos = [f["nombre"] for f in filas if f["cobertura"] == "urbano"]
    rupt = [f["nombre"] for f in filas if f["ruptura"]]
    spec2 = ChartSpec(
        chart_id="d1/gini-alc",
        question=("¿Cómo cambió la desigualdad del ingreso medida por encuestas en los países de América "
                  "Latina entre alrededor de 2000 y el dato más reciente?"),
        indicators=[GINI],
        caveats=[
            "Gini de ingreso según encuestas de hogares: subestima la concentración porque las encuestas "
            "captan mal los ingresos más altos (las fuentes que usan datos fiscales, como WID, muestran "
            "más concentración). Esta gráfica compara encuestas con encuestas.",
            "Inicio: dato más cercano a 2000 entre 1998 y 2003; fin: dato más reciente desde 2019.",
            ("Con cambio de encuesta o método entre ambos puntos (punto final hueco): " + ", ".join(rupt)
             + ". En esos países el cambio mezcla variación real y cambio de medición.") if rupt else
            "Ningún país tiene cambio de encuesta entre ambos puntos.",
            ("Solo cobertura urbana: " + ", ".join(urbanos) + ".") if urbanos else
            "Todos los países con cobertura nacional.",
            "Sin dato de ingreso con la misma cobertura en ambos periodos (no aparecen): "
            + ", ".join(excluidos) + ".",
            "La dirección deseable de la desigualdad es un juicio normativo: los colores no la valoran.",
        ],
        groups={"G.ALC_CEPAL33": alc},
    )
    write_chart(paths, catalog, spec2, {"gini": gini}, extra={"foco": FOCO})
    built.append(spec2.chart_id)
    built += _definiciones_pobreza(paths, catalog, obs)
    built += _encuestas_vs_fiscales(paths, catalog, obs, alc)
    return built


def _tramos_texto(periodos: list[str]) -> str:
    """['1984', '1985', '1986', '2023', '2024'] → '1984–1986 y 2023–2024'."""
    años = sorted(int(p) for p in periodos)
    tramos: list[list[int]] = []
    for a in años:
        if tramos and a == tramos[-1][1] + 1:
            tramos[-1][1] = a
        else:
            tramos.append([a, a])
    partes = [f"{i}" if i == f else f"{i}–{f}" for i, f in tramos]
    return ", ".join(partes[:-1]) + (" y " if len(partes) > 1 else "") + partes[-1] if partes else ""


TOP10_ENC = "bie.desigualdad.ingreso.top10_encuestas"
TOP10_WID = "bie.desigualdad.ingreso.top10_ingreso_nacional"


def _encuestas_vs_fiscales(paths: Paths, catalog: Catalog, obs: pl.DataFrame, alc: list[str]) -> list[str]:
    """1.8–1.9 · Participación del 10 % superior: encuestas (PIP) vs cuentas distributivas (WID)."""
    enc_sid, wid_sid = "wb_pip:decil10.ingreso.nacional", "wid:top10"
    present = set(obs["series_id"].unique().to_list())
    if not {enc_sid, wid_sid} <= present:
        return []
    built = []
    enc = obs.filter((pl.col("series_id") == enc_sid) & (pl.col("geo_id") == FOCO))
    wid = obs.filter((pl.col("series_id") == wid_sid) & (pl.col("geo_id") == FOCO)
                     & (pl.col("period") >= "1984"))
    serie = pl.concat([
        _with_segments(enc.select("period", "value", "obs_status")).with_columns(
            pl.lit("encuesta").alias("fuente")),
        wid.select("period", "value", "obs_status").sort("period").with_columns(
            pl.lit(0, dtype=pl.Int32).alias("tramo"), pl.lit("wid").alias("fuente")),
    ])
    imputados = wid.filter(pl.col("obs_status") == "I")["period"].to_list()
    spec = ChartSpec(
        chart_id="d1/top10-mex",
        question=("¿Qué proporción del ingreso recibe el 10 % más rico de México según las encuestas de "
                  "hogares y según estimaciones que incorporan datos fiscales y cuentas nacionales?"),
        indicators=[TOP10_ENC, TOP10_WID],
        caveats=[
            "No miden exactamente lo mismo: la encuesta usa el ingreso per cápita del hogar; WID usa el "
            "ingreso nacional antes de impuestos de adultos (incluye ingresos no reportados en encuestas, "
            "como utilidades retenidas por empresas imputadas a sus dueños). La brecha refleja tanto la "
            "subcaptación de ingresos altos en encuestas como estas diferencias de concepto.",
            "Años imputados por WID por falta de fuentes (línea punteada, no son mediciones): "
            + (_tramos_texto(imputados) or "ninguno") + ".",
            "La serie de encuesta se corta en el cambio a la ENIGH Nueva Serie (2014–2016).",
            "Las estimaciones de WID dependen de supuestos de imputación que son objeto de debate académico.",
        ],
        transformations=[LineageStep("tramos_comparables@1", {"criterio": "comparable_spell (encuesta)"},
                                     [TOP10_ENC]).to_dict()],
    )
    rupturas = serie.filter(pl.col("obs_status") == "B")["period"].to_list()
    write_chart(paths, catalog, spec, {"serie": serie}, extra={"foco": FOCO, "rupturas": rupturas})
    built.append(spec.chart_id)

    # 1.9 · ALC: misma comparación, último año con ambas mediciones (WID medido, no imputado)
    filas = []
    for geo in alc:
        e = obs.filter((pl.col("series_id") == enc_sid) & (pl.col("geo_id") == geo)
                       & (pl.col("period") >= "2015"))
        w = obs.filter((pl.col("series_id") == wid_sid) & (pl.col("geo_id") == geo)
                       & (pl.col("obs_status") != "I"))
        j = e.select("period", pl.col("value").alias("enc")).join(
            w.select("period", pl.col("value").alias("wid")), on="period").sort("period")
        if j.height:
            r = j.row(-1, named=True)
            filas.append({"geo_id": geo, "nombre": catalog.geo_name(geo), "cobertura": "nacional",
                          "anio_inicio": r["period"], "inicio": r["enc"], "anio_fin": r["period"],
                          "fin": r["wid"], "ruptura": False})
    if filas:
        tabla = pl.DataFrame(filas).sort("fin")
        spec2 = ChartSpec(
            chart_id="d1/top10-alc",
            question=("¿Cuánto cambia la participación del 10 % más rico en América Latina cuando se "
                      "incorporan datos fiscales y cuentas nacionales a las encuestas?"),
            indicators=[TOP10_ENC, TOP10_WID],
            caveats=[
                "Último año desde 2015 en que ambas fuentes tienen dato y WID no está imputado; el año "
                "puede variar entre países.",
                "Conceptos distintos (ver la gráfica de México): la diferencia no es un error de una fuente.",
                "Solo países con encuesta de ingreso de cobertura nacional en PIP.",
            ],
            groups={"G.ALC_CEPAL33": alc},
        )
        write_chart(paths, catalog, spec2, {"gini": tabla}, extra={"foco": FOCO})
        built.append(spec2.chart_id)
    return built


DEFINICIONES = [
    ("oficial", "inegi_pm:pobreza", "bie.pobreza.oficial.multidimensional",
     "Pobreza multidimensional (oficial)",
     "Ingreso menor a la línea de pobreza por ingresos y al menos una de seis carencias sociales"),
    ("ingreso_oficial", "inegi_pm:ingreso_bajo_lpi", "bie.pobreza.oficial.ingreso_bajo_lpi",
     "Pobreza por ingresos (línea oficial)",
     "Ingreso menor al valor de las canastas alimentaria y no alimentaria de México"),
    ("cepal", "cepal_pobreza:pobreza.nacional", "bie.pobreza.cepal.pobreza",
     "Pobreza (metodología CEPAL)",
     "Ingreso menor a la línea de pobreza regional de CEPAL (canastas básicas por país)"),
    ("internacional", "wb_pip:pobreza_8.30.ingreso.nacional", "bie.pobreza.internacional.linea_830",
     "Línea internacional US$8.30 (Banco Mundial)",
     "Ingreso menor a US$8.30 diarios en PPA 2021, línea para países de ingreso medio-alto"),
]


def _definiciones_pobreza(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """1.7 · Tres definiciones de pobreza para México en el periodo común (2016–2024)."""
    present = set(obs["series_id"].unique().to_list())
    defs = [d for d in DEFINICIONES if d[1] in present]
    if len(defs) < 2:
        return []
    periodos = None
    paneles = []
    for key, sid, ind, titulo, definicion in defs:
        v = obs.filter((pl.col("series_id") == sid) & (pl.col("geo_id") == FOCO)).select(
            "period", "value", "obs_status")
        periodos = set(v["period"]) if periodos is None else periodos & set(v["period"])
        lo = obs.filter((pl.col("series_id") == f"{sid}.L95") & (pl.col("geo_id") == FOCO)).select(
            "period", pl.col("value").alias("lo"))
        hi = obs.filter((pl.col("series_id") == f"{sid}.U95") & (pl.col("geo_id") == FOCO)).select(
            "period", pl.col("value").alias("hi"))
        paneles.append((key, ind, titulo, definicion,
                        v.join(lo, on="period", how="left").join(hi, on="period", how="left")))
    comun = sorted(periodos or [])
    filas = pl.concat([
        p.filter(pl.col("period").is_in(comun)).with_columns(
            pl.lit(key).alias("medida"), pl.lit(titulo).alias("titulo"),
            pl.lit(definicion).alias("definicion"))
        for key, _, titulo, definicion, p in paneles]).sort("medida", "period")
    spec = ChartSpec(
        chart_id="d1/pobreza-definiciones",
        question="¿Cuánta pobreza hay en México? La respuesta depende de cómo se define.",
        indicators=[ind for _, ind, *_ in paneles],
        caveats=[
            "Cada cifra es correcta según su propia definición: no miden lo mismo y no deben "
            "promediarse ni elegirse una como 'la verdadera'.",
            f"Periodo común a todas las medidas ({comun[0]}–{comun[-1]}), todas con la ENIGH Nueva Serie.",
            "Las líneas oficiales de México son distintas para zonas urbanas y rurales y se actualizan con "
            "el valor de las canastas; la línea internacional es una sola cifra en dólares PPA.",
            "Solo el último año de la medición oficial trae intervalo de confianza al 95 % en el archivo de "
            "INEGI (barra vertical); los demás años también tienen error muestral.",
            "La medición oficial 2016–2022 es del CONEVAL y la de 2024 de INEGI, con la misma metodología "
            "según INEGI; la transferencia institucional se documenta en el catálogo de fuentes.",
        ],
        transformations=[LineageStep("periodo_comun@1", {"periodos": comun},
                                     [ind for _, ind, *_ in paneles]).to_dict()],
    )
    write_chart(paths, catalog, spec, {"medidas": filas},
                extra={"foco": FOCO, "orden": [k for k, *_ in paneles]})
    return [spec.chart_id]
