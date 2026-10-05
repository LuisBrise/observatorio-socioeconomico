"""Parser de PIP (Banco Mundial).

Códigos de serie: `{medida}.{bienestar}.{cobertura}`
- medida: pobreza_3.00 | pobreza_4.20 | pobreza_8.30 | gini
- bienestar: ingreso | consumo  (no son comparables entre sí)
- cobertura: nacional | urbano  (urbano solo cuando no hay dato nacional ese año, p. ej. Argentina)
Las filas rurales se omiten (hay dato nacional para esos años).

Estatus de cada observación:
- B: primera observación de un nuevo periodo de comparabilidad (`comparable_spell`) de la misma
  serie: la diferencia con el punto anterior mezcla cambio real y cambio de encuesta/método.
- E: distribución no proveniente de microdatos (group, imputed, synthetic).
- "" (normal): microdatos.
Valores en proporción (0-1); el catálogo aplica el multiplicador a porcentaje/índice 0-100.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

WELFARE = {"income": "ingreso", "consumption": "consumo"}
LEVEL = {"national": "nacional", "urban": "urbano"}


def parse_wb_pip(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    frames = []
    for path in sorted(raw_dir.glob("pip_*.json")):
        line = path.stem.removeprefix("pip_")
        df = pl.DataFrame(json.loads(path.read_text(encoding="utf-8")), infer_schema_length=None)
        df = df.filter(pl.col("reporting_level").is_in(list(LEVEL)))
        # Urbano solo donde no hay nacional para ese país, año y tipo de bienestar.
        has_nat = (df.filter(pl.col("reporting_level") == "national")
                   .select("country_code", "reporting_year", "welfare_type").unique()
                   .with_columns(pl.lit(True).alias("_nat")))
        df = (df.join(has_nat, on=["country_code", "reporting_year", "welfare_type"], how="left")
              .filter((pl.col("reporting_level") == "national") | pl.col("_nat").is_null()))
        measures = [(f"pobreza_{line}", "headcount")]
        if line == "8.30":
            measures.append(("gini", "gini"))  # el Gini no depende de la línea: se toma una vez
        for code, col in measures:
            frames.append(df.select(
                pl.lit(dataset_id).alias("dataset_id"),
                pl.lit(vintage).alias("vintage_id"),
                (pl.lit(code + ".") + pl.col("welfare_type").replace_strict(WELFARE) + pl.lit(".")
                 + pl.col("reporting_level").replace_strict(LEVEL)).alias("source_series"),
                pl.col("country_code").alias("source_geo"),
                pl.col("country_name").alias("source_geo_name"),
                pl.col("reporting_year").cast(pl.String).alias("source_period"),
                pl.col(col).cast(pl.Float64).alias("value"),
                pl.col("comparable_spell").alias("_spell"),
                pl.col("distribution_type").alias("_dist"),
            ))
    if not frames:
        return pl.DataFrame(schema=STAGING_SCHEMA), pl.DataFrame(schema=GEO_SCHEMA)
    obs = pl.concat(frames).sort("source_series", "source_geo", "source_period")
    new_spell = (pl.col("_spell") != pl.col("_spell").shift(1).over("source_series", "source_geo")) \
        & pl.col("_spell").shift(1).over("source_series", "source_geo").is_not_null()
    obs = obs.with_columns(
        pl.when(new_spell).then(pl.lit("B"))
        .when(pl.col("_dist") != "micro").then(pl.lit("E"))
        .otherwise(pl.lit("")).alias("source_obs_status")
    ).drop("_spell", "_dist").cast(STAGING_SCHEMA)
    geos = (obs.select("source_geo", pl.col("source_geo_name").alias("name")).unique("source_geo")
            .with_columns(pl.lit(False).alias("is_aggregate")).cast(GEO_SCHEMA))
    return obs, geos
