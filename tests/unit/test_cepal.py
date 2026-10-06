"""CEPALSTAT: dimensiones codificadas, notas de comparabilidad y agregados sin ISO-3."""

import json

from observatorio.staging.cepal import parse_cepal


def body():
    dims = [
        {"name": "País__ESTANDAR", "id": 208, "members": [{"id": 233, "name": "México"},
                                                        {"id": 211, "name": "América Latina"}]},
        {"name": "Pobreza extrema y pobreza", "id": 1361, "members": [{"id": 1362, "name": "Pobreza"}]},
        {"name": "Area geográfica_(EH)", "id": 1364, "members": [{"id": 1365, "name": "Nacional"}]},
        {"name": "Años__ESTANDAR", "id": 29117,
         "members": [{"id": y, "name": str(y)} for y in (2014, 2016, 2018)]},
    ]
    def row(c, y, v, iso, notes=""):
        return {"value": str(v), "iso3": iso, "notes_ids": notes, "dim_208": c, "dim_1361": 1362,
                "dim_1364": 1365, "dim_29117": y}
    data = [row(233, 2014, 45.2, "MEX"), row(233, 2016, 37.6, "MEX", "8609"), row(233, 2018, 35.5, "MEX"),
            row(211, 2016, 30.0, None)]
    return {"body": {"dimensions": dims, "data": data,
                     "footnotes": [{"id": 8609,
                                    "description": "Datos anuales. Serie comparable desde 2016."}]}}


def test_parse_cepal(tmp_path):
    (tmp_path / "cepal_3328.json").write_text(json.dumps(body()))
    obs, geos = parse_cepal(tmp_path, "cepal_pobreza", "v1")
    st = {(r["source_geo"], r["source_period"]): r["source_obs_status"] for r in obs.to_dicts()}
    assert st[("MEX", "2016")] == "B" and st[("MEX", "2018")] == ""
    assert set(obs["source_series"]) == {"pobreza.nacional"}
    agg = geos.filter(geos["source_geo"] == "AGR_AMÉRICA_LATINA")
    assert agg.height == 1 and agg["is_aggregate"][0]
