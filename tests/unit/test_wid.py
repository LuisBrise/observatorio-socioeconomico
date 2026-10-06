"""WID: parser (imputados, ISO-2 → ISO-3) y lector de ZIP remoto por rangos (sin red)."""

import gzip
import io
import os
import zipfile

import httpx

from observatorio.ingestion.remote_zip import open_remote_zip
from observatorio.staging.wid import parse_wid
from observatorio.viz_data.d1 import _tramos_texto

CSV = ("country;variable;percentile;year;value;age;pop;data_quality\n"
       "MX;sptincj992;p90p100;2001;0.544;992;j;1\n"
       "MX;sptincj992;p90p100;2010;0.621;992;j;5\n"
       "MX;sptincj992;p50p90;2010;0.30;992;j;5\n"          # percentil no usado
       "MX;gptincj992;p0p100;2010;0.746;992;j;5\n")


def test_parse_wid(tmp_path):
    (tmp_path / "WID_data_MX.csv.gz").write_bytes(gzip.compress(CSV.encode(), mtime=0))
    obs, geos = parse_wid(tmp_path, "wid", "v1")
    r = {(x["source_series"], x["source_period"]): x for x in obs.to_dicts()}
    assert set(obs["source_geo"]) == {"MEX"}
    assert r[("top10", "2001")]["source_obs_status"] == "I"   # data_quality <= 1
    assert r[("top10", "2010")]["source_obs_status"] == ""
    assert ("gini", "2010") in r and len(r) == 3


def test_remote_zip_reads_member_with_ranges():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("WID_data_MX.csv", CSV)
        z.writestr("WID_data_BR.csv", os.urandom(200_000), compress_type=zipfile.ZIP_STORED)
    blob = buf.getvalue()
    requests = []

    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "HEAD":
            return httpx.Response(200, headers={"accept-ranges": "bytes",
                                                "content-length": str(len(blob))})
        start, end = map(int, req.headers["range"].removeprefix("bytes=").split("-"))
        requests.append((start, end))
        return httpx.Response(206, content=blob[start:end + 1])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    zf, remote = open_remote_zip(client, "https://example.org/all.zip")
    assert zf.read("WID_data_MX.csv").decode() == CSV
    assert sum(e - s + 1 for s, e in requests) < len(blob)    # no descargó todo el archivo


def test_tramos_texto():
    assert _tramos_texto(["1984", "1985", "1986", "2023", "2024"]) == "1984–1986 y 2023–2024"
    assert _tramos_texto(["2000"]) == "2000"
    assert _tramos_texto([]) == ""
