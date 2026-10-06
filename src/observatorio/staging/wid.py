"""Parser de WID: participaciones en el ingreso nacional antes de impuestos y Gini.

Variables (adultos de 20 años o más, ingreso repartido por igual entre cónyuges: `j992`):
- sptincj992 p90p100 → top10   ·  p99p100 → top1  ·  p0p50 → bottom50
- gptincj992 p0p100 → gini
Estatus: data_quality <= 1 → I (imputado/extrapolado: WID rellena años sin fuentes con el
valor más cercano o con modelos regionales). Códigos de país ISO-2 → ISO-3.
"""

from __future__ import annotations

import gzip
import io
from pathlib import Path

import polars as pl
import pycountry

SERIES = {("sptincj992", "p90p100"): "top10", ("sptincj992", "p99p100"): "top1",
          ("sptincj992", "p0p50"): "bottom50", ("gptincj992", "p0p100"): "gini"}


def _iso3(alpha2: str) -> str:
    c = pycountry.countries.get(alpha_2=alpha2)
    return c.alpha_3 if c else alpha2


def parse_wid(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    keys = pl.DataFrame([{"variable": v, "percentile": p, "code": c} for (v, p), c in SERIES.items()])
    frames = []
    for path in sorted(raw_dir.glob("WID_data_*.csv.gz")):
        # Todo como texto (los archivos de WID mezclan tipos en algunas columnas); se convierte después.
        df = pl.read_csv(io.BytesIO(gzip.decompress(path.read_bytes())), separator=";",
                         infer_schema=False)
        df = df.join(keys, on=["variable", "percentile"], how="inner")
        frames.append(df.select(
            pl.lit(dataset_id).alias("dataset_id"),
            pl.lit(vintage).alias("vintage_id"),
            pl.col("code").alias("source_series"),
            pl.col("country").map_elements(_iso3, return_dtype=pl.String).alias("source_geo"),
            pl.col("country").alias("source_geo_name"),
            pl.col("year").alias("source_period"),
            pl.col("value").cast(pl.Float64),
            pl.when(pl.col("data_quality").cast(pl.Int64, strict=False).fill_null(0) <= 1).then(pl.lit("I"))
            .otherwise(pl.lit("")).alias("source_obs_status"),
        ))
    obs = pl.concat(frames).cast(STAGING_SCHEMA) if frames else pl.DataFrame(schema=STAGING_SCHEMA)
    geos = (obs.select("source_geo", pl.col("source_geo_name").alias("name")).unique("source_geo")
            .with_columns(pl.lit(False).alias("is_aggregate")).cast(GEO_SCHEMA))
    return obs, geos
