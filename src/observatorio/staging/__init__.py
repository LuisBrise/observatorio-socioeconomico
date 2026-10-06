"""Parsers por dataset: archivos crudos → tabla de staging (sin cambiar significado)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import polars as pl

from observatorio.staging.cepal import parse_cepal
from observatorio.staging.fmi_weo import parse_fmi_weo
from observatorio.staging.inegi_pm import parse_inegi_pm
from observatorio.staging.onu_wpp import parse_onu_wpp
from observatorio.staging.wb_pip import parse_wb_pip
from observatorio.staging.wb_wdi import parse_wb_wdi
from observatorio.staging.wid import parse_wid

# Un parser devuelve (observaciones, entidades_geograficas_de_la_fuente).
Parser = Callable[[Path, str, str], tuple[pl.DataFrame, pl.DataFrame]]

PARSERS: dict[str, Parser] = {"wb_wdi": parse_wb_wdi, "fmi_weo": parse_fmi_weo,
                              "onu_wpp_prob": parse_onu_wpp, "wb_pip": parse_wb_pip,
                              "inegi_pm": parse_inegi_pm, "wid": parse_wid,
                              "cepal_pobreza": parse_cepal}

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
