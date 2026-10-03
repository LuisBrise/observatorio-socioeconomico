"""Parsers por dataset: archivos crudos → tabla de staging (sin cambiar significado)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import polars as pl

from observatorio.staging.fmi_weo import parse_fmi_weo
from observatorio.staging.wb_wdi import parse_wb_wdi

# Un parser devuelve (observaciones, entidades_geograficas_de_la_fuente).
Parser = Callable[[Path, str, str], tuple[pl.DataFrame, pl.DataFrame]]

PARSERS: dict[str, Parser] = {"wb_wdi": parse_wb_wdi, "fmi_weo": parse_fmi_weo}

STAGING_SCHEMA = {
    "dataset_id": pl.String,
    "vintage_id": pl.String,
    "source_series": pl.String,
    "source_geo": pl.String,
    "source_geo_name": pl.String,
    "source_period": pl.String,
    "value": pl.Float64,
    "source_obs_status": pl.String,
}

GEO_SCHEMA = {"source_geo": pl.String, "name": pl.String, "is_aggregate": pl.Boolean}
