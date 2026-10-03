"""Registro de conectores disponibles (nombre → clase)."""

from __future__ import annotations

from observatorio.ingestion.base import Connector
from observatorio.ingestion.connectors.wb_wdi import WorldBankWDI

CONNECTORS: dict[str, type] = {
    WorldBankWDI.name: WorldBankWDI,
}


def get_connector(name: str, **kwargs) -> Connector:
    try:
        return CONNECTORS[name](**kwargs)
    except KeyError as exc:
        raise KeyError(f"Conector desconocido: {name!r}") from exc
