"""Parser de víctimas del fuero común del SESNSP (CSV estatal dentro de un ZIP).

Columnas: Año, Clave_Ent, Entidad, Bien jurídico afectado, Tipo de delito, Subtipo de delito,
Modalidad, Sexo, Rango de edad, Enero…Diciembre. La codificación varía entre archivos (latin-1 o
UTF-8 con BOM).

- Meses reportados: un mes cuyo total en todo el archivo es 0 (o vacío) aún no se ha reportado
  (los archivos del año en curso traen ceros en los meses futuros).
- Series anuales (`{subtipo}.{total|sexo}`): solo años con los 12 meses reportados; nacional ("00")
  y por entidad (clave INEGI de dos dígitos).
- Series mensuales nacionales (`mensual.{subtipo}`): todos los meses reportados, periodo `AAAAMmm`.
  Las rupturas de metodología (2026) se declaran en el catálogo.
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
    # Subtipos que aparecen con la metodología 2026 (antes no se registraban por separado).
    "Tentativa de homicidio doloso": "tentativa_homicidio_doloso",
    "Tentativa de feminicidio": "tentativa_feminicidio",
}
ANUALES = {"homicidio_doloso", "feminicidio", "otros_contra_la_vida"}
CON_SEXO = {"homicidio_doloso"}
SEXO = {"Hombre": "hombre", "Mujer": "mujer", "No identificado": "no_identificado"}


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _num(v: str) -> float:
    v = v.strip()
    return float(v) if v else 0.0


def parse_sesnsp(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    anual: dict[tuple[str, str, str], float] = defaultdict(float)
    mensual: dict[tuple[str, str], float] = defaultdict(float)
    completos: dict[str, bool] = {}
    nombres: dict[str, str] = {"00": "Nacional"}
    for zpath in sorted(raw_dir.glob("sesnsp_*.zip")):
        with zipfile.ZipFile(zpath) as zf:
            for member in (m for m in zf.namelist() if m.lower().endswith(".csv")):
                reader = csv.DictReader(io.StringIO(_decode(zf.read(member))))
                reader.fieldnames = [f.strip().lstrip("﻿") for f in reader.fieldnames or []]
                requeridas = {"Año", "Clave_Ent", "Entidad", "Subtipo de delito", "Sexo", *MESES}
                faltan = requeridas - set(reader.fieldnames)
                if faltan:
                    raise ValueError(f"{zpath.name}/{member}: faltan columnas {sorted(faltan)}")
                filas = list(reader)
                # Meses reportados por año en este archivo (total del mes > 0 en todo el archivo).
                tot_mes: dict[tuple[str, str], float] = defaultdict(float)
                for row in filas:
                    for m in MESES:
                        tot_mes[(row["Año"].strip(), m)] += _num(row[m])
                for anio in {row["Año"].strip() for row in filas}:
                    completos[anio] = all(tot_mes[(anio, m)] > 0 for m in MESES)
                for row in filas:
                    serie = SUBTIPOS.get(row["Subtipo de delito"].strip())
                    if serie is None:
                        continue
                    anio = row["Año"].strip()
                    ent = row["Clave_Ent"].strip().zfill(2)
                    nombres[ent] = row["Entidad"].strip()
                    for i, m in enumerate(MESES, start=1):
                        if tot_mes[(anio, m)] > 0:
                            mensual[(f"mensual.{serie}", f"{anio}M{i:02d}")] += _num(row[m])
                    if serie not in ANUALES:
                        continue
                    total = sum(_num(row[m]) for m in MESES)
                    for geo in ("00", ent):
                        anual[(f"{serie}.total", anio, geo)] += total
                        if serie in CON_SEXO:
                            anual[(f"{serie}.{SEXO[row['Sexo'].strip()]}", anio, geo)] += total

    def fila(serie: str, periodo: str, geo: str, valor: float) -> dict:
        return {"dataset_id": dataset_id, "vintage_id": vintage, "source_series": serie,
                "source_geo": geo, "source_geo_name": nombres[geo], "source_period": periodo,
                "value": valor, "source_obs_status": ""}

    rows = [fila(s, anio, geo, v) for (s, anio, geo), v in sorted(anual.items()) if completos.get(anio)]
    rows += [fila(s, periodo, "00", v) for (s, periodo), v in sorted(mensual.items())]
    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = pl.DataFrame([{"source_geo": g, "name": n, "is_aggregate": False}
                         for g, n in sorted(nombres.items())], schema=GEO_SCHEMA)
    return obs, geos
