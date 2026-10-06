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
