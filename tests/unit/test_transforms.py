from datetime import date

import polars as pl

from observatorio.transform import TRANSFORMS, get_transform


def vals(rows):
    return pl.DataFrame(
        [(g, str(y), date(y, 1, 1), v) for g, y, v in rows],
        schema=["geo_id", "period", "period_start", "value"], orient="row")


def test_registry_has_versioned_names():
    assert {"razon_geo@1", "per_capita@1", "var_anual@1", "indice_base@1",
            "distribucion_grupo@1"} <= set(TRANSFORMS)


def test_razon_geo():
    df = vals([("MEX", 2000, 20.0), ("USA", 2000, 80.0), ("MEX", 2001, 30.0)])
    out = get_transform("razon_geo@1")(df, geo_denominador="USA", escala=100)
    assert out.filter(pl.col("geo_id") == "MEX")["value"].to_list() == [25.0]


def test_var_anual_skips_gaps():
    df = vals([("A", 2000, 100.0), ("A", 2001, 110.0), ("A", 2003, 121.0)])
    out = get_transform("var_anual@1")(df)
    assert out["period"].to_list() == ["2001"]
    assert abs(out["value"][0] - 10.0) < 1e-9


def test_indice_base():
    df = vals([("A", 2000, 50.0), ("A", 2001, 75.0)])
    out = get_transform("indice_base@1")(df, periodo_base="2000")
    assert out["value"].to_list() == [100.0, 150.0]


def test_distribucion_grupo_nulls_when_coverage_low():
    members = ["A", "B", "C", "D"]
    df = vals([("A", 2000, 1.0), ("B", 2000, 2.0), ("C", 2000, 3.0), ("D", 2000, 4.0),
               ("A", 2001, 1.0)])
    pop = vals([(g, y, 10.0) for g in members for y in (2000, 2001)])
    out = get_transform("distribucion_grupo@1")(df, members, poblacion=pop, cobertura_minima=0.8)
    r2000 = out.filter(pl.col("period") == "2000").row(0, named=True)
    r2001 = out.filter(pl.col("period") == "2001").row(0, named=True)
    assert r2000["mediana"] == 2.5 and r2000["cobertura_suficiente"]
    assert r2001["mediana"] is None and not r2001["cobertura_suficiente"]
    assert r2001["cobertura_poblacion"] == 0.25
