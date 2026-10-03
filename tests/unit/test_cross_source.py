from datetime import date

import polars as pl
import yaml

from observatorio.catalog import load_catalog
from observatorio.validation.cross_source import compare_indicator

IND = "eco.actividad.ingreso_pc.pib_pc_ppa"
A, B = "wb_wdi:NY.GDP.PCAP.PP.KD", "fmi_weo:NGDPRPPPPC"


def configure(root, origen=None, discrepancy=False):
    if origen:
        path = root / "datasets" / "fmi_weo.yaml"
        ds = yaml.safe_load(path.read_text())
        ds["series"][0]["origen"] = origen
        path.write_text(yaml.safe_dump(ds, allow_unicode=True))
    if discrepancy:
        (root / "discrepancies" / "DIS-900.yaml").write_text(yaml.safe_dump({
            "id": "DIS-900", "indicador": IND, "series": [A, B],
            "diferencia_observada": "x", "causas_documentadas": [{"tipo": "ppa", "descripcion": "y"}],
            "presentacion": "rango", "estado": "explicada", "fecha": date(2026, 10, 3)}))
    return load_catalog(root)


def obs(diff: float, status_b: str = "A") -> pl.DataFrame:
    rows = []
    for geo in ("MEX", "BRA"):
        for y in range(2000, 2010):
            rows += [(A, geo, str(y), 100.0, "A"), (B, geo, str(y), 100.0 * (1 + diff), status_b)]
    return pl.DataFrame(rows, schema=["series_id", "geo_id", "period", "value", "obs_status"],
                        orient="row")


def test_single_source_is_reported(env):
    _, cat = env
    res, _ = compare_indicator(obs(0.0).filter(pl.col("series_id") == A), cat, IND)
    assert res[0].check == "fuente_unica"


def test_undocumented_discrepancy_warns(env):
    paths, _ = env
    cat = configure(paths.catalog)
    res, details = compare_indicator(obs(0.12), cat, IND)
    assert res[0].check == "discrepancia_sin_documentar" and res[0].severity == "ADVERTENCIA"
    assert abs(details[(A, B)]["dif_rel"][0] - 0.12) < 1e-9


def test_forecasts_are_not_compared(env):
    paths, _ = env
    cat = configure(paths.catalog)
    res, _ = compare_indicator(obs(0.12, status_b="F"), cat, IND)
    assert res[0].check == "sin_traslape"


def test_documented_discrepancy_is_info(env):
    paths, _ = env
    cat = configure(paths.catalog, discrepancy=True)
    res, _ = compare_indicator(obs(0.12), cat, IND)
    assert res[0].severity == "INFO" and "DIS-900" in res[0].message


def test_same_origin_is_not_verification(env):
    paths, _ = env
    cat = configure(paths.catalog, origen="banco_mundial_icp+cuentas_nacionales")
    res, _ = compare_indicator(obs(0.12), cat, IND)
    assert res[0].check == "fuentes_no_independientes"
