"""Conector de los datos abiertos de incidencia delictiva del SESNSP.

La página de gob.mx enlaza los archivos (ZIP con CSV) alojados en OneDrive/SharePoint del SESNSP.
Los enlaces cambian cuando el archivo se actualiza, así que no se guardan en el catálogo: cada
entrada de `dataset.archivos` es una expresión regular sobre el TEXTO del enlace (p. ej.,
"2015 - 2025 (Fuero Común - Víctimas). Incidencia delictiva estatal").

Descarga de SharePoint sin cuenta: abrir el enlace compartido (asigna una cookie de invitado)
y repetirlo con `download=1`. Se guardan la página de gob.mx (para trazar qué enlace se usó) y el
ZIP original sin modificar.
"""

from __future__ import annotations

import html
import re
import unicodedata

import httpx

from observatorio.catalog.models import Dataset
from observatorio.ingestion import http
from observatorio.ingestion.base import FetchResult, RawFile

PAGINA = "https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva"
_LINK = re.compile(r'<a [^>]*href="(https://[^"]*sharepoint\.com/[^"]+)"[^>]*>(.*?)</a>', re.S)


def _norm(text: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip()


def find_links(page: str, patron: str) -> list[tuple[str, str]]:
    rx = re.compile(patron, re.I)
    return [(html.unescape(url), _norm(txt)) for url, txt in _LINK.findall(page) if rx.search(_norm(txt))]


class SESNSP:
    name = "sesnsp"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or http.make_client(timeout=300)

    def _download(self, url: str) -> httpx.Response:
        self.client.cookies.clear()
        http.get(self.client, url)  # cookie de invitado
        sep = "&" if "?" in url else "?"
        resp = http.get(self.client, f"{url}{sep}download=1")
        if "zip" not in resp.headers.get("content-type", "") and not resp.content.startswith(b"PK"):
            raise ValueError(f"SESNSP: la descarga no es un ZIP ({resp.headers.get('content-type')})")
        return resp

    def fetch(self, dataset: Dataset) -> FetchResult:
        page = http.get(self.client, PAGINA)
        files = [RawFile("pagina_datos_abiertos.html", page.content, PAGINA,
                         content_type=page.headers.get("content-type", ""))]
        for i, patron in enumerate(dataset.archivos):
            links = find_links(page.text, patron)
            if len(links) != 1:
                raise ValueError(f"SESNSP: el patrón {patron!r} encontró {len(links)} enlaces: {links}")
            url, texto = links[0]
            resp = self._download(url)
            files.append(RawFile(f"sesnsp_{i}.zip", resp.content, url,
                                 params={"texto_del_enlace": texto, "patron": patron},
                                 content_type=resp.headers.get("content-type", "")))
        return FetchResult(files=files, source_declared_version=None)
