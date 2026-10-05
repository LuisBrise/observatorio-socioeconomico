"""Armonización: staging → observaciones canónicas (docs/diseno/02-arquitectura.md §5).

- Geografía: códigos de la fuente → `geo_id`. Países deben existir en el catálogo; los
  agregados propios de la fuente se conservan como `G.{dataset}.{código}`. Un código
  desconocido nunca se descarta en silencio: se reporta como ERROR.
- Periodos: `period`, `period_start`, `period_end`, `freq`.
- Unidades: aplica el multiplicador declarado en el catálogo.
- Estatus: banderas de la fuente → códigos SDMX.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import polars as pl

from observatorio.catalog import Catalog
from observatorio.catalog.models import Dataset

OBSERVATION_SCHEMA = {
    "series_id": pl.String,
    "geo_id": pl.String,
    "period": pl.String,
    "period_start": pl.Date,
    "period_end": pl.Date,
    "freq": pl.String,
    "value": pl.Float64,
    "obs_status": pl.String,
    "vintage_id": pl.String,
}

# Banderas conocidas por dataset → código SDMX. "" = observación normal.
STATUS_MAP: dict[str, dict[str, str]] = {
    "wb_wdi": {"": "A", "E": "E", "F": "F", "P": "P"},
    "fmi_weo": {"": "A", "F": "F"},  # F = proyección del FMI (posterior al último año observado)
    "onu_wpp_prob": {"F": "F"},  # todo es proyección
    # PIP: B = inicio de un nuevo periodo de comparabilidad; E = sin microdatos (group/imputed/synthetic)
    "wb_pip": {"": "A", "E": "E", "B": "B"},
}

_ANNUAL = re.compile(r"^\d{4}$")
_QUARTER = re.compile(r"^(\d{4})Q([1-4])$")
_MONTH = re.compile(r"^(\d{4})M(\d{2})$")


@dataclass
class HarmonizeIssue:
    check: str
    severity: str  # ERROR | ADVERTENCIA | INFO
    message: str
    count: int = 0


def _period_frame(periods: pl.Series) -> pl.DataFrame:
    rows = []
    for p in periods.unique().to_list():
        if _ANNUAL.match(p):
            y = int(p)
            rows.append((p, p, f"{y}-01-01", f"{y}-12-31", "A"))
        elif m := _QUARTER.match(p):
            y, q = int(m[1]), int(m[2])
            end_month = q * 3
            end_day = {3: 31, 6: 30, 9: 30, 12: 31}[end_month]
            rows.append((p, f"{y}-Q{q}", f"{y}-{end_month - 2:02d}-01",
                         f"{y}-{end_month:02d}-{end_day}", "Q"))
        elif m := _MONTH.match(p):
            y, mo = int(m[1]), int(m[2])
            rows.append((p, f"{y}-{mo:02d}", f"{y}-{mo:02d}-01", None, "M"))
        else:
            rows.append((p, None, None, None, None))
    df = pl.DataFrame(
        rows, schema=["source_period", "period", "period_start", "period_end", "freq"], orient="row"
    ).with_columns(pl.col("period_start").str.to_date(), pl.col("period_end").str.to_date())
    # Fin de mes para periodos mensuales.
    return df.with_columns(
        pl.when(pl.col("freq") == "M")
        .then(pl.col("period_start").dt.month_end())
        .otherwise(pl.col("period_end"))
        .alias("period_end")
    )


def harmonize(
    staging: pl.DataFrame, source_geos: pl.DataFrame, dataset: Dataset, catalog: Catalog
) -> tuple[pl.DataFrame, list[HarmonizeIssue]]:
    issues: list[HarmonizeIssue] = []
    specs = {s.codigo: s for s in dataset.series}

    unexpected = set(staging["source_series"].unique()) - set(specs)
    if unexpected:
        issues.append(HarmonizeIssue("series_inesperadas", "ERROR",
                                     f"Series no declaradas en el catálogo: {sorted(unexpected)}",
                                     len(unexpected)))
    df = staging.filter(pl.col("source_series").is_in(list(specs)))

    n_null = df["value"].is_null().sum()
    df = df.filter(pl.col("value").is_not_null())
    if n_null:
        issues.append(HarmonizeIssue("valores_nulos", "INFO",
                                     "Observaciones sin valor en la fuente (se omiten)", n_null))

    # Geografía
    aggregates = set(source_geos.filter(pl.col("is_aggregate"))["source_geo"].to_list())
    countries = {g for g, geo in catalog.geographies.items() if geo.tipo == "pais"}
    xwalk = catalog.geo_crosswalk.get(dataset.id, {})
    geo_codes = df["source_geo"].unique().to_list()
    mapping, unknown = {}, []
    for code in geo_codes:
        if code in xwalk:
            mapping[code] = xwalk[code]
        elif code in countries:
            mapping[code] = code
        elif code in aggregates:
            mapping[code] = f"G.{dataset.id}.{code}"
        else:
            unknown.append(code)
    if unknown:
        names = (df.filter(pl.col("source_geo").is_in(unknown))
                 .select("source_geo", "source_geo_name").unique().sort("source_geo"))
        issues.append(HarmonizeIssue(
            "geografia_desconocida", "ERROR",
            "Códigos sin equivalencia en catalog/geographies: "
            + ", ".join(f"{a} ({b})" for a, b in names.iter_rows()),
            len(unknown)))
    df = df.filter(pl.col("source_geo").is_in(list(mapping))).with_columns(
        pl.col("source_geo").replace_strict(mapping).alias("geo_id")
    )

    # Periodos
    periods = _period_frame(df["source_period"])
    bad = periods.filter(pl.col("period").is_null())["source_period"].to_list()
    if bad:
        issues.append(HarmonizeIssue("periodo_invalido", "ERROR",
                                     f"Periodos no interpretables: {bad[:10]}", len(bad)))
    df = df.join(periods.filter(pl.col("period").is_not_null()), on="source_period", how="inner")

    # Estatus
    smap = STATUS_MAP.get(dataset.id, {"": "A"})
    unknown_status = set(df["source_obs_status"].unique()) - set(smap)
    if unknown_status:
        issues.append(HarmonizeIssue("estatus_desconocido", "ADVERTENCIA",
                                     f"Banderas no mapeadas (se marcan como 'A'): {unknown_status}",
                                     len(unknown_status)))

    mult = {c: s.multiplicador for c, s in specs.items()}
    out = df.with_columns(
        (pl.lit(f"{dataset.id}:") + pl.col("source_series")).alias("series_id"),
        (pl.col("value") * pl.col("source_series").replace_strict(mult, return_dtype=pl.Float64)),
        pl.col("source_obs_status").replace_strict(smap, default="A").alias("obs_status"),
    ).select(list(OBSERVATION_SCHEMA))
    return out.cast(OBSERVATION_SCHEMA).sort("series_id", "geo_id", "period_start"), issues
