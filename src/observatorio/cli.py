"""CLI del observatorio: `obs --help`."""

from __future__ import annotations

import json

import typer

from observatorio.catalog import CatalogError, load_catalog
from observatorio.paths import default_paths
from observatorio.pipeline import PipelineError, ingest, lock, process, read_lock

app = typer.Typer(help="Observatorio socioeconómico: pipeline de datos.", no_args_is_help=True)


def _load_dotenv(path) -> None:
    """Carga variables de `.env` (KEY=VALUE) sin sobrescribir las ya definidas."""
    if not path.exists():
        return
    import os

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _ctx():
    paths = default_paths()
    _load_dotenv(paths.root / ".env")
    try:
        catalog = load_catalog(paths.catalog)
    except CatalogError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(2) from exc
    return paths, catalog


@app.command("catalog-check")
def catalog_check() -> None:
    """Valida la estructura y las referencias del catálogo."""
    _, cat = _ctx()
    typer.echo(f"Catálogo válido: {len(cat.sources)} fuentes, {len(cat.datasets)} datasets, "
               f"{len(cat.indicators)} indicadores, {len(cat.groups)} grupos, "
               f"{len(cat.events)} eventos, {len(cat.geographies)} geografías.")


@app.command("ingest")
def ingest_cmd(dataset: str) -> None:
    """Descarga un dataset y guarda un vintage crudo si cambió."""
    paths, cat = _ctx()
    res = ingest(paths, cat, dataset)
    typer.echo(f"{dataset}: {'nuevo vintage ' if res.changed else 'sin cambios, vintage '}"
               f"{res.vintage}")


@app.command("process")
def process_cmd(dataset: str, vintage: str = typer.Option(None, help="Por defecto, el último")) -> None:
    """Staging + armonización + validación de un vintage."""
    paths, cat = _ctx()
    try:
        res = process(paths, cat, dataset, vintage)
    except PipelineError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from exc
    typer.echo((res.report_dir / "report.md").read_text(encoding="utf-8"))
    if res.status == "error":
        raise typer.Exit(1)


@app.command("lock")
def lock_cmd(dataset: str, vintage: str = typer.Option(None, help="Por defecto, el último")) -> None:
    """Fija el vintage que alimenta la publicación (catalog/vintages.lock.yaml)."""
    paths, cat = _ctx()
    from observatorio.ingestion.base import RawStore

    ds = cat.datasets[dataset]
    vintage = vintage or RawStore(paths.raw, paths.root).latest(ds.fuente, dataset)
    try:
        entry = lock(paths, cat, dataset, vintage)
    except PipelineError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{dataset} fijado en {entry['vintage']} ({entry['validation_status']})")


@app.command("build-viz")
def build_viz(dashboard: str = typer.Argument("d1")) -> None:
    """Construye los datasets de visualización de un dashboard."""
    from observatorio.viz_data import BUILDERS

    paths, cat = _ctx()
    for chart in BUILDERS[dashboard](paths, cat):
        typer.echo(f"✓ {chart}")


@app.command("run")
def run(dataset: str, auto_lock: bool = typer.Option(
        True, help="Fijar automáticamente si la validación no tiene advertencias")) -> None:
    """Ingesta + proceso (+ lock si la validación está limpia)."""
    paths, cat = _ctx()
    res = ingest(paths, cat, dataset)
    typer.echo(f"ingesta: {'nuevo' if res.changed else 'sin cambios'} {res.vintage}")
    pr = process(paths, cat, dataset, res.vintage)
    typer.echo(f"validación: {pr.status} ({pr.report_dir / 'report.md'})")
    if pr.status == "error":
        raise typer.Exit(1)
    current = read_lock(paths).get(dataset, {}).get("vintage")
    if current == pr.vintage:
        typer.echo("lock: sin cambios")
    elif (pr.status == "ok" and auto_lock) or current is None:
        lock(paths, cat, dataset, pr.vintage)
        typer.echo(f"lock: {dataset} → {pr.vintage}")
    else:
        typer.echo("lock: pendiente de revisión humana (hay advertencias). Revisa el reporte y "
                   f"ejecuta `obs lock {dataset} --vintage {pr.vintage}`")


@app.command("rebuild")
def rebuild() -> None:
    """Regenera processed/ a partir de los vintages crudos fijados en el lockfile."""
    paths, cat = _ctx()
    for dataset, entry in read_lock(paths).items():
        res = process(paths, cat, dataset, entry["vintage"])
        typer.echo(f"{dataset}@{entry['vintage']}: {res.status}")
        if res.status == "error":
            raise typer.Exit(1)


@app.command("status")
def status() -> None:
    """Vintages fijados y estado de validación."""
    paths, _ = _ctx()
    typer.echo(json.dumps(read_lock(paths), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
