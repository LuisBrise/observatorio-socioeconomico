"""Rutas del proyecto. `OBS_DATA_DIR` permite mover los datos fuera del repositorio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path
    data: Path

    @property
    def catalog(self) -> Path:
        return self.root / "catalog"

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def staging(self) -> Path:
        return self.data / "staging"

    @property
    def processed(self) -> Path:
        return self.data / "processed"

    @property
    def analytical(self) -> Path:
        return self.data / "analytical"

    @property
    def validation(self) -> Path:
        return self.data / "validation"

    @property
    def site_data(self) -> Path:
        return self.root / "site" / "data"

    @property
    def lockfile(self) -> Path:
        return self.catalog / "vintages.lock.yaml"


def default_paths() -> Paths:
    root = Path(os.environ.get("OBS_ROOT", PROJECT_ROOT))
    data = Path(os.environ.get("OBS_DATA_DIR", root / "data"))
    return Paths(root=root, data=data)
