"""Parser de WPP 2024 probabilístico con un libro que imita la estructura real del archivo."""

import xlsxwriter

from observatorio.staging.onu_wpp import VARIANTS, parse_onu_wpp

HEADER = ["Index", "Variant", "Region, subregion, country or area *", "Notes", "Location code",
          "ISO3 Alpha-code", "ISO2 Alpha-code", "SDMX code**", "Type", "Parent code", "Year", "Sex",
          "15-59", "15-64", "20-64", "20-69", "25-64", "25-69"]


def make_book(path):
    wb = xlsxwriter.Workbook(path)
    for sheet in VARIANTS:
        ws = wb.add_worksheet(sheet)
        ws.write(0, 4, "© July 2024 by United Nations")   # filas de portada antes del encabezado
        ws.write(10, 11, "Annual total dependency ratio")
        ws.write_row(16, 0, HEADER)
        base = {"Lower 95": 40, "Lower 80": 44, "Median": 48, "Upper 80": 52, "Upper 95": 56}[sheet]
        rows = [["1", sheet, "World", "", "900", "", "", "1", "World", "0", "2030", "Total"],
                ["2", sheet, "Mexico", "", "484", "MEX", "MX", "484", "Country", "916", "2030", "Total"],
                ["3", sheet, "Mexico", "", "484", "MEX", "MX", "484", "Country", "916", "2030", "Male"]]
        for i, r in enumerate(rows):
            ws.write_row(17 + i, 0, r + [str(base - 5), str(base), "0", "0", "0", "0"])
    ws = wb.add_worksheet("NOTES")
    ws.write(0, 0, "Notes")
    wb.close()


def test_parse_probabilistic_file(tmp_path):
    make_book(str(tmp_path / "UN_PPP2024_Output_Annual_TotalDepRatio.xlsx"))
    obs, geos = parse_onu_wpp(tmp_path, "onu_wpp_prob", "v1")
    mex = {r["source_series"]: r["value"] for r in obs.to_dicts() if r["source_geo"] == "MEX"}
    assert mex == {"TotalDepRatio.15-64.L95": 40.0, "TotalDepRatio.15-64.L80": 44.0,
                   "TotalDepRatio.15-64.MED": 48.0, "TotalDepRatio.15-64.U80": 52.0,
                   "TotalDepRatio.15-64.U95": 56.0}            # solo Sex == Total, columna 15-64
    assert set(obs["source_obs_status"]) == {"F"}               # todo es proyección
    world = geos.filter(geos["source_geo"] == "LOC900")
    assert world["is_aggregate"][0]
