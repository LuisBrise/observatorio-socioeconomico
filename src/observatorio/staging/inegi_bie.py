"""Parser de la API del BIE de INEGI (`bie_{id}.json`).

- Serie: el identificador del indicador.
- Periodo: `AAAA/MM` → `AAAAMmm` (frecuencia 8 = mensual). Otras frecuencias aún no se usan y se
  rechazan explícitamente para no interpretarlas mal.
- La API no distingue cifras preliminares (el estatus es el mismo en toda la serie): todas se
  guardan como "A"; las advertencias de las gráficas indican que los meses recientes se revisan.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

FRECUENCIAS = {"8": "mensual"}


def parse_inegi_bie(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    rows = []
    for path in sorted(raw_dir.glob("bie_*.json")):
        serie = json.loads(path.read_text(encoding="utf-8"))["Series"][0]
        if serie.get("FREQ") not in FRECUENCIAS:
            raise ValueError(f"{path.name}: frecuencia {serie.get('FREQ')!r} no soportada")
        for obs in serie["OBSERVATIONS"]:
            if obs.get("OBS_VALUE") in (None, ""):
                continue
            anio, mes = obs["TIME_PERIOD"].split("/")
            rows.append({"dataset_id": dataset_id, "vintage_id": vintage,
                         "source_series": serie["INDICADOR"], "source_geo": "MEX",
                         "source_geo_name": "Estados Unidos Mexicanos",
                         "source_period": f"{anio}M{int(mes):02d}", "value": float(obs["OBS_VALUE"]),
                         "source_obs_status": ""})
    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = pl.DataFrame([{"source_geo": "MEX", "name": "Estados Unidos Mexicanos", "is_aggregate": False}],
                        schema=GEO_SCHEMA)
    return obs, geos
