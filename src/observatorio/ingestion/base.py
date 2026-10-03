"""Interfaz de conectores y almacén de datos crudos.

Reglas:
- Un conector descarga bytes y no interpreta contenido.
- Cada descarga distinta se guarda como un vintage nuevo e inmutable:
  data/raw/{fuente}/{dataset}/{vintage}/ + _manifest.json
- Si el contenido es idéntico al del último vintage, no se crea uno nuevo.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from observatorio import __version__
from observatorio.catalog.models import Dataset

MANIFEST = "_manifest.json"


@dataclass
class RawFile:
    name: str
    content: bytes
    url: str
    params: dict = field(default_factory=dict)
    content_type: str = ""


@dataclass
class FetchResult:
    files: list[RawFile]
    source_declared_version: str | None = None


class Connector(Protocol):
    name: str

    def fetch(self, dataset: Dataset) -> FetchResult: ...


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def vintage_id(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H%M%SZ")


def _git_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


def content_hash(files: list[RawFile]) -> str:
    """Hash del conjunto de archivos (independiente del orden de descarga)."""
    h = hashlib.sha256()
    for f in sorted(files, key=lambda f: f.name):
        h.update(f.name.encode())
        h.update(hashlib.sha256(f.content).digest())
    return h.hexdigest()


@dataclass
class StoreResult:
    vintage: str
    path: Path
    changed: bool


class RawStore:
    def __init__(self, raw_root: Path, repo_root: Path):
        self.raw_root = raw_root
        self.repo_root = repo_root

    def dataset_dir(self, source_id: str, dataset_id: str) -> Path:
        return self.raw_root / source_id / dataset_id

    def vintages(self, source_id: str, dataset_id: str) -> list[str]:
        d = self.dataset_dir(source_id, dataset_id)
        if not d.exists():
            return []
        return sorted(p.name for p in d.iterdir() if (p / MANIFEST).exists())

    def latest(self, source_id: str, dataset_id: str) -> str | None:
        v = self.vintages(source_id, dataset_id)
        return v[-1] if v else None

    def manifest(self, source_id: str, dataset_id: str, vintage: str) -> dict:
        path = self.dataset_dir(source_id, dataset_id) / vintage / MANIFEST
        return json.loads(path.read_text(encoding="utf-8"))

    def store(
        self, dataset: Dataset, result: FetchResult, connector: str, now: datetime | None = None
    ) -> StoreResult:
        if not result.files:
            raise ValueError(f"{dataset.id}: la descarga no produjo archivos")
        now = now or utc_now()
        digest = content_hash(result.files)
        previous = self.latest(dataset.fuente, dataset.id)
        if previous:
            prev_manifest = self.manifest(dataset.fuente, dataset.id, previous)
            if prev_manifest["content_sha256"] == digest:
                return StoreResult(previous, self.dataset_dir(dataset.fuente, dataset.id) / previous,
                                   changed=False)

        base_vid = vid = vintage_id(now)
        target = self.dataset_dir(dataset.fuente, dataset.id) / vid
        n = 0
        while target.exists():  # dos descargas distintas en el mismo segundo: nunca sobrescribir
            n += 1
            vid = f"{base_vid}-{n}"
            target = target.with_name(vid)
        tmp = target.with_name(vid + ".partial")
        tmp.mkdir(parents=True, exist_ok=False)
        entries = []
        for f in result.files:
            (tmp / f.name).write_bytes(f.content)
            entries.append(
                {
                    "name": f.name,
                    "sha256": hashlib.sha256(f.content).hexdigest(),
                    "bytes": len(f.content),
                    "url": f.url,
                    "params": f.params,
                    "content_type": f.content_type,
                }
            )
        manifest = {
            "source_id": dataset.fuente,
            "dataset_id": dataset.id,
            "vintage": vid,
            "retrieved_at": now.isoformat().replace("+00:00", "Z"),
            "content_sha256": digest,
            "files": entries,
            "source_declared_version": result.source_declared_version,
            "license": dataset.licencia.model_dump(mode="json"),
            "connector": {"name": connector, "version": __version__,
                          "git_sha": _git_sha(self.repo_root)},
            "previous_vintage": previous,
        }
        (tmp / MANIFEST).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.rename(target)  # publicación atómica del vintage
        return StoreResult(vid, target, changed=True)
