"""Orquestación de las etapas del pipeline para un dataset.

ingest  → descarga y guarda un vintage crudo (si cambió)
process → staging + armonización + validación → processed (solo si no hay ERROR)
lock    → fija en catalog/vintages.lock.yaml el vintage que alimenta la publicación
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import yaml

from observatorio.catalog import Catalog
from observatorio.ingestion.base import RawStore, StoreResult
from observatorio.ingestion.connectors import get_connector
from observatorio.paths import Paths
from observatorio.staging import PARSERS
from observatorio.validation import checks
from observatorio.validation.report import write_report


class PipelineError(Exception):
    pass


# ---------------------------------------------------------------- ingesta

def ingest(paths: Paths, catalog: Catalog, dataset_id: str, connector=None) -> StoreResult:
    dataset = catalog.datasets[dataset_id]
    connector = connector or get_connector(dataset.conector)
    result = connector.fetch(dataset)
    return RawStore(paths.raw, paths.root).store(dataset, result, connector=dataset.conector)


# ------------------------------------------------------------ procesamiento

def processed_path(paths: Paths, dataset_id: str, vintage: str) -> Path:
    return paths.processed / "observations" / f"dataset={dataset_id}" / f"vintage={vintage}"


def read_lock(paths: Paths) -> dict:
    if not paths.lockfile.exists():
        return {}
    data = yaml.safe_load(paths.lockfile.read_text(encoding="utf-8")) or {}
    return data.get("datasets") or {}


def _read_meta(raw_dir: Path) -> dict[str, dict]:
    meta = {}
    for p in raw_dir.glob("*.meta.json"):
        payload = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(payload, list) and len(payload) > 1 and payload[1]:
            meta[p.name.removesuffix(".meta.json")] = payload[1][0]
    return meta


@dataclass
class ProcessResult:
    dataset_id: str
    vintage: str
    status: str
    report_dir: Path
    n_obs: int


def process(paths: Paths, catalog: Catalog, dataset_id: str, vintage: str | None = None,
            today=None) -> ProcessResult:
    dataset = catalog.datasets[dataset_id]
    store = RawStore(paths.raw, paths.root)
    vintage = vintage or store.latest(dataset.fuente, dataset_id)
    if vintage is None:
        raise PipelineError(f"{dataset_id}: no hay vintages crudos; ejecuta `obs ingest` primero")
    raw_dir = store.dataset_dir(dataset.fuente, dataset_id) / vintage
    if not raw_dir.is_dir():
        raise PipelineError(
            f"{dataset_id}: no existe el vintage crudo {vintage} en {raw_dir}. Si viene del lockfile, "
            "restaura el archivo crudo (scripts/raw_archive.sh restore) o vuelve a descargar.")

    # Staging
    obs_stg, geos = PARSERS[dataset_id](raw_dir, dataset_id, vintage)
    stg_dir = paths.staging / dataset.fuente / dataset_id
    stg_dir.mkdir(parents=True, exist_ok=True)
    obs_stg.write_parquet(stg_dir / f"{vintage}.parquet")

    # Armonización
    from observatorio.harmonize import harmonize

    obs, h_issues = harmonize(obs_stg, geos, dataset, catalog)
    results = [checks.CheckResult(i.check, i.severity, i.message, i.count) for i in h_issues]

    # Validación (C2 + C3)
    results += checks.check_schema(obs)
    results += checks.check_duplicates(obs)
    results += checks.check_ranges(obs, dataset, catalog)
    results += checks.check_future_dates(obs, today=today)
    results += checks.check_outliers(obs, dataset, catalog)

    locked = read_lock(paths).get(dataset_id)
    revisions = None
    if locked and locked["vintage"] != vintage:
        prev_dir = processed_path(paths, dataset_id, locked["vintage"])
        if prev_dir.exists():
            old = pl.read_parquet(prev_dir / "part-0.parquet")
            vr, revisions = checks.compare_vintages(obs, old, dataset.umbrales)
            results += vr
        prev_raw = store.dataset_dir(dataset.fuente, dataset_id) / locked["vintage"]
        if prev_raw.exists():  # el vintage fijado puede no estar disponible (p. ej., archivo vacío)
            results += checks.compare_metadata(_read_meta(raw_dir), _read_meta(prev_raw))

    report_dir = paths.validation / dataset_id / vintage
    summary = write_report(results, report_dir, {
        "dataset_id": dataset_id, "vintage_id": vintage,
        "compared_with": locked["vintage"] if locked else None,
        "validated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "n_obs": obs.height,
    })
    if summary["status"] != "error":
        out = processed_path(paths, dataset_id, vintage)
        out.mkdir(parents=True, exist_ok=True)
        obs.write_parquet(out / "part-0.parquet")
        if revisions is not None and revisions.height:
            revisions.write_parquet(out / "revisions.parquet")
    return ProcessResult(dataset_id, vintage, summary["status"], report_dir, obs.height)


# ------------------------------------------------------------------- lock

def lock(paths: Paths, catalog: Catalog, dataset_id: str, vintage: str) -> dict:
    dataset = catalog.datasets[dataset_id]
    if not (processed_path(paths, dataset_id, vintage) / "part-0.parquet").exists():
        raise PipelineError(f"{dataset_id}@{vintage}: no hay datos procesados válidos para fijar")
    report = json.loads((paths.validation / dataset_id / vintage / "report.json").read_text())
    manifest = RawStore(paths.raw, paths.root).manifest(dataset.fuente, dataset_id, vintage)
    entries = read_lock(paths)
    entries[dataset_id] = {
        "vintage": vintage,
        "content_sha256": manifest["content_sha256"],
        "retrieved_at": manifest["retrieved_at"],
        "source_declared_version": manifest.get("source_declared_version"),
        "validation_status": report["status"],
    }
    header = ("# Versión (vintage) de cada dataset que alimenta la publicación vigente.\n"
              "# Lo actualiza `obs lock`; su historial en git es el historial de datos del "
              "observatorio.\n")
    paths.lockfile.write_text(
        header + yaml.safe_dump({"datasets": dict(sorted(entries.items()))},
                                allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    return entries[dataset_id]


# --------------------------------------------------------- lectura vigente

def load_current(paths: Paths) -> pl.DataFrame:
    """Observaciones de los vintages fijados en el lockfile."""
    frames = []
    for dataset_id, entry in read_lock(paths).items():
        p = processed_path(paths, dataset_id, entry["vintage"]) / "part-0.parquet"
        if not p.exists():
            raise PipelineError(
                f"Falta {p}. Reconstruye con `obs process {dataset_id} --vintage {entry['vintage']}`"
            )
        frames.append(pl.read_parquet(p))
    if not frames:
        raise PipelineError("El lockfile está vacío: no hay datos publicados")
    return pl.concat(frames)


def indicator_values(obs: pl.DataFrame, catalog: Catalog, indicator_id: str) -> pl.DataFrame:
    """Valores de la serie principal (la primera listada) de un indicador no derivado."""
    ind = catalog.indicators[indicator_id]
    if not ind.series:
        raise PipelineError(f"{indicator_id} es derivado; usa su receta")
    return (obs.filter(pl.col("series_id") == ind.series[0])
            .select("geo_id", "period", "period_start", "value", "series_id", "vintage_id"))
