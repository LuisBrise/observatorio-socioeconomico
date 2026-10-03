"""Parser del WEO (SDMX-CSV). Marca como proyección (F) lo posterior al último año observado."""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

_AGGREGATE = re.compile(r"^G[X0-9]")  # códigos de grupos del FMI (G110, GX123…)


def last_actual_year(value: str | None) -> int | None:
    """'2024' → 2024; 'FY2019/20' → 2019; 'Not applicable' o vacío → None."""
    m = re.search(r"(\d{4})", value or "")
    return int(m.group(1)) if m else None


def parse_fmi_weo(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    frames = []
    for path in sorted(raw_dir.glob("*.csv")):
        df = pl.read_csv(path, infer_schema_length=0)
        last = df["LATEST_ACTUAL_ANNUAL_DATA"].map_elements(last_actual_year, return_dtype=pl.Int64)
        # Sin último año observado declarado (agregados, "Not applicable"): todo lo posterior al
        # año previo a la edición es proyección (en el WEO el año en curso siempre es proyectado).
        edition_year = pl.col("PUBLICATION_DATE").str.slice(0, 4).cast(pl.Int64, strict=False)
        df = df.with_columns(last.alias("_last")).with_columns(
            pl.coalesce(pl.col("_last"), edition_year - 1).alias("_last"))
        frames.append(df.select(
            pl.lit(dataset_id).alias("dataset_id"),
            pl.lit(vintage).alias("vintage_id"),
            pl.col("INDICATOR").alias("source_series"),
            pl.col("COUNTRY").alias("source_geo"),
            pl.col("COUNTRY").alias("source_geo_name"),
            pl.col("TIME_PERIOD").alias("source_period"),
            # OBS_VALUE viene en unidades (SCALE es metadato de presentación, no un multiplicador).
            pl.col("OBS_VALUE").cast(pl.Float64, strict=False).alias("value"),
            pl.when(pl.col("_last").is_not_null()
                    & (pl.col("TIME_PERIOD").cast(pl.Int64) > pl.col("_last")))
            .then(pl.lit("F")).otherwise(pl.lit("")).alias("source_obs_status"),
        ))
    obs = pl.concat(frames).cast(STAGING_SCHEMA) if frames else pl.DataFrame(schema=STAGING_SCHEMA)
    codes = obs["source_geo"].unique().sort()
    geos = pl.DataFrame({"source_geo": codes, "name": codes,
                         "is_aggregate": [bool(_AGGREGATE.match(c)) for c in codes]},
                        schema=GEO_SCHEMA)
    return obs, geos
