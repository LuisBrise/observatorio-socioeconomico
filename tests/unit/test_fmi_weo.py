"""Parser del WEO con un extracto con el formato real de la API SDMX-CSV del FMI."""

import polars as pl

from observatorio.staging.fmi_weo import last_actual_year, parse_fmi_weo

HEADER = ("DATAFLOW,COUNTRY,INDICATOR,FREQUENCY,TIME_PERIOD,OBS_VALUE,SCALE,"
          "LATEST_ACTUAL_ANNUAL_DATA,PUBLICATION_DATE")
ROWS = [
    "IMF.RES:WEO(9.0.0),MEX,NGDPRPPPPC,A,2024,21996.13,0,2024,2026-04-14T13:00:00Z",
    "IMF.RES:WEO(9.0.0),MEX,NGDPRPPPPC,A,2025,22100.00,0,2024,2026-04-14T13:00:00Z",
    "IMF.RES:WEO(9.0.0),IND,NGDPRPPPPC,A,2020,7000.00,0,FY2019/20,2026-04-14T13:00:00Z",
    "IMF.RES:WEO(9.0.0),G110,NGDPRPPPPC,A,2025,50000.00,0,,2026-04-14T13:00:00Z",
    "IMF.RES:WEO(9.0.0),G110,NGDPRPPPPC,A,2024,49000.00,0,,2026-04-14T13:00:00Z",
]


def test_last_actual_year():
    assert last_actual_year("2024") == 2024
    assert last_actual_year("FY2019/20") == 2019
    assert last_actual_year("Not applicable") is None
    assert last_actual_year(None) is None


def test_parser_marks_projections_and_aggregates(tmp_path):
    (tmp_path / "NGDPRPPPPC.csv").write_text("\n".join([HEADER, *ROWS]) + "\n")
    obs, geos = parse_fmi_weo(tmp_path, "fmi_weo", "v1")
    status = {(r["source_geo"], r["source_period"]): r["source_obs_status"] for r in obs.to_dicts()}
    assert status[("MEX", "2024")] == "" and status[("MEX", "2025")] == "F"
    assert status[("IND", "2020")] == "F"           # año fiscal 2019/20 → último observado 2019
    assert status[("G110", "2024")] == ""           # sin dato: edición 2026 → observado hasta 2025
    assert status[("G110", "2025")] == ""
    assert geos.filter(pl.col("source_geo") == "G110")["is_aggregate"][0]
    assert not geos.filter(pl.col("source_geo") == "MEX")["is_aggregate"][0]
