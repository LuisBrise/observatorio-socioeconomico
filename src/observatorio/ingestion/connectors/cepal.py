"""Conector de CEPALSTAT (API v1). Un archivo JSON por indicador: `cepal_{id}.json`.
Los ids de indicador se declaran en `dataset.archivos`."""

from __future__ import annotations

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator"


class CEPALSTAT:
    name = "cepalstat"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=180)

    def fetch(self, dataset: Dataset) -> FetchResult:
        files = []
        for ind in dataset.archivos:
            url = f"{BASE}/{ind}/data"
            params = {"lang": "es", "format": "json", "in": 1}
            resp = http.get(self.client, url, params=params)
            body = resp.json().get("body", {})
            if not body.get("data") or not body.get("dimensions"):
                raise ValueError(f"Respuesta inesperada de CEPALSTAT para {ind}: {resp.text[:300]!r}")
            files.append(RawFile(f"cepal_{ind}.json", resp.content, url, params=params,
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=None)
