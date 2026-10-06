"""Lectura parcial de un ZIP remoto mediante peticiones HTTP Range.

Permite extraer miembros concretos de archivos de descarga masiva muy grandes (p. ej., los
882 MB de WID) sin descargarlos completos. Los bytes extraídos son los del miembro original
(se verifica su CRC con zipfile).
"""

from __future__ import annotations

import io
import zipfile

import httpx

from observatorio.ingestion import http


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, client: httpx.Client, url: str):
        self.client, self.url, self.pos = client, url, 0
        head = client.head(url, follow_redirects=True)
        head.raise_for_status()
        if head.headers.get("accept-ranges") != "bytes":
            raise ValueError(f"{url} no acepta peticiones Range")
        self.size = int(head.headers["content-length"])
        self.etag = head.headers.get("etag")
        self.last_modified = head.headers.get("last-modified")

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = max(0, base + offset)
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if self.pos >= self.size:
            return b""
        end = self.size - 1 if n is None or n < 0 else min(self.size - 1, self.pos + n - 1)
        resp = http.get(self.client, self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        if resp.status_code != 206:
            raise ValueError(f"Se esperaba 206 Partial Content y se recibió {resp.status_code}")
        self.pos += len(resp.content)
        return resp.content

    def readinto(self, b) -> int:
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)


def open_remote_zip(client: httpx.Client, url: str) -> tuple[zipfile.ZipFile, HTTPRangeFile]:
    f = HTTPRangeFile(client, url)
    return zipfile.ZipFile(io.BufferedReader(f, buffer_size=1 << 16)), f
