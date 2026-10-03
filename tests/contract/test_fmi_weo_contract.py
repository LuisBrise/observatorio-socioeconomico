"""Contrato con la API SDMX del FMI (consulta mínima: una serie, un país, dos años)."""

import csv
import io
import os

import pytest

from observatorio.ingestion import http
from observatorio.ingestion.connectors.fmi_weo import ACCEPT, BASE

pytestmark = pytest.mark.skipif(os.environ.get("OBS_NETWORK_TESTS") != "1",
                                reason="pruebas de red desactivadas")


def test_weo_csv_shape():
    with http.make_client(timeout=120) as client:
        client.headers["Accept"] = ACCEPT
        resp = http.get(client, f"{BASE}/MEX.NGDPRPPPPC.A", {"startPeriod": 2023, "endPeriod": 2024})
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    assert rows and {"COUNTRY", "INDICATOR", "TIME_PERIOD", "OBS_VALUE",
                     "LATEST_ACTUAL_ANNUAL_DATA", "PUBLICATION_DATE"} <= set(rows[0])
    assert "ICP benchmark 2021" in rows[0].get("SERIES_NAME", "")
