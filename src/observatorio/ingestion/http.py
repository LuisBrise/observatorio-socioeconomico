"""Cliente HTTP robusto: reintentos con espera exponencial y User-Agent identificable."""

from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from observatorio import __version__

USER_AGENT = (
    f"observatorio-socioeconomico/{__version__} "
    "(+https://github.com/LuisBrise/observatorio-socioeconomico)"
)


class TransientHTTPError(Exception):
    """Error que vale la pena reintentar (5xx, 429, red)."""


def make_client(timeout: float = 60.0) -> httpx.Client:
    return httpx.Client(
        timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )


@retry(
    retry=retry_if_exception_type(TransientHTTPError),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def get(client: httpx.Client, url: str, params: dict | None = None) -> httpx.Response:
    try:
        resp = client.get(url, params=params)
    except httpx.TransportError as exc:
        raise TransientHTTPError(str(exc)) from exc
    if resp.status_code == 429 or resp.status_code >= 500:
        raise TransientHTTPError(f"HTTP {resp.status_code} en {url}")
    resp.raise_for_status()
    return resp
