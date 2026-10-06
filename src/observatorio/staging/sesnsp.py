"""Parser de víctimas del fuero común del SESNSP (CSV estatal dentro de un ZIP).

Columnas: Año, Clave_Ent, Entidad, Bien jurídico afectado, Tipo de delito, Subtipo de delito,
Modalidad, Sexo, Rango de edad, Enero…Diciembre. Se suman entidades y meses para obtener el total
nacional anual por subtipo (y por sexo en homicidio doloso); también por entidad (clave INEGI de
dos dígitos; "00" = nacional). Un año con meses vacíos (año en curso)
se marca preliminar (P). La codificación varía entre archivos (latin-1 o UTF-8 con BOM).
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections import defaultdict
from pathlib import Path

import polars as pl

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre"]
SUBTIPOS = {
    "Homicidio doloso": "homicidio_doloso",
    "Feminicidio": "feminicidio",
    "Otros delitos que atentan contra la vida y la integridad corporal": "otros_contra_la_vida",
}
CON_SEXO = {"homicidio_doloso"}
SEXO = {"Hombre": "hombre", "Mujer": "mujer", "No identificado": "no_identificado"}


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def parse_sesnsp(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    totals: dict[tuple[str, str, str], float] = defaultdict(float)
    nombres: dict[str, str] = {"00": "Nacional"}
    incompletos: set[str] = set()
    for zpath in sorted(raw_dir.glob("sesnsp_*.zip")):
        with zipfile.ZipFile(zpath) as zf:
            for member in (m for m in zf.namelist() if m.lower().endswith(".csv")):
                reader = csv.DictReader(io.StringIO(_decode(zf.read(member))))
                reader.fieldnames = [f.strip().lstrip("﻿") for f in reader.fieldnames or []]
                requeridas = {"Año", "Clave_Ent", "Entidad", "Subtipo de delito", "Sexo", *MESES}
                faltan = requeridas - set(reader.fieldnames)
                if faltan:
                    raise ValueError(f"{zpath.name}/{member}: faltan columnas {sorted(faltan)}")
                for row in reader:
                    serie = SUBTIPOS.get(row["Subtipo de delito"].strip())
                    if serie is None:
                        continue
                    anio = row["Año"].strip()
                    vals = [row[m].strip() for m in MESES]
                    if any(v == "" for v in vals):
                        incompletos.add(anio)
                    total = sum(float(v) for v in vals if v)
                    ent = row["Clave_Ent"].strip().zfill(2)
                    nombres[ent] = row["Entidad"].strip()
                    for geo in ("00", ent):
                        totals[(f"{serie}.total", anio, geo)] += total
                        if serie in CON_SEXO:
                            totals[(f"{serie}.{SEXO[row['Sexo'].strip()]}", anio, geo)] += total
    rows = [{"dataset_id": dataset_id, "vintage_id": vintage, "source_series": s, "source_geo": geo,
             "source_geo_name": nombres[geo], "source_period": anio, "value": v,
             "source_obs_status": "P" if anio in incompletos else ""}
            for (s, anio, geo), v in sorted(totals.items())]
    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = pl.DataFrame([{"source_geo": g, "name": n, "is_aggregate": False}
                         for g, n in sorted(nombres.items())], schema=GEO_SCHEMA)
    return obs, geos
