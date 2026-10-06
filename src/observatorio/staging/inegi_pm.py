"""Parser de la medición oficial de pobreza multidimensional (INEGI, pm_ip_{año}.xlsx).

- "Cuadro 1": indicadores nacionales en porcentaje para la serie comparable vigente
  (2016–2024: CONEVAL 2016–2022 e INEGI 2024, misma metodología).
- "IP cuadro 1": indicadores de precisión del último año (intervalo de confianza al 95 %), que
  se guardan como series con variante inferior_95 / superior_95.
Los renglones se identifican por su texto (no por posición) mediante `ROWS`.
"""

from __future__ import annotations

import re
from pathlib import Path

import fastexcel
import polars as pl

ROWS = {
    "Población en situación de pobreza": "pobreza",
    "Población en situación de pobreza extrema": "pobreza_extrema",
    "Población con ingreso inferior a la línea de pobreza por ingresos": "ingreso_bajo_lpi",
    "Rezago educativo": "carencia_educacion",
    "Carencia por acceso a los servicios de salud": "carencia_salud",
    "Carencia por acceso a la seguridad social": "carencia_seguridad_social",
    "Carencia por calidad y espacios de la vivienda": "carencia_vivienda",
    "Carencia por acceso a los servicios básicos en la vivienda": "carencia_servicios_basicos",
    "Carencia por acceso a la alimentación nutritiva y de calidad": "carencia_alimentacion",
}


def _sheet(book, name: str) -> pl.DataFrame:
    return book.load_sheet(name, header_row=None, dtypes="string").to_polars()


def _label(row: tuple) -> str | None:
    return next((str(v).strip() for v in row[:4] if v), None)


def parse_inegi_pm(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    path = next(raw_dir.glob("pm_ip_*.xlsx"))
    book = fastexcel.read_excel(path)
    rows: list[dict] = []

    def add(code: str, period: str, value: str | None) -> None:
        if value not in (None, ""):
            rows.append({"dataset_id": dataset_id, "vintage_id": vintage, "source_series": code,
                         "source_geo": "MEX", "source_geo_name": "Estados Unidos Mexicanos",
                         "source_period": period, "value": float(value), "source_obs_status": ""})

    # Cuadro 1: el bloque "Porcentaje" empieza en la columna con ese encabezado.
    c1 = _sheet(book, "Cuadro 1")
    hdr = next(i for i in range(c1.height) if "Porcentaje" in [str(v) for v in c1.row(i)])
    pct_col = [str(v) for v in c1.row(hdr)].index("Porcentaje")
    # Años consecutivos desde la columna "Porcentaje" hasta que se repite un año (inicia otro bloque).
    pct_years: dict[int, str] = {}
    for j, v in enumerate(c1.row(hdr + 1)):
        y = str(v) if v is not None else ""
        if j < pct_col or not re.fullmatch(r"\d{4}", y):
            continue
        if y in pct_years.values():
            break
        pct_years[j] = y
    for i in range(hdr + 2, c1.height):
        row = c1.row(i)
        code = ROWS.get(_label(row) or "")
        if code:
            for j, y in pct_years.items():
                add(code, y, row[j])

    # IP cuadro 1: intervalo de confianza al 95 % del porcentaje, último año.
    ip = _sheet(book, "IP cuadro 1")
    year = next(str(v) for i in range(ip.height) for v in ip.row(i)[:1]
                if v and re.fullmatch(r"\d{4}", str(v)))
    h = next(i for i in range(ip.height) if "Porcentaje" in [str(v) for v in ip.row(i)])
    pc = [str(v) for v in ip.row(h)].index("Porcentaje")
    lo_col, hi_col = pc + 2, pc + 3  # Estimación, Error estándar, IC inferior, IC superior, CV
    for i in range(h + 1, ip.height):
        row = ip.row(i)
        code = ROWS.get(_label(row) or "")
        if code:
            add(f"{code}.L95", year, row[lo_col])
            add(f"{code}.U95", year, row[hi_col])

    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = pl.DataFrame({"source_geo": ["MEX"], "name": ["Estados Unidos Mexicanos"],
                         "is_aggregate": [False]}, schema=GEO_SCHEMA)
    return obs, geos
