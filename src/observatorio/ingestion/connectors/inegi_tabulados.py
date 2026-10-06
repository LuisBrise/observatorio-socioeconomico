"""Conector de los tabulados interactivos de INEGI (servicio PxWeb del sitio de INEGI).

Cada entrada de `dataset.archivos` es un cuadro, p. ej. `Mortalidad/Mortalidad_08`. Por cuadro
se guardan tres archivos crudos, tal como los entrega el servicio:

- `{cuadro}.tabulado.json`: estructura (variables y sus valores).
- `{cuadro}.datos.json`: la matriz completa (todas las categorías de todas las variables).
- `{cuadro}.info.json`: título y notas (fuente, cifras preliminares, fecha de actualización).
"""

from __future__ import annotations

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

BASE = "https://www.inegi.org.mx/app/tabulados/pxwebapi/api"


def _stem(cuadro: str) -> str:
    return cuadro.replace("/", "__")


class INEGITabulados:
    name = "inegi_tabulados"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=120)

    def fetch(self, dataset: Dataset) -> FetchResult:
        files = []
        for cuadro in dataset.archivos:
            meta_params = {"lang": "es", "file": cuadro}
            meta = http.get(self.client, f"{BASE}/tabulado", params=meta_params)
            variables = meta.json().get("variables") or []
            if not variables:
                raise ValueError(f"Cuadro de INEGI sin variables: {cuadro}: {meta.text[:300]!r}")
            # Selección completa: todas las categorías de todas las variables.
            seleccion = {
                "file": cuadro, "lang": "es", "showdecimals": None,
                "query": {"query": [{"code": v["code"], "variabletype": None,
                                     "selection": {"filter": "item", "values": list(v["values"])}}
                                    for v in variables],
                          "response": {"format": "json-stat", "params": None}},
                "stub": [variables[0]["code"]],
                "heading": [v["code"] for v in variables[1:]],
                "agg": None,
            }
            datos = http.post_json(self.client, f"{BASE}/datatable", seleccion)
            if not datos.json().get("data"):
                raise ValueError(f"Cuadro de INEGI sin datos: {cuadro}: {datos.text[:300]!r}")
            info = http.post_json(self.client, f"{BASE}/info", seleccion)
            stem = _stem(cuadro)
            files += [
                RawFile(f"{stem}.tabulado.json", meta.content, f"{BASE}/tabulado", params=meta_params,
                        content_type=meta.headers.get("content-type", "")),
                RawFile(f"{stem}.datos.json", datos.content, f"{BASE}/datatable",
                        params={"seleccion": seleccion},
                        content_type=datos.headers.get("content-type", "")),
                RawFile(f"{stem}.info.json", info.content, f"{BASE}/info", params={"file": cuadro},
                        content_type=info.headers.get("content-type", "")),
            ]
        return FetchResult(files=files, source_declared_version=None)
