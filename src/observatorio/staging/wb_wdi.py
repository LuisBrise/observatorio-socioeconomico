"""Parser de WDI (API v2). Convierte las páginas JSON a la tabla de staging."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


def _load_pages(raw_dir: Path, stem: str) -> list[dict]:
    rows: list[dict] = []
    pages = sorted(raw_dir.glob(f"{stem}.p*.json"), key=lambda p: int(p.suffixes[-2][2:]))
    for p in pages:
        payload = json.loads(p.read_text(encoding="utf-8"))
        rows.extend(payload[1] or [])
    return rows


def parse_wb_wdi(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    countries = _load_pages(raw_dir, "countries")
    # Si una fila no trae countryiso3code, se recupera con el código ISO-2 de la lista de economías.
    iso2_to_id = {c.get("iso2Code"): c["id"] for c in countries if c.get("iso2Code")}
    records = []
    codes = sorted({p.name.split(".p")[0] for p in raw_dir.glob("*.p*.json")} - {"countries"})
    for code in codes:
        for r in _load_pages(raw_dir, code):
            records.append(
                {
                    "dataset_id": dataset_id,
                    "vintage_id": vintage,
                    "source_series": r["indicator"]["id"],
                    "source_geo": (r.get("countryiso3code")
                                   or iso2_to_id.get(r["country"]["id"], r["country"]["id"])),
                    "source_geo_name": r["country"]["value"],
                    "source_period": str(r["date"]),
                    "value": None if r["value"] is None else float(r["value"]),
                    "source_obs_status": r.get("obs_status") or "",
                }
            )
    obs = pl.DataFrame(records, schema=STAGING_SCHEMA)

    geos = [
        {
            "source_geo": c["id"],
            "name": c["name"],
            "is_aggregate": (c.get("region") or {}).get("id") == "NA",
        }
        for c in countries
    ]
    return obs, pl.DataFrame(geos, schema=GEO_SCHEMA)
