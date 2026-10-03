"""Escritura de datasets de visualización con su archivo de procedencia.

Contrato (docs/diseno/06-pipeline-y-validacion.md §9): cada gráfica recibe
`site/data/{chart_id}/data.json` (solo lo que dibuja), un CSV por tabla para descarga y
`provenance.json` con la cadena completa hasta los archivos crudos.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from observatorio.catalog import Catalog
from observatorio.ingestion.base import RawStore, _git_sha
from observatorio.paths import Paths
from observatorio.pipeline import read_lock


@dataclass
class ChartSpec:
    chart_id: str
    question: str
    indicators: list[str]
    caveats: list[str]
    transformations: list[dict] = field(default_factory=list)
    groups: dict[str, list[str]] = field(default_factory=dict)


def _series_provenance(paths: Paths, catalog: Catalog, indicator_ids: list[str]) -> list[dict]:
    lock = read_lock(paths)
    store = RawStore(paths.raw, paths.root)
    out, seen = [], set()
    for ind_id in indicator_ids:
        ind = catalog.indicators[ind_id]
        series = list(ind.series)
        if ind.derivacion:
            base = ind.derivacion.parametros.get("indicador")
            if base:
                series += catalog.indicators[str(base)].series
        for sid in series:
            if sid in seen:
                continue
            seen.add(sid)
            dataset_id = sid.split(":", 1)[0]
            ds = catalog.datasets[dataset_id]
            entry = lock[dataset_id]
            manifest = store.manifest(ds.fuente, dataset_id, entry["vintage"])
            out.append({
                "series_id": sid,
                "dataset": ds.nombre,
                "source": catalog.sources[ds.fuente].nombre,
                "vintage": entry["vintage"],
                "retrieved_at": manifest["retrieved_at"],
                "source_declared_version": manifest.get("source_declared_version"),
                "raw_content_sha256": manifest["content_sha256"],
                "raw_files": [{"name": f["name"], "sha256": f["sha256"], "url": f["url"]}
                              for f in manifest["files"] if sid.split(":", 1)[1] in f["name"]],
                "license": ds.licencia.nombre,
                "license_url": str(ds.licencia.url),
                "validation_status": entry.get("validation_status"),
                "known_breaks": [b.model_dump() for b in ds.rupturas_conocidas if b.serie == sid],
            })
    return out


def write_chart(paths: Paths, catalog: Catalog, spec: ChartSpec,
                tables: dict[str, pl.DataFrame], extra: dict | None = None) -> Path:
    out = paths.site_data / spec.chart_id
    out.mkdir(parents=True, exist_ok=True)
    payload = {name: df.with_columns(pl.col(pl.Date).cast(pl.String)).to_dicts()
               for name, df in tables.items()}
    if extra:
        payload.update(extra)
    (out / "data.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    for name, df in tables.items():
        df.write_csv(out / f"{name}.csv")
    series = _series_provenance(paths, catalog, spec.indicators)
    provenance = {
        "chart_id": spec.chart_id,
        "question": spec.question,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": _git_sha(paths.root),
        "indicators": [{"id": i, "nombre": catalog.indicators[i].nombre,
                        "unidad": catalog.indicators[i].unidad,
                        "derivacion": (catalog.indicators[i].derivacion.model_dump()
                                       if catalog.indicators[i].derivacion else None)}
                       for i in spec.indicators],
        "series": series,
        "transformations": spec.transformations,
        "groups": spec.groups,
        "caveats": spec.caveats,
        "licenses": sorted({s["license"] for s in series}),
    }
    missing = [k for k in ("series", "caveats") if not provenance[k]]
    if missing:  # Compuerta C5: sin procedencia completa no se publica.
        raise ValueError(f"{spec.chart_id}: procedencia incompleta ({missing})")
    (out / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
