"""Tabulados de INEGI: matriz fila×(periodo×sexo), separador de miles y cifras preliminares."""

import json

import httpx
import pytest

from observatorio.ingestion.connectors.inegi_tabulados import INEGITabulados
from observatorio.staging.inegi_tabulados import parse_inegi_tabulados

DATOS = {
    "stub": [{"code": "Entidad", "label": ["Total", "Aguascalientes"]}],
    "heading": [{"code": "Periodo", "label": ["2024", "2025"]},
                {"code": "Sexo", "label": ["Total", "Hombres", "Mujeres", "No especificado"]}],
    # Total: 2024 → 33,550 = 29,448 + 3,739 + 363; 2025 → 27,989 (preliminar)
    "data": ["33,550||", "29,448||", "3,739||", "363||", "27,989||", "24,506||", "3,154||", "329||",
             "114||", "98||", "14||", "2||", "151||", "132||", "15||", "4||"],
}
INFO = {"note": "Notas: ... Los datos de 2025 son preliminares, debido a que ..."}


def test_parse_inegi_tabulados(tmp_path):
    (tmp_path / "Mortalidad__Mortalidad_08.datos.json").write_text(json.dumps(DATOS))
    (tmp_path / "Mortalidad__Mortalidad_08.info.json").write_text(json.dumps(INFO))
    obs, geos = parse_inegi_tabulados(tmp_path, "inegi_homicidios", "v1")
    assert set(obs["source_geo"]) == {"MEX"}  # solo el total nacional
    v = {(r["source_series"], r["source_period"]): (r["value"], r["source_obs_status"])
         for r in obs.to_dicts()}
    assert v[("Mortalidad_08.total", "2024")] == (33550.0, "")
    assert v[("Mortalidad_08.mujeres", "2025")] == (3154.0, "P")
    assert v[("Mortalidad_08.no_especificado", "2024")] == (363.0, "")
    assert obs.height == 8


def test_parse_inegi_tabulados_dimensiones_incongruentes(tmp_path):
    bad = {**DATOS, "data": DATOS["data"][:-1]}
    (tmp_path / "X__Y.datos.json").write_text(json.dumps(bad))
    (tmp_path / "X__Y.info.json").write_text(json.dumps(INFO))
    with pytest.raises(ValueError, match="no coincide"):
        parse_inegi_tabulados(tmp_path, "d", "v1")


def test_conector_pide_todas_las_categorias():
    pedidos = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/tabulado"):
            return httpx.Response(200, json={"variables": [
                {"code": "Entidad", "values": ["0", "1"]}, {"code": "Periodo", "values": ["0", "1"]},
                {"code": "Sexo", "values": ["0", "1", "2", "3"]}]})
        pedidos.append(json.loads(request.content))
        if request.url.path.endswith("/datatable"):
            return httpx.Response(200, json=DATOS)
        return httpx.Response(200, json=INFO)

    class DS:
        archivos = ["Mortalidad/Mortalidad_08"]

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = INEGITabulados(client=client).fetch(DS())
    assert [f.name for f in res.files] == ["Mortalidad__Mortalidad_08.tabulado.json",
                                           "Mortalidad__Mortalidad_08.datos.json",
                                           "Mortalidad__Mortalidad_08.info.json"]
    q = pedidos[0]["query"]["query"]
    assert [len(x["selection"]["values"]) for x in q] == [2, 2, 4]
    assert pedidos[0]["stub"] == ["Entidad"] and pedidos[0]["heading"] == ["Periodo", "Sexo"]
