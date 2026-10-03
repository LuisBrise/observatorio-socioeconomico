import json

import polars as pl
import pytest

from observatorio.ingestion.base import RawStore
from observatorio.pipeline import ingest, load_current, lock, process, read_lock
from observatorio.transform.groups import resolve_group
from observatorio.viz_data import d1
from tests.conftest import FakeWDI

TODAY = __import__("datetime").date(2026, 10, 3)


def run_once(paths, cat, connector):
    res = ingest(paths, cat, "wb_wdi", connector=connector)
    return res, process(paths, cat, "wb_wdi", res.vintage, today=TODAY)


def test_end_to_end_builds_charts_with_provenance(env):
    paths, cat = env
    res, pr = run_once(paths, cat, FakeWDI())
    assert res.changed and pr.status in {"ok", "advertencia"}
    lock(paths, cat, "wb_wdi", pr.vintage)
    assert read_lock(paths)["wb_wdi"]["vintage"] == pr.vintage

    obs = load_current(paths)
    assert {"MEX", "G.wb_wdi.LCN"} <= set(obs["geo_id"].unique())

    charts = d1.build(paths, cat)
    assert charts == ["d1/ingreso-pc-alc", "d1/ingreso-relativo-contraste"]
    prov = json.loads((paths.site_data / "d1/ingreso-pc-alc/provenance.json").read_text())
    s = prov["series"][0]
    assert s["vintage"] == pr.vintage and len(s["raw_content_sha256"]) == 64
    assert s["raw_files"] and prov["caveats"]
    data = json.loads((paths.site_data / "d1/ingreso-pc-alc/data.json").read_text())
    assert data["distribucion"] and data["foco"] == "MEX"


def test_raw_is_immutable_and_deduplicated(env):
    paths, cat = env
    r1 = ingest(paths, cat, "wb_wdi", connector=FakeWDI())
    r2 = ingest(paths, cat, "wb_wdi", connector=FakeWDI())
    assert r1.changed and not r2.changed and r1.vintage == r2.vintage
    store = RawStore(paths.raw, paths.root)
    assert store.vintages("banco_mundial", "wb_wdi") == [r1.vintage]
    manifest = store.manifest("banco_mundial", "wb_wdi", r1.vintage)
    assert manifest["license"]["nombre"] == "CC BY 4.0"


def _second_vintage(paths, cat, connector):
    _, pr1 = run_once(paths, cat, FakeWDI())
    lock(paths, cat, "wb_wdi", pr1.vintage)
    import time
    time.sleep(1.1)  # vintages con marca de tiempo distinta
    return run_once(paths, cat, connector)


def test_revisions_are_detected(env):
    paths, cat = env
    bump = lambda code, geo, y, v: v * 1.10 if code == "NY.GDP.PCAP.PP.KD" and y >= 2020 else v  # noqa: E731
    _, pr = _second_vintage(paths, cat, FakeWDI(transform=bump))
    rep = json.loads((pr.report_dir / "report.json").read_text())
    rev = [r for r in rep["results"] if r["check"] == "revisiones"]
    assert rev and rev[0]["severity"] == "ADVERTENCIA"
    assert pr.status == "advertencia"


def test_unit_change_blocks_processing(env):
    paths, cat = env
    thousand = lambda code, geo, y, v: v * 1000 if code == "SP.POP.TOTL" else v  # noqa: E731
    _, pr = _second_vintage(paths, cat, FakeWDI(transform=thousand))
    assert pr.status == "error"
    from observatorio.pipeline import processed_path
    assert not processed_path(paths, "wb_wdi", pr.vintage).exists()


def test_metadata_change_is_flagged(env):
    paths, cat = env
    _, pr = _second_vintage(paths, cat, FakeWDI(meta_name_suffix=" (nueva definición)"))
    rep = json.loads((pr.report_dir / "report.json").read_text())
    assert any(r["check"] == "cambio_metadatos" for r in rep["results"])


def test_unknown_geography_is_an_error(env):
    paths, cat = env
    _, pr = run_once(paths, cat, FakeWDI(extra_geo="ZZZ"))
    rep = json.loads((pr.report_dir / "report.json").read_text())
    assert pr.status == "error"
    assert any(r["check"] == "geografia_desconocida" and "ZZZ" in r["message"]
               for r in rep["results"])


def test_outlier_is_flagged_not_removed(env):
    paths, cat = env
    spike = lambda code, geo, y, v: v * 5 if (code, geo, y) == ("SP.DYN.LE00.IN", "CHL", 2010) else v  # noqa: E731
    # La esperanza de vida ×5 sale del rango válido: es un ERROR de valor imposible.
    _, pr = run_once(paths, cat, FakeWDI(transform=spike))
    rep = json.loads((pr.report_dir / "report.json").read_text())
    assert any(r["check"] == "valores_imposibles" for r in rep["results"])

    gdp_spike = lambda code, geo, y, v: v * 3 if (code, geo, y) == ("NY.GDP.PCAP.PP.KD", "CHL", 2010) else v  # noqa: E731
    paths2, cat2 = paths, cat
    res = ingest(paths2, cat2, "wb_wdi", connector=FakeWDI(transform=gdp_spike))
    pr2 = process(paths2, cat2, "wb_wdi", res.vintage, today=TODAY)
    rep2 = json.loads((pr2.report_dir / "report.json").read_text())
    out = [r for r in rep2["results"] if r["check"] == "atipicos"]
    assert out and any(d["geo_id"] == "CHL" for d in out[0]["details"])
    obs = pl.read_parquet(next(paths2.processed.rglob(f"vintage={pr2.vintage}/part-0.parquet")))
    assert obs.filter((pl.col("geo_id") == "CHL") & (pl.col("period") == "2010")).height == 3


def test_group_rule_resolves_from_data(env):
    paths, cat = env
    _, pr = run_once(paths, cat, FakeWDI())
    lock(paths, cat, "wb_wdi", pr.vintage)
    from observatorio.pipeline import indicator_values
    pop = indicator_values(load_current(paths), cat, "dem.poblacion.tamano.total")
    members = resolve_group(cat, "G.ALC_GRANDES", {"dem.poblacion.tamano.total": pop})
    assert "MEX" in members and "ATG" not in members


def test_lock_requires_valid_processed_data(env):
    paths, cat = env
    from observatorio.pipeline import PipelineError
    with pytest.raises(PipelineError):
        lock(paths, cat, "wb_wdi", "2000-01-01T000000Z")
