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
    return built
