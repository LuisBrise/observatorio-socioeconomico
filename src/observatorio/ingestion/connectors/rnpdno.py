"""Conector de la versión pública del RNPDNO (Comisión Nacional de Búsqueda).

El sitio exige una sesión (cookie) que se obtiene al abrir la página inicial; después responde
consultas JSON por POST. Se guarda, tal como llega:

- `totales.json`: totales por estatus en el momento de la consulta.
- `anio_sexo_{estatus}.json`: personas por año de desaparición y sexo, para cada estatus de
  `dataset.archivos` (0 = todas; 7 = desaparecidas y no localizadas; 2 = localizadas con vida;
  3 = localizadas sin vida).
- `anio_sexo_{estatus}_e{clave}.json`: lo mismo por entidad, para las entradas `{estatus}@entidades`
  (clave INEGI del catálogo de estados del sitio).

El registro cambia continuamente: cada descarga es una instantánea con su fecha de consulta.
Las consultas son pocas y ligeras (una por estatus), conforme a los términos de uso del sitio.
"""

from __future__ import annotations

import json
import time

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://versionpublicarnpdno.segob.gob.mx"
_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/Dashboard/Sociodemografico"}


class RNPDNO:
    name = "rnpdno"

    def __init__(self, client: httpx.Client | None = None, pausa: float = 0.5):
        self.client = client or http.make_client(timeout=120)
        self.pausa = pausa

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
        consultas: list[tuple[str, str, str]] = []  # (estatus, idEstado, nombre de archivo)
        for entrada in dataset.archivos:
            estatus, _, alcance = entrada.partition("@")
            if alcance == "entidades":
                estados = self._post("/Catalogo/Estados", {}).json()
                files.append(RawFile("catalogo_estados.json", json.dumps(estados).encode(),
                                     f"{BASE}/Catalogo/Estados", content_type="application/json"))
                consultas += [(estatus, str(e["Value"]), f"anio_sexo_{estatus}_e{int(e['Value']):02d}.json")
                              for e in estados if int(e["Value"]) > 0]
            else:
                consultas.append((estatus, "0", f"anio_sexo_{estatus}.json"))
        for estatus, estado, nombre in consultas:
            payload = {"titulo": "", "subtitulo": "POR AÑO Y SEXO", "idEstatusVictima": estatus,
                       "idEstado": estado, "mostrarFechaNula": "1", "mostrarEdadNula": "1"}
            resp = self._post("/SocioDemografico/AreaChartSexoAnio", payload)
            if not resp.json().get("Series"):
                raise ValueError(f"RNPDNO {nombre}: respuesta sin series: {resp.text[:300]!r}")
            files.append(RawFile(nombre, resp.content, f"{BASE}/SocioDemografico/AreaChartSexoAnio",
                                 params=payload, content_type=resp.headers.get("content-type", "")))
            time.sleep(self.pausa)  # consultas espaciadas: el sitio es un servicio público
        return FetchResult(files=files, source_declared_version=None)
