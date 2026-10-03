"""Conector del Banco Mundial (World Development Indicators, API v2).

Guarda sin modificar:
- las páginas JSON de datos de cada serie: `{codigo}.p{n}.json`
- los metadatos de cada serie: `{codigo}.meta.json` (para detectar cambios de definición)
- la lista de economías: `countries.json` (distingue países de agregados)
"""

from __future__ import annotations

import json

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://api.worldbank.org/v2"
PER_PAGE = 20000


class WorldBankWDI:
    name = "wb_wdi"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client()

    def _get(self, path: str, params: dict) -> RawFile:
        url = f"{BASE}/{path}"
        resp = http.get(self.client, url, params=params)
        return RawFile(name="", content=resp.content, url=url, params=params,
                       content_type=resp.headers.get("content-type", ""))

    def _paged(self, path: str, stem: str) -> tuple[list[RawFile], str | None]:
        files: list[RawFile] = []
        page, pages, last_updated = 1, 1, None
        while page <= pages:
            f = self._get(path, {"format": "json", "per_page": PER_PAGE, "page": page})
            payload = json.loads(f.content)
            if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[0], dict):
                # La API responde [ {"message": [...]} ] ante códigos inválidos.
                raise ValueError(f"Respuesta inesperada de {f.url}: {payload!r:.300}")
            meta = payload[0]
            pages = int(meta.get("pages", 1))
            last_updated = meta.get("lastupdated", last_updated)
            f.name = f"{stem}.p{page}.json"
            files.append(f)
            page += 1
        return files, last_updated

    def fetch(self, dataset: Dataset) -> FetchResult:
        files: list[RawFile] = []
        updated: dict[str, str | None] = {}
        for s in dataset.series:
            data_files, last_updated = self._paged(f"country/all/indicator/{s.codigo}", s.codigo)
            files.extend(data_files)
            updated[s.codigo] = last_updated
            meta = self._get(f"indicator/{s.codigo}", {"format": "json"})
            meta.name = f"{s.codigo}.meta.json"
            files.append(meta)
        countries, _ = self._paged("country", "countries")
        files.extend(countries)
        declared = max((v for v in updated.values() if v), default=None)
        return FetchResult(files=files, source_declared_version=declared)
