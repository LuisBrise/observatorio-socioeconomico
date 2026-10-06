"""Conector de la versión pública del RNPDNO (Comisión Nacional de Búsqueda).

El sitio exige una sesión (cookie) que se obtiene al abrir la página inicial; después responde
consultas JSON por POST. Se guarda, tal como llega:

- `totales.json`: totales por estatus en el momento de la consulta.
- `anio_sexo_{estatus}.json`: personas por año de desaparición y sexo, para cada estatus de
  `dataset.archivos` (0 = todas; 7 = desaparecidas y no localizadas; 2 = localizadas con vida;
  3 = localizadas sin vida).

El registro cambia continuamente: cada descarga es una instantánea con su fecha de consulta.
Las consultas son pocas y ligeras (una por estatus), conforme a los términos de uso del sitio.
"""

from __future__ import annotations

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://versionpublicarnpdno.segob.gob.mx"
_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/Dashboard/Sociodemografico"}


class RNPDNO:
    name = "rnpdno"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=120)

    def _post(self, path: str, payload: dict) -> httpx.Response:
        resp = self.client.post(f"{BASE}{path}", json=payload, headers=_HEADERS)
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            raise ValueError(f"RNPDNO {path}: respuesta no JSON ({resp.headers.get('content-type')})")
        return resp

    def fetch(self, dataset: Dataset) -> FetchResult:
        http.get(self.client, f"{BASE}/")  # abre la sesión (cookie)
        files = []
        totales = self._post("/ContextoGeneral/Totales", {"titulo": "", "subtitulo": ""})
        files.append(RawFile("totales.json", totales.content, f"{BASE}/ContextoGeneral/Totales",
                             content_type=totales.headers.get("content-type", "")))
        for estatus in dataset.archivos:
            payload = {"titulo": "", "subtitulo": "POR AÑO Y SEXO", "idEstatusVictima": estatus,
                       "idEstado": "0", "mostrarFechaNula": "1", "mostrarEdadNula": "1"}
            resp = self._post("/SocioDemografico/AreaChartSexoAnio", payload)
            if not resp.json().get("Series"):
                raise ValueError(f"RNPDNO estatus {estatus}: respuesta sin series: {resp.text[:300]!r}")
            files.append(RawFile(f"anio_sexo_{estatus}.json", resp.content,
                                 f"{BASE}/SocioDemografico/AreaChartSexoAnio", params=payload,
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=None)
