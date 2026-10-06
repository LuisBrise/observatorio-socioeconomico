"""Conector de WID (World Inequality Database): extracción parcial de la descarga masiva.

La descarga masiva (`acceso.endpoint`, ~0.9 GB) es un ZIP con un archivo por país. Mediante
peticiones HTTP Range se extraen solo los miembros listados en `dataset.archivos`
(p. ej., WID_data_MX.csv). Cada miembro se guarda con su contenido original, comprimido con
gzip determinista (mtime=0) para ahorrar espacio: `WID_data_MX.csv.gz`.
"""

from __future__ import annotations

import gzip

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile
from observatorio.ingestion.remote_zip import open_remote_zip


class WID:
    name = "wid"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=300)

    def fetch(self, dataset: Dataset) -> FetchResult:
        url = dataset.acceso.endpoint
        if not url or not dataset.archivos:
            raise ValueError(f"{dataset.id}: faltan acceso.endpoint o archivos (miembros del ZIP)")
        zf, remote = open_remote_zip(self.client, url)
        available = set(zf.namelist())
        missing = [m for m in dataset.archivos if m not in available]
        if missing:
            raise ValueError(f"{dataset.id}: miembros ausentes en {url}: {missing}")
        files = []
        for member in dataset.archivos:
            raw = zf.read(member)  # zipfile verifica el CRC del miembro
            files.append(RawFile(f"{member}.gz", gzip.compress(raw, mtime=0), url,
                                 params={"miembro": member, "etag": remote.etag},
                                 content_type="application/gzip"))
        return FetchResult(files=files, source_declared_version=remote.last_modified)
