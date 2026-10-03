"""Carga y validación del catálogo (estructura + referencias cruzadas)."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from observatorio.catalog.models import (
    Dataset,
    Dimension,
    Discrepancy,
    Event,
    Group,
    Indicator,
    OutlierReview,
    Source,
)

T = TypeVar("T", bound=BaseModel)


class CatalogError(Exception):
    """El catálogo tiene errores de estructura o de referencias."""


@dataclass
class Geography:
    geo_id: str
    nombre_es: str
    nombre_en: str
    tipo: str  # pais | agregado
    valido_desde: str = ""
    valido_hasta: str = ""


@dataclass
class Catalog:
    root: Path
    sources: dict[str, Source] = field(default_factory=dict)
    datasets: dict[str, Dataset] = field(default_factory=dict)
    indicators: dict[str, Indicator] = field(default_factory=dict)
    groups: dict[str, Group] = field(default_factory=dict)
    events: dict[str, Event] = field(default_factory=dict)
    dimensions: list[Dimension] = field(default_factory=list)
    geographies: dict[str, Geography] = field(default_factory=dict)
    discrepancies: dict[str, Discrepancy] = field(default_factory=dict)
    # Equivalencias de códigos geográficos por dataset: {dataset: {código_fuente: geo_id}}
    geo_crosswalk: dict[str, dict[str, str]] = field(default_factory=dict)
    outlier_reviews: dict[tuple[str, str, str], OutlierReview] = field(default_factory=dict)

    @property
    def concept_ids(self) -> set[str]:
        return {
            c.id for d in self.dimensions for s in d.subdimensiones for c in s.conceptos
        }

    def series_ids(self) -> set[str]:
        return {f"{d.id}:{s.codigo}" for d in self.datasets.values() for s in d.series}

    def series_spec(self, series_id: str):
        dataset_id, code = series_id.split(":", 1)
        return next(s for s in self.datasets[dataset_id].series if s.codigo == code)

    def geo_name(self, geo_id: str) -> str:
        g = self.geographies.get(geo_id)
        return g.nombre_es if g else geo_id


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_dir(directory: Path, model: type[T], errors: list[str], pattern: str = "*.yaml") -> dict[str, T]:
    items: dict[str, T] = {}
    if not directory.exists():
        return items
    for path in sorted(directory.glob(pattern)):
        raw = _read_yaml(path)
        docs = raw if isinstance(raw, list) else [raw]
        for doc in docs:
            try:
                obj = model.model_validate(doc)
            except ValidationError as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            obj_id = obj.id  # type: ignore[attr-defined]
            if obj_id in items:
                errors.append(f"{path.name}: id duplicado {obj_id!r}")
            items[obj_id] = obj
    return items


def _load_geographies(directory: Path) -> dict[str, Geography]:
    geos: dict[str, Geography] = {}
    for path in sorted(directory.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                geos[row["geo_id"]] = Geography(**row)
    return geos


def load_catalog(root: Path) -> Catalog:
    errors: list[str] = []
    cat = Catalog(root=root)
    cat.sources = _load_dir(root / "sources", Source, errors)
    cat.datasets = _load_dir(root / "datasets", Dataset, errors)
    cat.indicators = _load_dir(root / "indicators", Indicator, errors)
    cat.groups = _load_dir(root / "geographies", Group, errors, pattern="grupos*.yaml")
    cat.events = _load_dir(root / "events", Event, errors)
    cat.geographies = _load_geographies(root / "geographies")
    cat.discrepancies = _load_dir(root / "discrepancies", Discrepancy, errors)
    xwalk = root / "geographies" / "equivalencias.yaml"
    if xwalk.exists():
        cat.geo_crosswalk = _read_yaml(xwalk) or {}
        for ds_id, mapping in cat.geo_crosswalk.items():
            for code, geo in mapping.items():
                if geo not in cat.geographies:
                    errors.append(f"equivalencias.yaml: {ds_id}:{code} → geografía desconocida {geo!r}")
    for path in sorted((root / "revisiones").glob("atipicos_*.yaml")):
        for doc in _read_yaml(path) or []:
            try:
                r = OutlierReview.model_validate(doc)
            except ValidationError as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            cat.outlier_reviews[(r.serie, r.geo, r.periodo)] = r

    concepts_path = root / "concepts.yaml"
    if concepts_path.exists():
        raw = _read_yaml(concepts_path) or []
        try:
            cat.dimensions = [Dimension.model_validate(d) for d in raw]  # type: ignore[union-attr]
        except ValidationError as exc:
            errors.append(f"concepts.yaml: {exc}")

    errors.extend(_check_references(cat))
    if errors:
        raise CatalogError("Errores en el catálogo:\n- " + "\n- ".join(errors))
    return cat


def _check_references(cat: Catalog) -> list[str]:
    errors: list[str] = []
    series = cat.series_ids()
    concepts = cat.concept_ids
    group_ids = set(cat.groups)

    for d in cat.datasets.values():
        if d.fuente not in cat.sources:
            errors.append(f"dataset {d.id}: fuente desconocida {d.fuente!r}")
        for s in d.series:
            if s.indicador not in cat.indicators:
                errors.append(f"dataset {d.id}: serie {s.codigo} apunta a indicador desconocido")

    for ind in cat.indicators.values():
        if ind.concepto not in concepts:
            errors.append(f"indicador {ind.id}: concepto desconocido {ind.concepto!r}")
        for sid in ind.series:
            if sid not in series:
                errors.append(f"indicador {ind.id}: serie desconocida {sid!r}")
        if not ind.series and ind.derivacion is None:
            errors.append(f"indicador {ind.id}: no tiene series ni receta de derivación")

    for g in cat.groups.values():
        for m in g.miembros:
            if m not in cat.geographies and m not in group_ids:
                errors.append(f"grupo {g.id}: miembro desconocido {m!r}")
        if g.regla:
            if g.regla.universo not in group_ids:
                errors.append(f"grupo {g.id}: universo desconocido {g.regla.universo!r}")
            if g.regla.indicador not in cat.indicators:
                errors.append(f"grupo {g.id}: indicador de la regla desconocido")
        if not g.miembros and not g.regla:
            errors.append(f"grupo {g.id}: necesita miembros o una regla")

    for dis in cat.discrepancies.values():
        if dis.indicador not in cat.indicators:
            errors.append(f"discrepancia {dis.id}: indicador desconocido {dis.indicador!r}")
        for sid in dis.series:
            if sid not in series:
                errors.append(f"discrepancia {dis.id}: serie desconocida {sid!r}")

    for e in cat.events.values():
        for geo in e.geo:
            if geo not in cat.geographies and geo not in group_ids:
                errors.append(f"evento {e.id}: geografía desconocida {geo!r}")
    return errors
