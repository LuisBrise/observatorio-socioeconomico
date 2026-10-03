"""Comparación entre fuentes que miden el mismo indicador.

Principio: no creer ciegamente en una fuente, pero tampoco contar dos veces la misma.
- Solo se comparan series de un mismo indicador (misma definición declarada).
- Si dos series tienen el mismo `origen`, no son independientes: se informa y no cuenta como
  verificación.
- Si la diferencia supera la tolerancia del indicador y no hay una discrepancia documentada en
  catalog/discrepancies/, se emite ADVERTENCIA: hay que investigar por qué difieren
  (nunca elegir una arbitrariamente).
"""

from __future__ import annotations

from itertools import combinations

import polars as pl

from observatorio.catalog import Catalog
from observatorio.validation.checks import INFO, WARN, CheckResult


def series_origin(catalog: Catalog, series_id: str) -> str:
    dataset_id, code = series_id.split(":", 1)
    spec = next(s for s in catalog.datasets[dataset_id].series if s.codigo == code)
    return spec.origen


def compare_pair(obs: pl.DataFrame, a: str, b: str) -> pl.DataFrame:
    """Diferencia relativa (b/a − 1) por geografía y periodo donde ambas series tienen dato.

    Se excluyen pronósticos (obs_status F): comparar una proyección con un dato observado no
    verifica nada.
    """
    if "obs_status" in obs.columns:
        obs = obs.filter(pl.col("obs_status") != "F")
    va = obs.filter(pl.col("series_id") == a).select("geo_id", "period", pl.col("value").alias("a"))
    vb = obs.filter(pl.col("series_id") == b).select("geo_id", "period", pl.col("value").alias("b"))
    return (va.join(vb, on=["geo_id", "period"], how="inner")
            .filter(pl.col("a") != 0)
            .with_columns((pl.col("b") / pl.col("a") - 1).alias("dif_rel"))
            .sort("geo_id", "period"))


def summarize(detail: pl.DataFrame, tol: float) -> dict:
    if detail.is_empty():
        return {"n": 0}
    absd = detail["dif_rel"].abs()
    worst = (detail.with_columns(pl.col("dif_rel").abs().alias("_abs"))
             .group_by("geo_id").agg(pl.col("_abs").max().alias("max_abs"))
             .sort("max_abs", descending=True).head(10))
    return {
        "n": detail.height,
        "geografias": detail["geo_id"].n_unique(),
        "mediana_dif_abs": float(absd.median()),
        "p90_dif_abs": float(absd.quantile(0.9)),
        "share_sobre_tolerancia": float((absd > tol).mean()),
        "peores_geografias": worst.to_dicts(),
    }


def compare_indicator(obs: pl.DataFrame, catalog: Catalog, indicator_id: str
                      ) -> tuple[list[CheckResult], dict[tuple[str, str], pl.DataFrame]]:
    ind = catalog.indicators[indicator_id]
    present = set(obs["series_id"].unique().to_list())
    series = [s for s in ind.series if s in present]
    results: list[CheckResult] = []
    details: dict[tuple[str, str], pl.DataFrame] = {}
    if len(series) < 2:
        results.append(CheckResult(
            "fuente_unica", INFO,
            f"{indicator_id}: una sola fuente disponible ({', '.join(series) or 'ninguna'}); "
            "no hay verificación cruzada", len(series)))
        return results, details

    for a, b in combinations(series, 2):
        detail = compare_pair(obs, a, b)
        details[(a, b)] = detail
        s = summarize(detail, ind.tolerancia_entre_fuentes)
        label = f"{indicator_id}: {a} vs {b}"
        if s["n"] == 0:
            results.append(CheckResult("sin_traslape", INFO, f"{label}: sin periodos en común"))
            continue
        same_origin = series_origin(catalog, a) == series_origin(catalog, b)
        documented = [d.id for d in catalog.discrepancies.values()
                      if d.indicador == indicator_id and {a, b} <= set(d.series)]
        msg = (f"{label}: mediana de diferencia {s['mediana_dif_abs']:.1%}, p90 {s['p90_dif_abs']:.1%}, "
               f"{s['share_sobre_tolerancia']:.0%} de {s['n']} observaciones sobre la tolerancia "
               f"({ind.tolerancia_entre_fuentes:.0%})")
        if same_origin:
            results.append(CheckResult("fuentes_no_independientes", INFO,
                                       msg + " · mismo origen: no cuenta como verificación", s["n"], [s]))
        elif s["share_sobre_tolerancia"] > 0 and not documented:
            results.append(CheckResult("discrepancia_sin_documentar", WARN,
                                       msg + " · documentar la causa en catalog/discrepancies/",
                                       s["n"], [s]))
        else:
            ref = f" · documentada en {', '.join(documented)}" if documented else ""
            results.append(CheckResult("comparacion_fuentes", INFO, msg + ref, s["n"], [s]))
    return results, details
