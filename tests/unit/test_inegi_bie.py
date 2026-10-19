# ruff: noqa: E501  (respuestas de la API como literales)
"""BIE de INEGI: el token nunca queda en archivos ni mensajes; periodos mensuales; contexto de tarjetas."""

import datetime as dt
import json

import httpx
import polars as pl
import pytest

from observatorio.ingestion.base import FetchResult, RawFile, RawStore
from observatorio.ingestion.connectors.inegi_bie import INEGIBIE
from observatorio.staging.inegi_bie import parse_inegi_bie
from observatorio.transform import get_transform
from observatorio.viz_data.d2 import _contexto

TOKEN = "token-secreto-de-prueba-123"
RESPUESTA = {"Series": [{"INDICADOR": "910392", "FREQ": "8", "LASTUPDATE": "08/10/2026 12:00:00 a. m.",
                         "OBSERVATIONS": [{"TIME_PERIOD": "2026/09", "OBS_VALUE": "146.075", "OBS_STATUS": "3"},
                                          {"TIME_PERIOD": "2026/08", "OBS_VALUE": "145.462", "OBS_STATUS": "3"},
                                          {"TIME_PERIOD": "2026/07", "OBS_VALUE": "", "OBS_STATUS": "3"}]}]}


class DS:
    archivos = ["910392"]


def test_conector_no_registra_el_token():
    vistas = []

    def handler(request: httpx.Request) -> httpx.Response:
        vistas.append(str(request.url))
        return httpx.Response(200, json=RESPUESTA)

    res = INEGIBIE(client=httpx.Client(transport=httpx.MockTransport(handler)), token=TOKEN).fetch(DS())
    assert TOKEN in vistas[0]  # la consulta sí lo usa…
    f = res.files[0]
    assert TOKEN not in f.url and "{INEGI_TOKEN}" in f.url  # …pero no se registra
    assert TOKEN not in json.dumps(f.params)
    assert res.source_declared_version == "2026-10-08"


def test_conector_errores_sin_url():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="no")

    with pytest.raises(RuntimeError) as exc:
        INEGIBIE(client=httpx.Client(transport=httpx.MockTransport(handler)), token=TOKEN).fetch(DS())
    assert TOKEN not in str(exc.value) and exc.value.__cause__ is None


def test_rawstore_rechaza_manifiesto_con_token(tmp_path, monkeypatch):
    from observatorio.catalog.models import Dataset  # noqa: F401  (tipo del dataset)

    monkeypatch.setenv("INEGI_TOKEN", TOKEN)

    class D:
        id = "x"
        fuente = "inegi"

        class licencia:  # noqa: N801
            @staticmethod
            def model_dump(mode=None):
                return {}

    store = RawStore(tmp_path / "raw", tmp_path)
    malo = FetchResult(files=[RawFile("a.json", b"{}", f"https://x/{TOKEN}")])
    with pytest.raises(ValueError, match="token"):
        store.store(D, malo, "inegi_bie")
    assert not list((tmp_path / "raw").rglob("*.partial"))  # no deja restos


def test_parse_inegi_bie(tmp_path):
    (tmp_path / "bie_910392.json").write_text(json.dumps(RESPUESTA))
    obs, _ = parse_inegi_bie(tmp_path, "inegi_bie_coyuntura", "v1")
    assert sorted(obs["source_period"]) == ["2026M08", "2026M09"]  # el vacío se omite
    assert obs.filter(obs["source_period"] == "2026M09")["value"][0] == 146.075


def _serie(valores, desde=dt.date(2014, 1, 1)):
    fechas = [desde.replace(year=desde.year + (desde.month - 1 + i) // 12, month=(desde.month - 1 + i) % 12 + 1)
              for i in range(len(valores))]
    return pl.DataFrame({"geo_id": "MEX", "period": [f.strftime("%Y-%m") for f in fechas],
                         "period_start": fechas, "value": valores})


def test_var_interanual_empareja_por_fecha():
    v = _serie([100.0 + i for i in range(24)])
    out = get_transform("var_interanual@1")(v, rezago=12)
    assert out.height == 12 and abs(out["value"][0] - 12.0) < 1e-9  # 112/100 - 1


def test_contexto_con_ruptura_no_compara_con_la_historia():
    v = _serie([float(i % 7) for i in range(150)])
    sin = _contexto(v, "pp", [])
    assert sin["percentil"] is not None and sin["cambio_12m"] is not None
    con = _contexto(v, "pp", [v["period"][-3]])
    assert con["percentil"] is None and con["cambio_12m"] is None and con["ruptura"] == v["period"][-3]
