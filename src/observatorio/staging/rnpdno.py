"""Parser de la versión pública del RNPDNO (ver el conector `rnpdno`).

- Periodo = año de desaparición declarado en el registro (no el año en que se registró).
- Series: `{estatus}.total` para cada estatus y, solo para las personas que siguen
  desaparecidas, el desglose `desaparecidas.{hombre,mujer,indeterminado}` (lo demás queda en el
  archivo crudo).
- La categoría "CIFRA SIN AÑO DE REFERENCIA" se guarda como serie `{estatus}.sin_anio` con
  periodo = año de la consulta (es un acervo sin fecha, no un flujo anual).
- Toda la tabla es una instantánea; el año de la consulta y el anterior quedan marcados como
  preliminares (P): el registro de desapariciones recientes se completa con retraso.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ESTATUS = {"0": "todas", "7": "desaparecidas", "2": "localizadas_con_vida", "3": "localizadas_sin_vida"}
CON_SEXO = {"desaparecidas"}
CON_SIN_ANIO = {"desaparecidas", "todas"}
SEXO = {"Hombre": "hombre", "Mujer": "mujer", "Indeterminado": "indeterminado"}


def parse_rnpdno(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    anio_consulta = vintage[:4]
    prelim = {anio_consulta, str(int(anio_consulta) - 1)}
    rows: list[dict] = []

    def add(series: str, period: str, value: float) -> None:
        rows.append({"dataset_id": dataset_id, "vintage_id": vintage, "source_series": series,
                     "source_geo": "MEX", "source_geo_name": "México", "source_period": period,
                     "value": value, "source_obs_status": "P" if period in prelim else ""})

    for path in sorted(raw_dir.glob("anio_sexo_*.json")):
        estatus = ESTATUS[path.stem.removeprefix("anio_sexo_")]
        d = json.loads(path.read_text(encoding="utf-8"))
        cats = d["XAxisCategories"]
        series = {SEXO[s["name"]]: s["data"] for s in d["Series"]}
        if any(len(v) != len(cats) for v in series.values()):
            raise ValueError(f"{path.name}: series y categorías de distinto largo")
        for i, cat in enumerate(cats):
            total = float(sum(v[i] for v in series.values()))
            if not cat.strip().isdigit():
                if "SIN" in cat.upper():
                    if estatus not in CON_SIN_ANIO:
                        continue
                    rows.append({"dataset_id": dataset_id, "vintage_id": vintage,
                                 "source_series": f"{estatus}.sin_anio", "source_geo": "MEX",
                                 "source_geo_name": "México", "source_period": anio_consulta,
                                 "value": total, "source_obs_status": ""})
                    continue
                raise ValueError(f"{path.name}: categoría inesperada {cat!r}")
            add(f"{estatus}.total", cat, total)
            for sexo, data in (series.items() if estatus in CON_SEXO else ()):
                add(f"{estatus}.{sexo}", cat, float(data[i]))
    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = pl.DataFrame([{"source_geo": "MEX", "name": "México", "is_aggregate": False}],
                        schema=GEO_SCHEMA)
    return obs, geos
