"""Parser de PIP: series por bienestar y cobertura, rupturas de comparabilidad y estatus."""

import json

from observatorio.staging.wb_pip import parse_wb_pip


def row(cc, year, spell, level="national", welfare="income", dist="micro", hc=0.2, gini=0.45):
    return {"country_code": cc, "country_name": cc, "reporting_year": year, "reporting_level": level,
            "welfare_type": welfare, "comparable_spell": spell, "distribution_type": dist,
            "headcount": hc, "gini": gini, "decile10": 0.35}


def test_pip_series_breaks_and_coverage(tmp_path):
    rows = [row("MEX", 2012, "1984 - 2014"), row("MEX", 2014, "1984 - 2014"),
            row("MEX", 2016, "2016 - 2024"), row("MEX", 2018, "2016 - 2024", dist="group"),
            row("ARG", 2020, "2017 - 2024", level="urban"),                 # sin nacional → urbano
            row("BOL", 2020, "x", level="urban"), row("BOL", 2020, "x"),    # hay nacional → urbano fuera
            row("BOL", 2020, "x", level="rural"),                           # rural siempre fuera
            row("PER", 2020, "y", welfare="consumption")]
    (tmp_path / "pip_8.30.json").write_text(json.dumps(rows))
    obs, geos = parse_wb_pip(tmp_path, "wb_pip", "v1")
    pov = {(r["source_geo"], r["source_period"]): r for r in obs.to_dicts()
           if r["source_series"].startswith("pobreza_8.30")}
    assert pov[("MEX", "2014")]["source_obs_status"] == ""
    assert pov[("MEX", "2016")]["source_obs_status"] == "B"      # nuevo periodo comparable
    assert pov[("MEX", "2018")]["source_obs_status"] == "E"      # sin microdatos
    assert pov[("ARG", "2020")]["source_series"] == "pobreza_8.30.ingreso.urbano"
    assert pov[("BOL", "2020")]["source_series"] == "pobreza_8.30.ingreso.nacional"
    assert pov[("PER", "2020")]["source_series"] == "pobreza_8.30.consumo.nacional"
    assert sum(1 for k in pov if k[0] == "BOL") == 1
    assert any(r["source_series"] == "gini.ingreso.nacional" for r in obs.to_dicts())
