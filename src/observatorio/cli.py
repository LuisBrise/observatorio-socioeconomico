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


@app.command("atipicos")
def atipicos(dataset: str, vintage: str = typer.Option(None, help="Por defecto, el último")) -> None:
    """Agrega los atípicos sin revisar a catalog/revisiones/atipicos_{dataset}.yaml como 'pendiente'.

    Después, una persona cambia `resolucion` a `valor_real` o `error_fuente`, escribe la nota y
    su nombre. Los revisados dejan de generar advertencias.
    """
    from datetime import date

    import yaml

    from observatorio.ingestion.base import RawStore

    paths, cat = _ctx()
    ds = cat.datasets[dataset]
    vintage = vintage or RawStore(paths.raw, paths.root).latest(ds.fuente, dataset)
    report = json.loads((paths.validation / dataset / vintage / "report.json").read_text())
    todo = [d for r in report["results"] if r["check"] == "atipicos" for d in r["details"]]
    target = paths.catalog / "revisiones" / f"atipicos_{dataset}.yaml"
    target.parent.mkdir(exist_ok=True)
    existing = yaml.safe_load(target.read_text(encoding="utf-8")) if target.exists() else []
    existing = existing or []
    keys = {(e["serie"], e["geo"], e["periodo"]) for e in existing}
    new = []
    for d in sorted(todo, key=lambda d: (d["series_id"], d["geo_id"], d["period"])):
        key = (d["series_id"], d["geo_id"], d["period"])
        if key in keys:
            continue
        new.append({
            "serie": d["series_id"], "geo": d["geo_id"], "periodo": d["period"],
            "resolucion": "pendiente",
            "nota": (f"{cat.geo_name(d['geo_id'])}: {d['value_prev']:,.4g} → {d['value']:,.4g} "
                     f"({d['cambio_pct']:+.1f} %, z={d['z']:.0f})"),
            "revisado_por": "",
            "fecha": date.today(),
        })
    if new:
        header = ("# Revisión humana de atípicos (docs/diseno/06-pipeline-y-validacion.md §7).\n"
                  "# resolucion: valor_real | error_fuente | pendiente. Nunca se borran datos.\n")
        target.write_text(header + yaml.safe_dump(existing + new, allow_unicode=True,
                                                  sort_keys=False, width=110), encoding="utf-8")
    typer.echo(f"{len(new)} atípicos nuevos agregados como 'pendiente' a {target} "
               f"({len(todo) - len(new)} ya estaban listados).")


@app.command("comparar")
def comparar(indicador: str = typer.Argument(None, help="Por defecto, todos los indicadores")) -> None:
    """Compara las fuentes que miden un mismo indicador (datos fijados en el lockfile)."""
    from observatorio.pipeline import load_current
    from observatorio.validation.cross_source import compare_indicator
    from observatorio.validation.report import write_report

    paths, cat = _ctx()
    obs = load_current(paths)
    ids = [indicador] if indicador else [i for i, ind in cat.indicators.items() if ind.series]
    results = []
    for ind_id in ids:
        res, _ = compare_indicator(obs, cat, ind_id)
        results += res
    out = paths.validation / "_comparaciones"
    summary = write_report(results, out, {"dataset_id": "comparación entre fuentes",
                                          "vintage_id": "vigente"})
    typer.echo((out / "report.md").read_text(encoding="utf-8"))
    if summary["status"] == "advertencia":
        raise typer.Exit(3)


@app.command("rebuild")
def rebuild(omitir_faltantes: bool = typer.Option(
        False, help="Omitir (con aviso) los datasets cuyo vintage fijado no está en data/raw")) -> None:
    """Regenera processed/ a partir de los vintages crudos fijados en el lockfile."""
    from observatorio.ingestion.base import RawStore

    paths, cat = _ctx()
    store = RawStore(paths.raw, paths.root)
    for dataset, entry in read_lock(paths).items():
        raw_dir = store.dataset_dir(cat.datasets[dataset].fuente, dataset) / entry["vintage"]
        if omitir_faltantes and not raw_dir.exists():
            typer.secho(f"{dataset}@{entry['vintage']}: falta el vintage crudo; se omite", fg="yellow")
            continue
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
