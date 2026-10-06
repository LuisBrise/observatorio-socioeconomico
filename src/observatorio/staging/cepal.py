"""Parser de CEPALSTAT (API v1, formato JSON con dimensiones codificadas).

Indicador 3328: población en situación de pobreza y pobreza extrema por área geográfica.
Códigos de serie: `{pobreza|pobreza_extrema}.{nacional|urbana|rural}`.
Estatus: las notas de la fuente "Serie comparable desde AAAA" marcan B en ese año, y
"Serie comparable hasta AAAA" marca B en el primer año posterior con dato.
Geografía: ISO-3 de la fuente; los agregados regionales (sin ISO-3) se codifican por nombre.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl

KIND = {"Pobreza": "pobreza", "Pobreza extrema": "pobreza_extrema"}
AREA = {"Nacional": "nacional", "Total del área urbana": "urbana", "Total del área rural": "rural"}


def parse_cepal(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    rows, geos = [], {}
    for path in sorted(raw_dir.glob("cepal_*.json")):
        body = json.loads(path.read_text(encoding="utf-8"))["body"]
        dims = {d["name"]: {m["id"]: m["name"] for m in d["members"]} | {"_id": d["id"]}
                for d in body["dimensions"]}

        def dim(prefix: str, dims: dict = dims) -> tuple[str, dict]:
            name = next(n for n in dims if n.startswith(prefix))
            return f"dim_{dims[name]['_id']}", dims[name]

        k_country, countries = dim("País")
        k_year, years = dim("Años")
        k_kind, kinds = dim("Pobreza extrema y pobreza")
        k_area, areas = dim("Area geográfica")
        notes = {str(f["id"]): f["description"] for f in body.get("footnotes", [])}
        for r in body["data"]:
            name = countries[r[k_country]]
            geo = r.get("iso3") or "AGR_" + re.sub(r"\W+", "_", name).upper()
            geos[geo] = (name, r.get("iso3") is None)
            text = " ".join(notes.get(n, "") for n in str(r.get("notes_ids") or "").split(",") if n)
            rows.append({
                "dataset_id": dataset_id, "vintage_id": vintage,
                "source_series": f"{KIND[kinds[r[k_kind]]]}.{AREA[areas[r[k_area]]]}",
                "source_geo": geo, "source_geo_name": name,
                "source_period": years[r[k_year]],
                "value": float(r["value"]) if r["value"] not in (None, "") else None,
                "_notes": text,
            })
    df = pl.DataFrame(rows).sort("source_series", "source_geo", "source_period")
    desde = pl.col("_notes").str.extract(r"comparable (?:desde|a partir de) (\d{4})").cast(pl.Int32)
    hasta = pl.col("_notes").str.extract(r"comparable hasta (\d{4})").cast(pl.Int32)
    year = pl.col("source_period").cast(pl.Int32)
    prev_hasta = hasta.shift(1).over("source_series", "source_geo")
    is_break = ((desde == year) & year.shift(1).over("source_series", "source_geo").is_not_null()) \
        | (prev_hasta.is_not_null() & (prev_hasta < year))
    obs = df.with_columns(pl.when(is_break.fill_null(False)).then(pl.lit("B")).otherwise(pl.lit(""))
                          .alias("source_obs_status")).drop("_notes").cast(STAGING_SCHEMA)
    geo_df = pl.DataFrame([{"source_geo": g, "name": n, "is_aggregate": a} for g, (n, a) in geos.items()],
                          schema=GEO_SCHEMA)
    return obs, geo_df
