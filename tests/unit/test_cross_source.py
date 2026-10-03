from datetime import date

import polars as pl
import yaml

from observatorio.catalog import load_catalog
from observatorio.validation.cross_source import compare_indicator

IND = "eco.actividad.ingreso_pc.pib_pc_ppa"
A, B = "wb_wdi:NY.GDP.PCAP.PP.KD", "fmi_weo:NGDPRPPPPC"


def add_second_source(root, origen="fmi_weo", discrepancy=False):
    ds = yaml.safe_load((root / "datasets" / "wb_wdi.yaml").read_text())
    ds.update(id="fmi_weo", nombre="WEO (prueba)", conector="fmi_weo",
              series=[{"codigo": "NGDPRPPPPC", "indicador": IND, "unidad": "PPA 2021",
                       "origen": origen}])
    (root / "datasets" / "fmi_weo.yaml").write_text(yaml.safe_dump(ds, allow_unicode=True))
    path = root / "indicators" / "eco.actividad.ingreso_pc.yaml"
    docs = yaml.safe_load(path.read_text())
    docs[0]["series"].append(B)
    path.write_text(yaml.safe_dump(docs, allow_unicode=True))
    if discrepancy:
        (root / "discrepancies" / "DIS-900.yaml").write_text(yaml.safe_dump({
            "id": "DIS-900", "indicador": IND, "series": [A, B],
            "diferencia_observada": "x", "causas_documentadas": [{"tipo": "ppa", "descripcion": "y"}],
            "presentacion": "rango", "estado": "explicada", "fecha": date(2026, 10, 3)}))
    return load_catalog(root)


def obs(diff: float) -> pl.DataFrame:
    rows = []
    for geo in ("MEX", "BRA"):
        for y in range(2000, 2010):
            rows += [(A, geo, str(y), 100.0), (B, geo, str(y), 100.0 * (1 + diff))]
    return pl.DataFrame(rows, schema=["series_id", "geo_id", "period", "value"], orient="row")


def test_single_source_is_reported(env):
    _, cat = env
    res, _ = compare_indicator(obs(0.0).filter(pl.col("series_id") == A), cat, IND)
    assert res[0].check == "fuente_unica"


def test_undocumented_discrepancy_warns(env):
    paths, _ = env
    cat = add_second_source(paths.catalog)
    res, details = compare_indicator(obs(0.12), cat, IND)
    assert res[0].check == "discrepancia_sin_documentar" and res[0].severity == "ADVERTENCIA"
    assert abs(details[(A, B)]["dif_rel"][0] - 0.12) < 1e-9


def test_documented_discrepancy_is_info(env):
    paths, _ = env
    cat = add_second_source(paths.catalog, discrepancy=True)
    res, _ = compare_indicator(obs(0.12), cat, IND)
    assert res[0].severity == "INFO" and "DIS-900" in res[0].message


def test_same_origin_is_not_verification(env):
    paths, _ = env
    cat = add_second_source(paths.catalog, origen="banco_mundial_icp+cuentas_nacionales")
    res, _ = compare_indicator(obs(0.12), cat, IND)
    assert res[0].check == "fuentes_no_independientes"
