"""Fixtures de prueba.

IMPORTANTE: los datos generados aquí son SINTÉTICOS y existen solo para probar el
pipeline sin conexión. Nunca se publican ni se usan en análisis.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from observatorio.catalog import load_catalog
from observatorio.ingestion.base import FetchResult, RawFile
from observatorio.paths import Paths

REPO = Path(__file__).resolve().parents[1]

ALC = ["ATG", "ARG", "BHS", "BRB", "BLZ", "BOL", "BRA", "CHL", "COL", "CRI", "CUB", "DMA", "DOM",
       "ECU", "SLV", "GRD", "GTM", "GUY", "HTI", "HND", "JAM", "MEX", "NIC", "PAN", "PRY", "PER",
       "KNA", "LCA", "VCT", "SUR", "TTO", "URY", "VEN"]
OTHERS = ["USA", "CAN", "CHN", "VNM", "POL", "CZE", "GRC", "PRT", "RUS", "SWE", "FIN"]
GEOS = ALC + OTHERS
BIG = {"MEX", "BRA", "ARG", "COL", "PER", "VEN", "CHL", "GTM", "ECU", "BOL", "HTI", "CUB", "DOM",
       "HND"}
YEARS = list(range(1990, 2025))


def synthetic_value(code: str, geo: str, year: int) -> float | None:
    seed = sum(ord(c) for c in geo)
    t = year - 1990
    if code == "SP.POP.TOTL":
        base = 20e6 if geo in BIG else 0.5e6
        return base * (1 + (seed % 7) / 10) * (1.01 ** t)
    if code == "SP.POP.DPND":
        return 90 - 1.2 * t + (seed % 5)
    if code == "SP.DYN.LE00.IN":
        return 65 + (seed % 10) + 0.2 * t
    if code == "VC.IHR.PSRC.P5":
        return 5 + (seed % 20) + 0.1 * t
    # PIB per cápita
    if geo == "VEN" and year >= 2015:
        return None  # hueco realista
    return (8000 + 300 * (seed % 40)) * (1.015 ** t) * (1 + 0.02 * math.sin(t + seed))


def wb_page(code: str, rows: list[dict]) -> bytes:
    meta = {"page": 1, "pages": 1, "per_page": 20000, "total": len(rows),
            "sourceid": "2", "lastupdated": "2026-09-30"}
    return json.dumps([meta, rows]).encode()


class FakeWDI:
    """Conector falso con el formato de la API v2 del Banco Mundial."""

    name = "wb_wdi"

    def __init__(self, transform=None, extra_geo: str | None = None, meta_name_suffix: str = ""):
        self.transform = transform or (lambda code, geo, year, v: v)
        self.extra_geo = extra_geo
        self.meta_name_suffix = meta_name_suffix

    def fetch(self, dataset) -> FetchResult:
        files = []
        geos = GEOS + ([self.extra_geo] if self.extra_geo else []) + ["LCN"]
        for s in dataset.series:
            rows = []
            for geo in geos:
                for y in YEARS:
                    v = synthetic_value(s.codigo, "MEX" if geo == "LCN" else geo, y)
                    v = None if v is None else self.transform(s.codigo, geo, y, v)
                    rows.append({"indicator": {"id": s.codigo, "value": s.codigo},
                                 "country": {"id": "ZJ" if geo == "LCN" else geo[:2], "value": geo},
                                 "countryiso3code": "" if geo == "LCN" else geo,
                                 "date": str(y), "value": v,
                                 "unit": "", "obs_status": "", "decimal": 1})
            files.append(RawFile(f"{s.codigo}.p1.json", wb_page(s.codigo, rows), "fake://"))
            meta = [{"page": 1}, [{"id": s.codigo, "name": s.codigo + self.meta_name_suffix,
                                   "unit": "", "sourceNote": "nota"}]]
            files.append(RawFile(f"{s.codigo}.meta.json", json.dumps(meta).encode(), "fake://"))
        countries = [{"id": g, "iso2Code": g[:2], "name": g, "region": {"id": "LCN"}}
                     for g in geos if g != "LCN"]
        countries.append({"id": "LCN", "iso2Code": "ZJ", "name": "Latin America & Caribbean",
                          "region": {"id": "NA", "value": "Aggregates"}})
        files.append(RawFile("countries.p1.json", wb_page("countries", countries), "fake://"))
        return FetchResult(files=files, source_declared_version="2026-09-30")


@pytest.fixture
def env(tmp_path: Path):
    root = tmp_path / "repo"
    shutil.copytree(REPO / "catalog", root / "catalog")
    # Las pruebas empiezan sin datos publicados ni discrepancias documentadas.
    (root / "catalog" / "vintages.lock.yaml").write_text("datasets: {}\n")
    for f in (root / "catalog" / "discrepancies").glob("*.yaml"):
        f.unlink()
    (root / "site").mkdir()
    paths = Paths(root=root, data=tmp_path / "data")
    return paths, load_catalog(paths.catalog)
