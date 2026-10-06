"""Registro de conectores disponibles (nombre → clase)."""

from __future__ import annotations

from observatorio.ingestion.base import Connector
from observatorio.ingestion.connectors.archivos import FileDownload
from observatorio.ingestion.connectors.cepal import CEPALSTAT
from observatorio.ingestion.connectors.fmi_weo import IMFWEO
from observatorio.ingestion.connectors.inegi_tabulados import INEGITabulados
from observatorio.ingestion.connectors.rnpdno import RNPDNO
from observatorio.ingestion.connectors.sesnsp import SESNSP
from observatorio.ingestion.connectors.wb_pip import WorldBankPIP
from observatorio.ingestion.connectors.wb_wdi import WorldBankWDI
from observatorio.ingestion.connectors.wid import WID

CONNECTORS: dict[str, type] = {
    WorldBankWDI.name: WorldBankWDI,
    IMFWEO.name: IMFWEO,
    FileDownload.name: FileDownload,
    WorldBankPIP.name: WorldBankPIP,
    WID.name: WID,
    CEPALSTAT.name: CEPALSTAT,
    INEGITabulados.name: INEGITabulados,
    RNPDNO.name: RNPDNO,
    SESNSP.name: SESNSP,
}


def get_connector(name: str, **kwargs) -> Connector:
    try:
        return CONNECTORS[name](**kwargs)
    except KeyError as exc:
        raise KeyError(f"Conector desconocido: {name!r}") from exc
