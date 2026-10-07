"""Datasets de visualización del dashboard D4 · Violencia letal y desapariciones.

Las cifras representan personas: solo agregados, lenguaje sobrio, sin adjetivos.
"""

from __future__ import annotations

import polars as pl

from observatorio.catalog import Catalog
from observatorio.paths import Paths
from observatorio.pipeline import indicator_values, load_current
from observatorio.transform import LineageStep, get_transform
from observatorio.transform.groups import resolve_group
from observatorio.viz_data.common import ChartSpec, write_chart

HOM = "seg.violencia_letal.homicidio.defunciones"
TASA = "seg.violencia_letal.homicidio.tasa"
TASA_INEGI = "seg.violencia_letal.homicidio.tasa_inegi"
POB = "dem.poblacion.tamano.total"
FOCO = "MEX"

# Agregados regionales del Banco Mundial (calculados por WDI con los datos de UNODC).
REGIONES = {
    "G.wb_wdi.WLD": "Mundo",
    "G.wb_wdi.LCN": "América Latina y el Caribe",
    "G.wb_wdi.SSF": "África subsahariana",
    "G.wb_wdi.NAC": "América del Norte",
    "G.wb_wdi.MEA": "Oriente Medio y Norte de África",
    "G.wb_wdi.SAS": "Asia meridional",
    "G.wb_wdi.ECS": "Europa y Asia central",
    "G.wb_wdi.EAS": "Asia oriental y Pacífico",
}


def _named(df: pl.DataFrame, catalog: Catalog) -> pl.DataFrame:
    names = {g: catalog.geo_name(g) for g in df["geo_id"].unique().to_list()}
    return df.with_columns(pl.col("geo_id").replace_strict(names).alias("nombre"))


def build(paths: Paths, catalog: Catalog) -> list[str]:
    obs = load_current(paths)
    built = []
    built += _serie_mexico(paths, catalog, obs)
    built += _mexico_alc(paths, catalog, obs)
    built += _regiones(paths, catalog, obs)
    built += _desaparecidas(paths, catalog, obs)
    built += _fuentes_homicidio(paths, catalog, obs)
    built += _mujeres(paths, catalog, obs)
    built += _entidades(paths, catalog, obs)
    built += _mensual(paths, catalog, obs)
    return built


