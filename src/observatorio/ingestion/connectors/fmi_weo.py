"""Conector del FMI: World Economic Outlook vía la API SDMX (api.imf.org).

Guarda sin modificar un archivo SDMX-CSV por serie del catálogo: `{codigo}.csv`.
Respeta los términos del FMI: solo pide las series declaradas (nunca el dataflow completo).
"""

from __future__ import annotations

import csv
import io

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://api.imf.org/external/sdmx/2.1/data/IMF.RES,WEO"
ACCEPT = "application/vnd.sdmx.data+csv;version=1.0.0"


class IMFWEO:
    name = "fmi_weo"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=300)
        self.client.headers["Accept"] = ACCEPT

    def fetch(self, dataset: Dataset) -> FetchResult:
        files, published = [], set()
        for s in dataset.series:
            url = f"{BASE}/.{s.codigo}.A"
            resp = http.get(self.client, url)
            reader = csv.DictReader(io.StringIO(resp.text))
            if not reader.fieldnames or "OBS_VALUE" not in reader.fieldnames:
                raise ValueError(f"Respuesta inesperada de {url}: {resp.text[:300]!r}")
            for row in reader:
                if row.get("PUBLICATION_DATE"):
                    published.add(row["PUBLICATION_DATE"])
            files.append(RawFile(f"{s.codigo}.csv", resp.content, url,
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=max(published, default=None))
