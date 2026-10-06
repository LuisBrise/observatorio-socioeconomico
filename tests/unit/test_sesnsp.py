# ruff: noqa: E501  (fixtures con líneas HTML y CSV literales)
"""SESNSP: localizar el enlace por su texto, sumar meses y entidades, detectar años incompletos."""

import io
import zipfile

import httpx
import polars as pl

from observatorio.ingestion.connectors.sesnsp import SESNSP, find_links
from observatorio.staging.sesnsp import parse_sesnsp
from observatorio.transform import get_transform

PAGINA = """<ul>
<li><a href="https://x.sharepoint.com/:u:/g/a?e=1" target="_blank">2015 - 2025 (Fuero Com&uacute;n - Delitos). Incidencia delictiva estatal</a></li>
<li><a href="https://x.sharepoint.com/:u:/g/b?e=2" target="_blank">2015 - 2025 (Fuero Com&uacute;n - V&iacute;ctimas). Incidencia delictiva estatal</a></li>
<li><a href="https://x.sharepoint.com/:u:/g/c?e=3" target="_blank">2015 -&nbsp;2025 (Fuero com&uacute;n - V&iacute;ctimas). Incidencia delictiva municipal</a></li>
</ul>"""
PATRON = r"^2015 ?- ?20\d\d \(Fuero Común - Víctimas\)\. Incidencia delictiva estatal$"

ENC = ("Año,Clave_Ent,Entidad,Bien jurídico afectado,Tipo de delito,Subtipo de delito,Modalidad,Sexo,"
       "Rango de edad," + ",".join(["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                                    "Septiembre", "Octubre", "Noviembre", "Diciembre"]))


def fila(anio, ent, subtipo, sexo, meses):
    return f"{anio},{ent},E{ent},La vida,X,{subtipo},Con arma de fuego,{sexo},Adultos (18 y más)," + ",".join(meses)


def zip_csv(text: str, enc: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("victimas.csv", text.encode(enc))
    return buf.getvalue()


def test_find_links_por_texto():
    links = find_links(PAGINA, PATRON)
    assert links == [("https://x.sharepoint.com/:u:/g/b?e=2",
                      "2015 - 2025 (Fuero Común - Víctimas). Incidencia delictiva estatal")]


def test_parse_sesnsp(tmp_path):
    doce = ["1"] * 12
    filas = [ENC,
             fila(2024, 1, "Homicidio doloso", "Hombre", doce), fila(2024, 2, "Homicidio doloso", "Mujer", doce),
             fila(2024, 1, "Feminicidio", "Mujer", ["2"] * 12), fila(2024, 1, "Robo", "Hombre", doce),
             fila(2025, 1, "Homicidio doloso", "Hombre", ["3"] * 8 + [""] * 4)]
    (tmp_path / "sesnsp_0.zip").write_bytes(zip_csv("\n".join(filas), "latin-1"))
    obs, geos = parse_sesnsp(tmp_path, "sesnsp_victimas", "v1")
    assert set(geos["source_geo"]) == {"00", "01", "02"}
    ent = obs.filter(obs["source_geo"] == "02")
    assert ent.filter(ent["source_series"] == "homicidio_doloso.mujer")["value"].to_list() == [12.0]
    obs = obs.filter(obs["source_geo"] == "00")
    v = {(r["source_series"], r["source_period"]): (r["value"], r["source_obs_status"]) for r in obs.to_dicts()}
    assert v[("homicidio_doloso.total", "2024")] == (24.0, "")
    assert v[("homicidio_doloso.mujer", "2024")] == (12.0, "")
    assert v[("feminicidio.total", "2024")] == (24.0, "")
    assert v[("homicidio_doloso.total", "2025")] == (24.0, "P")  # meses vacíos → preliminar
    assert not any(s.startswith("robo") for s, _ in v)


def test_parse_sesnsp_utf8_con_bom(tmp_path):
    text = "\ufeff" + "\n".join([ENC, fila(2024, 1, "Feminicidio", "Mujer", ["1"] * 12)])
    (tmp_path / "sesnsp_0.zip").write_bytes(zip_csv(text, "utf-8"))
    obs, _ = parse_sesnsp(tmp_path, "d", "v1")
    assert obs.filter(obs["source_geo"] == "00")["value"].to_list() == [12.0]


def test_conector_descarga_con_cookie_de_invitado():
    pedidos = []

    def handler(request: httpx.Request) -> httpx.Response:
        pedidos.append(str(request.url))
        if "gob.mx" in request.url.host:
            return httpx.Response(200, text=PAGINA)
        if "download=1" in str(request.url):
            return httpx.Response(200, content=b"PK\x03\x04zip", headers={"content-type": "application/x-zip-compressed"})
        return httpx.Response(200, text="ok", headers={"set-cookie": "FedAuth=x; path=/"})

    class DS:
        archivos = [PATRON]

    res = SESNSP(client=httpx.Client(transport=httpx.MockTransport(handler))).fetch(DS())
    assert [f.name for f in res.files] == ["pagina_datos_abiertos.html", "sesnsp_0.zip"]
    assert pedidos[-2] == "https://x.sharepoint.com/:u:/g/b?e=2"
    assert pedidos[-1].endswith("download=1")


def test_suma():
    a = pl.DataFrame({"geo_id": ["MEX"], "period": ["2024"], "period_start": [None], "value": [2.0]})
    b = a.with_columns(pl.lit(3.0).alias("value"))
    assert get_transform("suma@1")(a, b)["value"].to_list() == [5.0]
