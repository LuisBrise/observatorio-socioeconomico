"""Prueba de contrato: ¿la API del Banco Mundial sigue respondiendo como esperamos?

Requiere red. Se ejecuta con `OBS_NETWORK_TESTS=1 uv run pytest tests/contract`
(semanalmente en CI, según docs/diseno/07-actualizacion.md §4).
"""

import json
import os

import pytest

from observatorio.ingestion import http

pytestmark = pytest.mark.skipif(os.environ.get("OBS_NETWORK_TESTS") != "1",
                                reason="pruebas de red desactivadas")


def test_indicator_endpoint_shape():
    with http.make_client() as client:
        resp = http.get(client, "https://api.worldbank.org/v2/country/MEX/indicator/SP.POP.TOTL",
                        {"format": "json", "per_page": 5})
    meta, rows = json.loads(resp.content)
    assert {"page", "pages", "lastupdated"} <= set(meta)
    row = rows[0]
    assert {"indicator", "country", "countryiso3code", "date", "value", "obs_status"} <= set(row)
    assert row["countryiso3code"] == "MEX"


def test_countries_endpoint_marks_aggregates():
    with http.make_client() as client:
        resp = http.get(client, "https://api.worldbank.org/v2/country",
                        {"format": "json", "per_page": 400})
    _, rows = json.loads(resp.content)
    lcn = next(r for r in rows if r["id"] == "LCN")
    assert lcn["region"]["id"] == "NA"
