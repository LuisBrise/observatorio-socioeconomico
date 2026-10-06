"""Parser de tabulados interactivos de INEGI (ver el conector `inegi_tabulados`).

La matriz llega en orden de filas: filas = categorías de la variable de renglón (entidad
federativa), columnas = combinaciones de las variables de encabezado (p. ej. Periodo × Sexo).
Cada celda es `"25,757||"`: valor con separador de miles y banderas vacías.

- Serie: `{cuadro}.{categoría}` (p. ej. `Mortalidad_08.total`, `Mortalidad_08.mujeres`).
- Geografía: el código de la variable de renglón (clave INEGI de la entidad, dos dígitos; "00" =
  total nacional). Las equivalencias a ISO 3166-2 están en catalog/geographies/equivalencias.yaml.
- Cifras preliminares: la nota del cuadro ("Los datos de 2025 son preliminares") → estatus P.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import polars as pl

_PRELIM = re.compile(r"[Ll]os datos de (\d{4}) son preliminares")


def _slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def _value(cell: str) -> float | None:
    raw = cell.split("|", 1)[0].replace(",", "").strip()
    try:
        return float(raw)
    except ValueError:
        return None


def parse_inegi_tabulados(raw_dir: Path, dataset_id: str,
                          vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    rows: list[dict] = []
    for datos_path in sorted(raw_dir.glob("*.datos.json")):
        stem = datos_path.name.removesuffix(".datos.json")
        cuadro = stem.split("__")[-1]
        datos = json.loads(datos_path.read_text(encoding="utf-8"))
        info = json.loads((raw_dir / f"{stem}.info.json").read_text(encoding="utf-8"))
        tab = json.loads((raw_dir / f"{stem}.tabulado.json").read_text(encoding="utf-8"))
        renglon = tab["variables"][0]
        clave = dict(zip(renglon["valueTexts"], renglon["values"], strict=True))
        preliminares = set(_PRELIM.findall(info.get("note") or ""))

        stub = datos["stub"][0]["label"]
        heading = datos["heading"]
        codes = [h["code"] for h in heading]
        if "Periodo" not in codes:
            raise ValueError(f"{stem}: el cuadro no tiene variable Periodo ({codes})")
        # Combinaciones de encabezado en el orden de la matriz (la última variable varía más rápido).
        combos: list[dict[str, str]] = [{}]
        for h in heading:
            combos = [{**c, h["code"]: lab} for c in combos for lab in h["label"]]
        ncol = len(combos)
        if len(datos["data"]) != ncol * len(stub):
            raise ValueError(f"{stem}: la matriz no coincide con sus dimensiones")
        for i, entidad in enumerate(stub):
            geo = clave[entidad].zfill(2)
            for j, combo in enumerate(combos):
                value = _value(datos["data"][i * ncol + j])
                if value is None:
                    continue
                periodo = combo["Periodo"]
                resto = [_slug(v) for k, v in combo.items() if k != "Periodo"]
                rows.append({
                    "dataset_id": dataset_id, "vintage_id": vintage,
                    "source_series": ".".join([cuadro, *resto]),
                    "source_geo": geo, "source_geo_name": entidad,
                    "source_period": periodo, "value": value,
                    "source_obs_status": "P" if periodo in preliminares else "",
                })
    obs = pl.DataFrame(rows, schema=STAGING_SCHEMA)
    geos = (obs.select(pl.col("source_geo"), pl.col("source_geo_name").alias("name"),
                       pl.lit(False).alias("is_aggregate")).unique().sort("source_geo"))
    geos = pl.DataFrame(geos.to_dicts(), schema=GEO_SCHEMA)
    return obs, geos
