"""Conector de la API del Banco de Indicadores de INEGI (BIE), con token.

Cada entrada de `dataset.archivos` es un identificador de indicador del BIE. Se guarda la respuesta
completa (`bie_{id}.json`), que incluye la fecha de última actualización (`LASTUPDATE`).

El token va en la ruta de la URL: la URL que se registra en el manifiesto lleva el marcador
`{INEGI_TOKEN}` en su lugar y los errores se reportan sin la URL, porque el archivo crudo y los
registros de GitHub Actions son públicos.
"""

from __future__ import annotations

import os
import re

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"
RUTA = "{id}/es/00/false/BIE-BISE/2.0/{token}"


class INEGIBIE:
    name = "inegi_bie"

    def __init__(self, client: httpx.Client | None = None, token: str | None = None):
        self.client = client or http.make_client(timeout=120)
        self.token = token or os.environ.get("INEGI_TOKEN", "")

    def _get(self, indicador: str) -> httpx.Response:
        url = f"{BASE}/{RUTA.format(id=indicador, token=self.token)}"
        try:
            resp = http.get(self.client, url, params={"type": "json"})
        except Exception as exc:  # sin la URL: contiene el token
            nombre = type(exc).__name__
            raise RuntimeError(f"INEGI BIE {indicador}: fallo de la consulta ({nombre})") from None
        return resp

    def fetch(self, dataset: Dataset) -> FetchResult:
        if not self.token:
            raise RuntimeError("Falta INEGI_TOKEN (ver docs/guias/tokens-api.md)")
        files, actualizaciones = [], []
        for indicador in dataset.archivos:
            resp = self._get(indicador)
            data = resp.json()
            if not isinstance(data, dict) or not data.get("Series"):
                raise ValueError(f"INEGI BIE {indicador}: respuesta sin series ({str(data)[:200]!r})")
            if m := re.match(r"(\d{2})/(\d{2})/(\d{4})", data["Series"][0].get("LASTUPDATE") or ""):
                actualizaciones.append(f"{m[3]}-{m[2]}-{m[1]}")
            files.append(RawFile(f"bie_{indicador}.json", resp.content,
                                 f"{BASE}/{RUTA.format(id=indicador, token='{INEGI_TOKEN}')}",
                                 params={"type": "json"},
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=max(actualizaciones, default=None))
