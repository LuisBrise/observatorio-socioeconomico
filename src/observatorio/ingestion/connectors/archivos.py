"""Conector genérico para fuentes que publican archivos de descarga (sin API).

Descarga cada URL de `dataset.archivos` y la guarda con su nombre original.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile


class FileDownload:
    name = "descarga_archivos"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=600)

    def fetch(self, dataset: Dataset) -> FetchResult:
        if not dataset.archivos:
            raise ValueError(f"{dataset.id}: el catálogo no declara `archivos`")
        files = []
        for url in dataset.archivos:
            resp = http.get(self.client, url)
            name = PurePosixPath(unquote(urlparse(url).path)).name
            files.append(RawFile(name, resp.content, url,
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=None)
