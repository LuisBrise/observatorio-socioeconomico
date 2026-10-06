# ruff: noqa: E501
"""RNPDNO: año de desaparición, categoría sin año, años preliminares y sesión del conector."""

import json

import httpx

from observatorio.ingestion.connectors.rnpdno import RNPDNO
from observatorio.staging.rnpdno import parse_rnpdno


def resp(h, m, i):
    cats = ["1.CIFRA SIN  AÑO DE REFERENCIA", "2020", "2025", "2026"]
    return {"XAxisCategories": cats, "Series": [{"name": "Hombre", "data": h}, {"name": "Mujer", "data": m},
                                                {"name": "Indeterminado", "data": i}]}


def test_parse_rnpdno(tmp_path):
    (tmp_path / "anio_sexo_7.json").write_text(json.dumps(resp([10, 5, 6, 2], [3, 1, 2, 1], [1, 0, 0, 0])))
    (tmp_path / "anio_sexo_3.json").write_text(json.dumps(resp([2, 1, 1, 0], [0, 0, 1, 0], [0, 0, 0, 0])))
    obs, _ = parse_rnpdno(tmp_path, "rnpdno", "2026-10-06T163417Z")
    v = {(r["source_series"], r["source_period"]): (r["value"], r["source_obs_status"])
         for r in obs.to_dicts()}
    assert v[("desaparecidas.total", "2020")] == (6.0, "")
    assert v[("desaparecidas.mujer", "2025")] == (2.0, "P")  # año anterior a la consulta
    assert v[("desaparecidas.total", "2026")] == (3.0, "P")  # año en curso
    assert v[("desaparecidas.sin_anio", "2026")] == (14.0, "")  # acervo sin año → año de consulta
    # Localizadas sin vida: solo el total (sin desglose por sexo ni categoría sin año).
    assert {s for s in obs["source_series"] if s.startswith("localizadas")} == {"localizadas_sin_vida.total"}


def test_conector_abre_sesion_y_pide_cada_estatus():
    llamadas = []

    def handler(request: httpx.Request) -> httpx.Response:
        llamadas.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, text="<html></html>", headers={"set-cookie": "s=1; path=/"})
        if request.url.path.endswith("/Totales"):
            return httpx.Response(200, json={"TotalGlobal": "10"})
        return httpx.Response(200, json=resp([1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]))

    class DS:
        archivos = ["7", "3"]

    res = RNPDNO(client=httpx.Client(transport=httpx.MockTransport(handler)), pausa=0).fetch(DS())
    assert llamadas[0] == ("GET", "/")
    assert [f.name for f in res.files] == ["totales.json", "anio_sexo_7.json", "anio_sexo_3.json"]
    assert json.loads(next(f for f in res.files if f.name == "anio_sexo_3.json").content)["Series"]


def test_entidades(tmp_path):
    (tmp_path / "anio_sexo_7.json").write_text(json.dumps(resp([3, 2, 2, 1], [1, 1, 1, 0], [0, 0, 0, 0])))
    (tmp_path / "anio_sexo_7_e09.json").write_text(json.dumps(resp([2, 1, 1, 1], [1, 0, 1, 0], [0, 0, 0, 0])))
    (tmp_path / "anio_sexo_7_e33.json").write_text(json.dumps(resp([1, 1, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0])))
    obs, geos = parse_rnpdno(tmp_path, "rnpdno", "2026-10-06T163417Z")
    assert set(geos["source_geo"]) == {"00", "09", "33"}
    tot = obs.filter(obs["source_series"] == "desaparecidas.total")
    nac = tot.filter(tot["source_geo"] == "00")["value"].sum()
    assert nac == tot.filter(tot["source_geo"] != "00")["value"].sum()  # entidades suman el nacional


def test_conector_consulta_cada_entidad():
    estados = [{"Value": 0, "Text": "--TODOS--"}, {"Value": 9, "Text": "CDMX"}, {"Value": 33, "Text": "SE DESCONOCE"}]
    pedidos = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, text="<html></html>")
        body = json.loads(request.content or b"{}")
        pedidos.append((request.url.path, body.get("idEstado")))
        if request.url.path.endswith("/Estados"):
            return httpx.Response(200, json=estados)
        if request.url.path.endswith("/Totales"):
            return httpx.Response(200, json={})
        return httpx.Response(200, json=resp([1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]))

    class DS:
        archivos = ["7", "7@entidades"]

    res = RNPDNO(client=httpx.Client(transport=httpx.MockTransport(handler)), pausa=0).fetch(DS())
    nombres = [f.name for f in res.files]
    assert {"anio_sexo_7.json", "anio_sexo_7_e09.json", "anio_sexo_7_e33.json", "catalogo_estados.json"} <= set(nombres)
    assert ("/SocioDemografico/AreaChartSexoAnio", "9") in pedidos