def _serie_mexico(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.1 · Tasa de homicidio en México: UNODC (1990–) y cálculo propio con INEGI para los años
    que UNODC aún no publica. Se verifica que ambos coinciden en los años comunes."""
    pob = indicator_values(obs, catalog, POB)
    conteo = (obs.filter((pl.col("series_id") == "inegi_homicidios:Mortalidad_08.total")
                         & (pl.col("geo_id") == FOCO))
              .select("geo_id", "period", "period_start", "value", "obs_status"))
    per_capita = get_transform("per_capita@1")
    inegi = (per_capita(conteo.select("geo_id", "period", "period_start", "value"), pob, escala=100_000)
             .join(conteo.select("period", pl.col("value").alias("conteo"), "obs_status"), on="period"))
    unodc = (obs.filter((pl.col("series_id") == "wb_wdi:VC.IHR.PSRC.P5") & (pl.col("geo_id") == FOCO))
             .select("period", "value"))

    comunes = unodc.join(inegi.select("period", pl.col("value").alias("inegi")), on="period")
    max_dif = float(((comunes["inegi"] / comunes["value"]) - 1).abs().max())
    if max_dif > 0.01:  # si dejan de coincidir, el empalme ya no es válido
        raise ValueError(f"d4/homicidios-mex: INEGI y UNODC difieren hasta {max_dif:.1%}; revisar el empalme")
    ultimo_unodc = unodc["period"].max()
    serie = pl.concat([
        unodc.select("period", "value", pl.lit("A").alias("obs_status"), pl.lit("unodc").alias("fuente")),
        inegi.filter(pl.col("period") > ultimo_unodc)
        .select("period", "value", "obs_status", pl.lit("inegi").alias("fuente")),
    ]).join(conteo.select("period", pl.col("value").alias("conteo")), on="period", how="left").sort("period")

    prelim = inegi.filter(pl.col("obs_status") == "P")["period"].to_list()
    rango = (comunes["period"].min(), comunes["period"].max())
    spec = ChartSpec(
        chart_id="d4/homicidios-mex",
        question="¿Cómo ha evolucionado la tasa de homicidio en México desde 1990?",
        indicators=[TASA, TASA_INEGI, HOM, POB],
        caveats=[
            "Homicidios según el certificado de defunción (registro civil y sector salud), por año de "
            "registro: no son carpetas de investigación (SESNSP) ni incluyen a personas desaparecidas "
            "cuyo cuerpo no ha sido localizado.",
            f"{ultimo_unodc} y antes: tasa publicada por UNODC (vía Banco Mundial). Para México, UNODC "
            f"usa los registros de INEGI: en {rango[0]}–{rango[1]} la tasa de UNODC coincide con las "
            f"defunciones de INEGI divididas entre la población de la ONU (diferencia máxima {max_dif:.0e}). "
            "Por eso no son dos fuentes independientes: es una sola medición.",
            f"Después de {ultimo_unodc}: cálculo propio con las defunciones de INEGI y la población de la "
            "ONU (INEGI publica sus tasas con la población de CONAPO, ligeramente distinta). La población "
            "de los años más recientes es proyección de la ONU.",
            ("Cifras preliminares de INEGI (punto hueco): " + ", ".join(prelim) + ". Suelen revisarse al "
             "alza al concluir la confronta con la Secretaría de Salud; por ejemplo, 2019 pasó de 36,476 "
             "(preliminar) a 36,661 (definitiva).") if prelim else "Ninguna cifra preliminar.",
        ],
        transformations=[LineageStep("per_capita@1", {"poblacion": POB, "escala": 100_000},
                                     [HOM, POB]).to_dict()],
        series_usadas=["wb_wdi:VC.IHR.PSRC.P5", "inegi_homicidios:Mortalidad_08.total",
                       "wb_wdi:SP.POP.TOTL"],
    )
    write_chart(paths, catalog, spec, {"serie": serie},
                extra={"foco": FOCO, "ultimo_unodc": ultimo_unodc})
    return [spec.chart_id]


def _mexico_alc(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.2 · México dentro de la distribución de ALC (tasa UNODC)."""
    tasa = indicator_values(obs, catalog, TASA)
    pob = indicator_values(obs, catalog, POB)
    values = {TASA: tasa, POB: pob}
    alc = resolve_group(catalog, "G.ALC_CEPAL33", values)
    grandes = resolve_group(catalog, "G.ALC_GRANDES", values)
    dist = get_transform("distribucion_grupo@1")(tasa, alc, poblacion=pob, cobertura_minima=0.8)
    paises = _named(tasa.filter(pl.col("geo_id").is_in(sorted(set(grandes) | {FOCO})))
                    .select("geo_id", "period", "value"), catalog)
    sin_dato = sorted(catalog.geo_name(g) for g in alc
                      if tasa.filter((pl.col("geo_id") == g) & (pl.col("period") >= "2019")).is_empty())
    spec = ChartSpec(
        chart_id="d4/homicidios-alc",
        question=("¿Cómo se compara la tasa de homicidio de México con la de los países de América Latina "
                  "y el Caribe?"),
        indicators=[TASA, POB],
        caveats=[
            "UNODC compila cifras nacionales de salud pública o de justicia penal según el país; la "
            "cobertura y la calidad del registro varían, así que las diferencias pequeñas entre países no "
            "son significativas.",
            "Mediana y cuartiles no ponderados de los 33 países de CEPAL (cada país cuenta igual). Se omiten "
            "los años en que los países con dato suman menos del 80 % de la población regional.",
            ("Sin dato desde 2019: " + ", ".join(sin_dato) + ".") if sin_dato
            else "Todos los países tienen dato desde 2019.",
        ],
        transformations=[LineageStep("distribucion_grupo@1",
                                     {"grupo": "G.ALC_CEPAL33", "ponderacion": "ninguna",
                                      "cobertura_minima_poblacion": 0.8}, [TASA, POB]).to_dict()],
        groups={"G.ALC_CEPAL33": alc, "G.ALC_GRANDES": grandes},
        series_usadas=["wb_wdi:VC.IHR.PSRC.P5", "wb_wdi:SP.POP.TOTL"],
    )
    write_chart(paths, catalog, spec, {"distribucion": dist, "paises": paises},
                extra={"foco": FOCO, "eventos": [], "grupo_lineas": grandes})
    return [spec.chart_id]


def _regiones(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.3 · México frente a las regiones del mundo: 2010 y último año común."""
    tasa = indicator_values(obs, catalog, TASA)
    geos = [FOCO, *REGIONES]
    sel = tasa.filter(pl.col("geo_id").is_in(geos))
    inicio = "2010"
    fin = sel.group_by("geo_id").agg(pl.col("period").max())["period"].min()
    filas = []
    for geo in geos:
        g = sel.filter(pl.col("geo_id") == geo)
        a = g.filter(pl.col("period") == inicio)
        b = g.filter(pl.col("period") == fin)
        if a.is_empty() or b.is_empty():
            continue
        filas.append({"geo_id": geo, "nombre": REGIONES.get(geo) or catalog.geo_name(geo),
                      "cobertura": "nacional", "anio_inicio": inicio, "inicio": a["value"][0],
                      "anio_fin": fin, "fin": b["value"][0], "ruptura": False})
    tabla = pl.DataFrame(filas).sort("fin")
    spec = ChartSpec(
        chart_id="d4/homicidios-regiones",
        question="¿Cómo se compara la tasa de homicidio de México con la de las regiones del mundo?",
        indicators=[TASA],
        caveats=[
            "Agregados regionales calculados por el Banco Mundial con los datos de UNODC; incluyen "
            "estimaciones para países sin registro confiable, sobre todo en África subsahariana y Asia.",
            "Las regiones del Banco Mundial agrupan países muy distintos: el promedio regional oculta "
            "diferencias grandes entre países (p. ej., dentro de América Latina).",
            f"Se usa {fin} como último año porque es el más reciente con dato para todas las regiones.",
        ],
        groups={"regiones_banco_mundial": list(REGIONES)},
    )
    write_chart(paths, catalog, spec, {"filas": tabla}, extra={"foco": FOCO})
    return [spec.chart_id]


DESAP = "seg.desapariciones.registro.desaparecidas"
DESAP_ESTATUS = {
    "rnpdno:desaparecidas.total": "siguen_desaparecidas",
    "rnpdno:localizadas_sin_vida.total": "localizadas_sin_vida",
    "rnpdno:localizadas_con_vida.total": "localizadas_con_vida",
}
DESDE = "2000"


def _desaparecidas(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.4 · Personas reportadas como desaparecidas por año de desaparición y su estatus actual."""
    rn = obs.filter(pl.col("series_id").str.starts_with("rnpdno:") & (pl.col("geo_id") == FOCO))
    vintage = rn["vintage_id"].max()
    est = (rn.filter(pl.col("series_id").is_in(list(DESAP_ESTATUS)))
           .with_columns(pl.col("series_id").replace_strict(DESAP_ESTATUS).alias("estatus"))
           .select("period", "estatus", "value", "obs_status"))
    sexo = (rn.filter(pl.col("series_id").is_in(["rnpdno:desaparecidas.mujer",
                                                 "rnpdno:desaparecidas.hombre"]))
            .pivot(on="series_id", index="period", values="value")
            .rename({"rnpdno:desaparecidas.mujer": "mujeres", "rnpdno:desaparecidas.hombre": "hombres"}))
    anual = est.filter(pl.col("period") >= DESDE).sort("period", "estatus")
    total = est.group_by("period").agg(pl.col("value").sum())
    antes = int(total.filter(pl.col("period") < DESDE)["value"].sum())

    def suma(sid: str) -> int:
        return int(rn.filter(pl.col("series_id") == sid)["value"].sum())

    sin_anio_desap, sin_anio_todas = suma("rnpdno:desaparecidas.sin_anio"), suma("rnpdno:todas.sin_anio")
    desap_total, reportadas = suma("rnpdno:desaparecidas.total"), suma("rnpdno:todas.total")
    # Coherencia interna: los tres estatus suman el total de reportes de cada año.
    chk = total.join(rn.filter(pl.col("series_id") == "rnpdno:todas.total")
                     .select("period", pl.col("value").alias("todas")), on="period")
    if (chk["value"] != chk["todas"]).any():
        raise ValueError("d4/desaparecidas: los estatus no suman el total de reportes")
    prelim = sorted(anual.filter(pl.col("obs_status") == "P")["period"].unique().to_list())
    corte = f"{vintage[:4]}-{vintage[5:7]}-{vintage[8:10]}"
    # Posible rezago de carga: entidades cuyo año en curso tiene muy pocos registros frente al anterior.
    actual, anterior = corte[:4], str(int(corte[:4]) - 1)
    por_ent = (obs.filter((pl.col("series_id") == "rnpdno:desaparecidas.total")
                          & pl.col("geo_id").str.starts_with("MX-") & (pl.col("geo_id") != "MX-ND")
                          & pl.col("period").is_in([actual, anterior]))
               .pivot(on="period", index="geo_id", values="value").fill_null(0))
    rezago = []
    if {actual, anterior} <= set(por_ent.columns):
        ratios = por_ent.filter(pl.col(anterior) >= 100).with_columns(
            (pl.col(actual) / pl.col(anterior)).alias("r"))
        mediana = float(ratios["r"].median())
        rezago = [f"{catalog.geo_name(g)} ({int(a):,} en {actual} frente a {int(b):,} en {anterior})"
                  for g, a, b, r in ratios.select("geo_id", actual, anterior, "r").iter_rows()
                  if r < mediana / 4]
    spec = ChartSpec(
        chart_id="d4/desaparecidas-anio",
        question=("¿Cuántas personas reportadas como desaparecidas siguen sin ser localizadas, según el año "
                  "en que desaparecieron?"),
        indicators=[DESAP, "seg.desapariciones.registro.localizadas_con_vida",
                    "seg.desapariciones.registro.localizadas_sin_vida",
                    "seg.desapariciones.registro.reportadas"],
        caveats=[
            f"Instantánea del registro consultada el {corte}: el estatus de cada persona puede cambiar "
            "después (localización, depuración de duplicados, registros tardíos).",
            "Por año de desaparición: los años recientes han tenido menos tiempo para que las personas sean "
            "localizadas, así que la proporción que sigue desaparecida no es comparable entre años lejanos y "
            "recientes.",
            (f"{corte[:4]}: año en curso (de enero a la fecha de consulta). "
             + ", ".join(p for p in prelim if p != corte[:4])
             + ": el registro de reportes tardíos sigue en curso.") if prelim else "",
            "Antes de 2019 no existía un registro integrado; los años anteriores provienen del RNPED "
            "(SESNSP) normalizado por la CNB y están subregistrados.",
            "En 2023–2024 el gobierno federal revisó el registro con una metodología cuestionada por "
            "colectivos de familias y organismos de derechos humanos: instantáneas anteriores y posteriores "
            "pueden no ser comparables.",
            f"No se muestran: {antes:,} personas reportadas con año de desaparición anterior a {DESDE} y "
            f"{sin_anio_todas:,} sin año de desaparición ({sin_anio_desap:,} de ellas siguen desaparecidas). "
            f"Total en el registro: {reportadas + sin_anio_todas:,} personas reportadas, de las cuales "
            f"{desap_total + sin_anio_desap:,} siguen desaparecidas o no localizadas.",
            ("Posible rezago en la carga de registros del año en curso (menos de una cuarta parte de la "
             f"proporción típica entre entidades): {'; '.join(rezago)}. El total nacional de {actual} está "
             "subestimado en esa medida.") if rezago else "",
            "Es un registro administrativo: depende de que haya reporte o denuncia. No es una estimación "
            "del total de personas desaparecidas.",
        ],
        series_usadas=[*DESAP_ESTATUS, "rnpdno:todas.total", "rnpdno:desaparecidas.mujer",
                       "rnpdno:desaparecidas.hombre", "rnpdno:desaparecidas.sin_anio",
                       "rnpdno:todas.sin_anio"],
    )
    spec.caveats = [c for c in spec.caveats if c]
    write_chart(paths, catalog, spec,
                {"estatus": anual, "sexo": sexo.filter(pl.col("period") >= DESDE).sort("period")},
                extra={"corte": corte, "preliminares": prelim})

    # 4.4b · Acervo de personas desaparecidas por entidad (todos los años y sin año).
    sids = ["rnpdno:desaparecidas.total", "rnpdno:desaparecidas.sin_anio"]
    acervo = (obs.filter(pl.col("series_id").is_in(sids)
                         & pl.col("geo_id").str.starts_with("MX-"))
              .group_by("geo_id").agg(pl.col("value").sum().alias("personas"))
              .with_columns(pl.col("geo_id").map_elements(catalog.geo_name, return_dtype=pl.String)
                            .alias("nombre"))
              .sort("personas"))
    total_ent = int(acervo["personas"].sum())
    if total_ent != desap_total + sin_anio_desap:
        raise ValueError("d4/desaparecidas-entidades: la suma de entidades no coincide con el total nacional")
    spec2 = ChartSpec(
        chart_id="d4/desaparecidas-entidades",
        question=("¿En qué entidades se registró la desaparición de las personas que siguen sin ser "
                  "localizadas?"),
        indicators=[DESAP, "seg.desapariciones.registro.desaparecidas_sin_anio"],
        caveats=[
            f"Instantánea del registro consultada el {corte}; incluye todos los años de desaparición y los "
            "registros sin año.",
            "Conteos, no tasas: las entidades más pobladas tienden a tener más registros. Las tasas por "
            "habitante requieren la población por entidad de CONAPO (pendiente).",
            "La cifra depende también de la capacidad y disposición de cada fiscalía y comisión de búsqueda "
            "para registrar y actualizar casos; las diferencias entre entidades no miden solo la incidencia.",
            f"Suma de entidades = total nacional ({total_ent:,} personas), incluida 'entidad no "
            "especificada'.",
        ],
        series_usadas=["rnpdno:desaparecidas.total", "rnpdno:desaparecidas.sin_anio"],
        groups={"entidades_federativas": acervo["geo_id"].to_list()},
    )
    write_chart(paths, catalog, spec2, {"entidades": acervo}, extra={"corte": corte})
    return [spec.chart_id, spec2.chart_id]


def _serie(obs: pl.DataFrame, sid: str, nombre: str) -> pl.DataFrame:
    return (obs.filter((pl.col("series_id") == sid) & (pl.col("geo_id") == FOCO))
            .select("geo_id", "period", "period_start", "value", "obs_status",
                    pl.lit(nombre).alias("serie")))


def _largo(*partes: pl.DataFrame) -> pl.DataFrame:
    cols = ["period", "serie", "value", "obs_status"]
    return pl.concat([p.select(cols) for p in partes]).sort("serie", "period")


def _fuentes_homicidio(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.5 · Dos registros independientes: defunciones (INEGI) y carpetas de investigación (SESNSP).
    4.6 · Composición de las víctimas de delitos contra la vida en el SESNSP."""
    inegi = _serie(obs, "inegi_homicidios:Mortalidad_08.total", "inegi")
    dol = _serie(obs, "sesnsp_victimas:homicidio_doloso.total", "doloso")
    fem = _serie(obs, "sesnsp_victimas:feminicidio.total", "feminicidio")
    otros = _serie(obs, "sesnsp_victimas:otros_contra_la_vida.total", "otros")
    suma = get_transform("suma@1")
    sesnsp = (suma(dol, fem).join(dol.select("period", "obs_status"), on="period")
              .with_columns(pl.lit("sesnsp").alias("serie")))
    comunes = inegi.join(sesnsp.select("period", pl.col("value").alias("s")), on="period")
    brecha = comunes.with_columns(((pl.col("value") / pl.col("s") - 1) * 100).alias("dif"))
    bmin, bmax = brecha.sort("dif").row(0, named=True), brecha.sort("dif").row(-1, named=True)
    rango = f"{comunes['period'].min()}–{comunes['period'].max()}"
    prelim = inegi.filter(pl.col("obs_status") == "P")["period"].to_list()
    spec = ChartSpec(
        chart_id="d4/homicidios-fuentes",
        question=("¿Cuentan lo mismo los registros de defunciones (INEGI) y las carpetas de investigación "
                  "(SESNSP)?"),
        indicators=[HOM, "seg.violencia_letal.homicidio.victimas_doloso",
                    "seg.violencia_letal.feminicidio.victimas"],
        caveats=[
            "Miden cosas distintas: INEGI cuenta defunciones con causa de homicidio en el "
            "certificado (por año "
            "de registro); el SESNSP cuenta víctimas de homicidio doloso y feminicidio en carpetas de "
            "investigación de las fiscalías (por fecha de inicio de la carpeta). No incluyen homicidios "
            "culposos ni 'otros delitos contra la vida'.",
            f"En {rango} INEGI registra más que el SESNSP todos los años: la diferencia va de "
            f"{bmin['dif']:.1f} % ({bmin['period']}) a {bmax['dif']:.1f} % ({bmax['period']}). Causas "
            "documentadas en DIS-003; la diferencia no se atribuye a una sola causa.",
            ("Cifras preliminares de INEGI (punto hueco): " + ", ".join(prelim) + ".") if prelim else "",
            "Son registros de instituciones distintas en momentos distintos del proceso: que coincidan en la "
            "dirección del cambio es evidencia de que el cambio no es un artefacto de un solo registro.",
        ],
        transformations=[LineageStep("suma@1", {}, ["sesnsp_victimas:homicidio_doloso.total",
                                                    "sesnsp_victimas:feminicidio.total"]).to_dict()],
    )
    spec.caveats = [c for c in spec.caveats if c]
    write_chart(paths, catalog, spec, {"serie": _largo(inegi, sesnsp)})

    comp = _largo(dol, fem, otros)
    o0, o1 = otros.sort("period").row(0, named=True), otros.sort("period").row(-1, named=True)
    spec2 = ChartSpec(
        chart_id="d4/sesnsp-contra-la-vida",
        question=("¿Cómo han cambiado las víctimas registradas en cada tipo de delito contra la vida en las "
                  "carpetas de investigación?"),
        indicators=["seg.violencia_letal.homicidio.victimas_doloso",
                    "seg.violencia_letal.feminicidio.victimas",
                    "seg.violencia_letal.otros_contra_vida.victimas"],
        caveats=[
            f"'Otros delitos que atentan contra la vida y la integridad corporal' pasó de {o0['value']:,.0f} "
            f"víctimas en {o0['period']} a {o1['value']:,.0f} en {o1['period']}. Es una categoría "
            f"residual que "
            "agrupa delitos distintos según cada código penal; con estos datos no se puede "
            "saber qué parte, si alguna, corresponde a muertes que antes se habrían registrado como "
            "homicidio "
            "doloso. Responderlo requiere revisar los criterios de clasificación de cada fiscalía.",
            "El feminicidio es un tipo penal: su evolución mezcla cambios en la violencia y en la "
            "tipificación "
            "y aplicación por cada fiscalía.",
            "Víctimas en carpetas de investigación: dependen de la denuncia y de la clasificación de "
            "la fiscalía.",
        ],
    )
    write_chart(paths, catalog, spec2, {"serie": comp})
    return [spec.chart_id, spec2.chart_id]


def _mujeres(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.7 · Mujeres asesinadas: defunciones (INEGI) vs víctimas de homicidio doloso + feminicidio
    (SESNSP)."""
    inegi = _serie(obs, "inegi_homicidios:Mortalidad_08.mujeres", "inegi")
    dol = _serie(obs, "sesnsp_victimas:homicidio_doloso.mujer", "doloso_mujeres")
    fem = _serie(obs, "sesnsp_victimas:feminicidio.total", "feminicidio")
    sesnsp = (get_transform("suma@1")(dol, fem).join(dol.select("period", "obs_status"), on="period")
              .with_columns(pl.lit("sesnsp").alias("serie")))
    prop = (fem.select("period", pl.col("value").alias("f"))
            .join(sesnsp.select("period", pl.col("value").alias("t")), on="period")
            .with_columns((pl.col("f") / pl.col("t") * 100).alias("pct")).sort("period"))
    p0, p1 = prop.row(0, named=True), prop.row(-1, named=True)
    prelim = inegi.filter(pl.col("obs_status") == "P")["period"].to_list()
    spec = ChartSpec(
        chart_id="d4/mujeres",
        question=("¿Cuántas mujeres son asesinadas en México y cuántos de esos casos se investigan como "
                  "feminicidio?"),
        indicators=["seg.violencia_letal.homicidio.defunciones_mujeres",
                    "seg.violencia_letal.homicidio.victimas_doloso_mujeres",
                    "seg.violencia_letal.feminicidio.victimas"],
        caveats=[
            "Feminicidio (SESNSP) es un tipo penal que exige acreditar razones de género; las defunciones de "
            "mujeres por homicidio (INEGI) incluyen todos los asesinatos de mujeres. Ninguna de las "
            "dos cifras "
            "es 'el número de feminicidios' en sentido social o sociológico.",
            f"La proporción de víctimas mujeres registradas como feminicidio (sobre homicidio doloso "
            f"de mujeres + "
            f"feminicidio, SESNSP) pasó de {p0['pct']:.0f} % en {p0['period']} a {p1['pct']:.0f} % en "
            f"{p1['period']}: refleja también cambios en la tipificación y en las prácticas de las "
            f"fiscalías.",
            ("Cifras preliminares de INEGI (punto hueco): " + ", ".join(prelim) + ".") if prelim else "",
            "Los códigos penales estatales definen el feminicidio de forma distinta: las comparaciones entre "
            "entidades requieren cautela (no se muestran aquí).",
        ],
        transformations=[LineageStep("suma@1", {}, ["sesnsp_victimas:homicidio_doloso.mujer",
                                                    "sesnsp_victimas:feminicidio.total"]).to_dict()],
    )
    spec.caveats = [c for c in spec.caveats if c]
    write_chart(paths, catalog, spec, {"serie": _largo(inegi, sesnsp, fem)},
                extra={"proporcion_feminicidio": prop.select("period", "pct").to_dicts()})
    return [spec.chart_id]


ENT_DESDE, ENT_HASTA = "2021", "2024"  # años definitivos de INEGI más recientes


def _entidades(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.8 · Por entidad: diferencia INEGI–SESNSP y peso de "otros delitos contra la vida"."""
    import math

    ent = obs.filter(pl.col("geo_id").str.starts_with("MX-")
                     & pl.col("period").is_between(pl.lit(ENT_DESDE), pl.lit(ENT_HASTA)))

    def total(sid: str, name: str) -> pl.DataFrame:
        return (ent.filter(pl.col("series_id") == sid).group_by("geo_id")
                .agg(pl.col("value").sum().alias(name), pl.len().alias(f"n_{name}")))

    t = (total("inegi_homicidios:Mortalidad_08.total", "inegi")
         .join(total("sesnsp_victimas:homicidio_doloso.total", "doloso"), on="geo_id")
         .join(total("sesnsp_victimas:feminicidio.total", "feminicidio"), on="geo_id")
         .join(total("sesnsp_victimas:otros_contra_la_vida.total", "otros"), on="geo_id"))
    anios = int(ENT_HASTA) - int(ENT_DESDE) + 1
    completos = t.select(pl.all_horizontal(pl.col("^n_.*$") == anios)).to_series().all()
    if not completos or t.height != 32:
        raise ValueError("d4/entidades: faltan años o entidades")
    t = (t.select("geo_id", "inegi", "doloso", "feminicidio", "otros")
         .with_columns((pl.col("doloso") + pl.col("feminicidio")).alias("sesnsp"))
         .with_columns(((pl.col("inegi") - pl.col("sesnsp")) / pl.col("inegi") * 100).alias("brecha"),
                       (pl.col("otros") / pl.col("sesnsp") * 100).alias("otros_pct"))
         .with_columns(pl.col("geo_id").map_elements(catalog.geo_name, return_dtype=pl.String)
                       .alias("nombre"))
         .sort("brecha"))
    # Asociación entre entidades (Spearman) con intervalo aproximado de Fisher.
    r = float(t.select(pl.corr("brecha", "otros_pct", method="spearman")).item())
    z, se = math.atanh(r), 1 / math.sqrt(t.height - 3)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    periodo = f"{ENT_DESDE}–{ENT_HASTA}"
    neg = t.filter(pl.col("brecha") < 0)["nombre"].to_list()
    spec = ChartSpec(
        chart_id="d4/entidades-brecha",
        question=("¿En qué entidades difieren más las defunciones por homicidio (INEGI) y las víctimas en "
                  "carpetas de investigación (SESNSP), y se relaciona esa diferencia con el uso de la "
                  "categoría 'otros delitos contra la vida'?"),
        indicators=[HOM, "seg.violencia_letal.homicidio.victimas_doloso",
                    "seg.violencia_letal.feminicidio.victimas",
                    "seg.violencia_letal.otros_contra_vida.victimas"],
        caveats=[
            f"Suma de {periodo} (últimos años definitivos de INEGI). Diferencia = (INEGI − SESNSP) / INEGI; "
            "SESNSP = homicidio doloso + feminicidio.",
            "INEGI asigna la defunción a la entidad donde se registró; el SESNSP, a la fiscalía que abrió la "
            "carpeta. Una muerte puede registrarse en una entidad e investigarse en otra.",
            ("Diferencia negativa (el SESNSP registra más víctimas que defunciones INEGI): " + ", ".join(neg)
             + ". Puede deberse a carpetas sin cuerpo localizado o a diferencias de entidad y de año.")
            if neg else "",
            f"Asociación entre entidades (correlación de Spearman): {r:.2f}, intervalo de 95 % aproximado "
            f"{lo:.2f} a {hi:.2f} (n = {t.height}). Es débil y compatible con ausencia de asociación: estos "
            "datos agregados no permiten afirmar ni descartar reclasificaciones. Además, una correlación "
            "entre entidades no muestra causalidad.",
            "El peso de 'otros delitos contra la vida' varía enormemente entre fiscalías (de 0 % a más de "
            "600 % de las víctimas de homicidio doloso y feminicidio): refleja prácticas de registro "
            "distintas, no solo incidencia.",
        ],
        transformations=[LineageStep("suma@1", {"periodo": periodo},
                                     ["sesnsp_victimas:homicidio_doloso.total",
                                      "sesnsp_victimas:feminicidio.total"]).to_dict()],
        groups={"entidades_federativas": t["geo_id"].to_list()},
        periodos=[str(a) for a in range(int(ENT_DESDE), int(ENT_HASTA) + 1)],
    )
    spec.caveats = [c for c in spec.caveats if c]
    write_chart(paths, catalog, spec, {"entidades": t},
                extra={"periodo": periodo, "spearman": r, "ic95": [lo, hi]})
    return [spec.chart_id]


MENSUALES = {
    "sesnsp_victimas:mensual.homicidio_doloso": "doloso",
    "sesnsp_victimas:mensual.otros_contra_la_vida": "otros",
    "sesnsp_victimas:mensual.feminicidio": "feminicidio",
    "sesnsp_victimas:mensual.tentativa_homicidio_doloso": "tentativa_homicidio",
    "sesnsp_victimas:mensual.tentativa_feminicidio": "tentativa_feminicidio",
}


def _mensual(paths: Paths, catalog: Catalog, obs: pl.DataFrame) -> list[str]:
    """4.9 · Víctimas por mes en carpetas de investigación, con la ruptura metodológica de 2026."""
    m = (obs.filter(pl.col("series_id").is_in(list(MENSUALES)) & (pl.col("geo_id") == FOCO))
         .with_columns(pl.col("series_id").replace_strict(MENSUALES).alias("serie"))
         .select("period", "serie", "value", "obs_status").sort("serie", "period"))
    rupturas = sorted(m.filter(pl.col("obs_status") == "B")["period"].unique().to_list())
    ultimo = m["period"].max()
    otros = m.filter(pl.col("serie") == "otros")
    antes = otros.filter(pl.col("period").str.starts_with("2025"))["value"].mean()
    despues = otros.filter(pl.col("period") >= "2026-01")["value"].mean()
    meses_nuevos = m.filter(pl.col("period") >= "2026-01")["period"].n_unique()
    tentativas = (m.filter(pl.col("serie").str.starts_with("tentativa"))["value"].sum()
                  / max(meses_nuevos, 1))
    spec = ChartSpec(
        chart_id="d4/sesnsp-mensual",
        question=("¿Cómo han cambiado mes a mes las víctimas de delitos contra la vida en las carpetas de "
                  "investigación?"),
        indicators=["seg.violencia_letal.homicidio.victimas_doloso_mensual",
                    "seg.violencia_letal.otros_contra_vida.victimas_mensual",
                    "seg.violencia_letal.feminicidio.victimas_mensual",
                    "seg.violencia_letal.homicidio.tentativa_mensual",
                    "seg.violencia_letal.feminicidio.tentativa_mensual"],
        caveats=[
            (f"Desde {', '.join(rupturas)} rige una nueva metodología del SESNSP (línea punteada): las "
             "cifras antes y después no son estrictamente comparables.") if rupturas else
            "Metodología de registro 2015–2025 del SESNSP (aún no se incorporan los meses de 2026).",
            "" if despues is None else
            "La nueva metodología separa la tentativa de homicidio doloso y la de feminicidio como subtipos "
            f"propios. En el mismo cambio, 'otros delitos contra la vida' pasó de {antes:,.0f} víctimas "
            f"al mes en promedio en 2025 a {despues:,.0f} en 2026 (−{antes - despues:,.0f}), mientras las "
            f"tentativas registradas aparte suman {tentativas:,.0f} al mes: las tentativas pueden explicar "
            "una parte de la caída, pero no toda. Con datos agregados no se puede saber cómo se "
            "reasignó el resto.",
            f"Último mes: {ultimo}. Las fiscalías corrigen meses recientes en cortes posteriores.",
            "Víctimas en carpetas de investigación iniciadas en el mes: dependen de la denuncia y de la "
            "clasificación de cada fiscalía.",
        ],
    )
    spec.caveats = [c for c in spec.caveats if c]
    write_chart(paths, catalog, spec, {"serie": m}, extra={"rupturas": rupturas, "ultimo": ultimo})
    return [spec.chart_id]
