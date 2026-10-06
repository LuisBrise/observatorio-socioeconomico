"""Parser de la medición oficial de pobreza (INEGI) con un libro que imita pm_ip_2024.xlsx."""

import xlsxwriter

from observatorio.staging.inegi_pm import parse_inegi_pm


def make_book(path):
    wb = xlsxwriter.Workbook(path)
    c1 = wb.add_worksheet("Cuadro 1")
    c1.write(0, 0, "INEGI. Pobreza Multidimensional (PM) 2024")
    c1.write(6, 0, "Indicador")
    c1.write(6, 4, "Población")
    c1.write(6, 10, "Porcentaje")
    c1.write(6, 16, "Carencias promedio")
    for k, y in enumerate(["2016", "2018", "2020", "2022", "2024"]):
        c1.write(7, 4 + k, y)
        c1.write(7, 10 + k, y)
        c1.write(7, 16 + k, y)
    c1.write(8, 0, "Pobreza")
    c1.write(9, 0, "Población en situación de pobreza")
    c1.write_row(9, 4, ["52.2", "51.9", "55.7", "46.8", "38.5"])
    c1.write_row(9, 10, ["43.2", "41.9", "43.9", "36.3", "29.6"])
    c1.write_row(9, 16, ["2.2", "2.3", "2.4", "2.4", "2.5"])
    c1.write(10, 1, "Población en situación de pobreza extrema")      # sangría: columna 1
    c1.write_row(10, 10, ["7.2", "7.0", "8.5", "7.1", "5.3"])
    ip = wb.add_worksheet("IP cuadro 1")
    ip.write(4, 0, "2024")
    ip.write(6, 4, "Población")
    ip.write(6, 10, "Porcentaje")
    ip.write(10, 0, "Población en situación de pobreza")
    ip.write_row(10, 10, ["29.6", "0.33", "28.9", "30.2", "1.1"])
    wb.close()


def test_parse_official_poverty(tmp_path):
    make_book(str(tmp_path / "pm_ip_2024.xlsx"))
    obs, _ = parse_inegi_pm(tmp_path, "inegi_pm", "v1")
    v = {(r["source_series"], r["source_period"]): r["value"] for r in obs.to_dicts()}
    assert v[("pobreza", "2016")] == 43.2 and v[("pobreza", "2024")] == 29.6   # bloque porcentaje
    assert v[("pobreza_extrema", "2020")] == 8.5
    assert v[("pobreza.L95", "2024")] == 28.9 and v[("pobreza.U95", "2024")] == 30.2
    assert ("pobreza", "2016") in v and not any(k[0] == "pobreza" and v[k] == 52.2 for k in v)
