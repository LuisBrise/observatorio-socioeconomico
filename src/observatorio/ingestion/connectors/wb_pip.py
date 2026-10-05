"""Conector del Banco Mundial: Poverty and Inequality Platform (PIP), API v1.

Una petición por línea de pobreza (todas las economías, todos los años de encuesta, sin
interpolar: `fill_gaps=false`). Guarda las respuestas JSON sin modificar: `pip_{línea}.json`.
"""

from __future__ import annotations

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://api.worldbank.org/pip/v1/pip"
POVERTY_LINES = ("3.00", "4.20", "8.30")  # PPA 2021 (líneas vigentes desde junio de 2025)


class WorldBankPIP:
    name = "wb_pip"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=300)

    def fetch(self, dataset: Dataset) -> FetchResult:
        files = []
        for line in POVERTY_LINES:
            params = {"country": "all", "year": "all", "povline": line, "fill_gaps": "false",
                      "format": "json"}
            resp = http.get(self.client, BASE, params=params)
            payload = resp.json()
            if not isinstance(payload, list) or not payload or "headcount" not in payload[0]:
                raise ValueError(f"Respuesta inesperada de PIP para la línea {line}: {resp.text[:300]!r}")
            files.append(RawFile(f"pip_{line}.json", resp.content, BASE, params=params,
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=None)
