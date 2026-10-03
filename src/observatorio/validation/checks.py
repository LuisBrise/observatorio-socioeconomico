"""Controles de validación (docs/diseno/06-pipeline-y-validacion.md §7).

Cada control devuelve una lista de `CheckResult`. Los controles marcan; nunca corrigen
ni eliminan datos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

import pandera.polars as pa
import polars as pl

from observatorio.catalog import Catalog
from observatorio.catalog.models import Dataset

ERROR, WARN, INFO = "ERROR", "ADVERTENCIA", "INFO"
KEY = ["series_id", "geo_id", "period"]


@dataclass
class CheckResult:
    check: str
    severity: str
    message: str
    count: int = 0
    details: list[dict] = field(default_factory=list)


class ObservationModel(pa.DataFrameModel):
    series_id: str = pa.Field(nullable=False)
    geo_id: str = pa.Field(nullable=False)
    period: str = pa.Field(nullable=False)
    period_start: date = pa.Field(nullable=False)
    period_end: date = pa.Field(nullable=False)
    freq: str = pa.Field(isin=["A", "Q", "M", "W", "D"])
    value: float = pa.Field(nullable=False)
    obs_status: str = pa.Field(isin=["A", "P", "E", "F", "I", "B", "M"])
    vintage_id: str = pa.Field(nullable=False)

    class Config:
        strict = True


def check_schema(df: pl.DataFrame) -> list[CheckResult]:
    try:
        ObservationModel.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        return [CheckResult("esquema", ERROR, "El esquema de observaciones no es válido",
                            len(exc.failure_cases), [{"error": str(exc)[:2000]}])]
    return []


def check_duplicates(df: pl.DataFrame) -> list[CheckResult]:
    dup = df.group_by(KEY).len().filter(pl.col("len") > 1)
    if dup.height:
        return [CheckResult("duplicados", ERROR, "Claves (serie, geografía, periodo) repetidas",
                            dup.height, dup.head(20).to_dicts())]
    return []


def _series_indicator(dataset: Dataset) -> dict[str, str]:
    return {f"{dataset.id}:{s.codigo}": s.indicador for s in dataset.series}


def check_ranges(df: pl.DataFrame, dataset: Dataset, catalog: Catalog) -> list[CheckResult]:
    out = []
    for sid, ind_id in _series_indicator(dataset).items():
        rng = catalog.indicators[ind_id].rangos_validos
        is_bound = catalog.series_spec(sid).variante not in ("estimacion", "mediana")
        s = df.filter(pl.col("series_id") == sid)
        cond = pl.lit(False)
        if rng.min is not None:
            cond = cond | (pl.col("value") < rng.min)
        if rng.max is not None:
            cond = cond | (pl.col("value") > rng.max)
        bad = s.filter(cond)
        if bad.height and is_bound:
            # Límites de intervalos de predicción: las colas de un modelo pueden salir del rango
            # de valores plausibles sin ser un error de datos. Se informa, no se bloquea.
            out.append(CheckResult(
                "intervalos_extremos", INFO,
                f"{sid}: límites de intervalo fuera de [{rng.min}, {rng.max}] (colas del modelo)",
                bad.height, bad.select(KEY + ["value"]).head(20).to_dicts()))
        elif bad.height:
            out.append(CheckResult(
                "valores_imposibles", ERROR,
                f"{sid}: valores fuera del rango válido [{rng.min}, {rng.max}] de {ind_id}",
                bad.height, bad.select(KEY + ["value"]).head(20).to_dicts()))
    return out


def check_future_dates(df: pl.DataFrame, today: date | None = None) -> list[CheckResult]:
    today = today or date.today()
    bad = df.filter((pl.col("period_start") > today) & (pl.col("obs_status") != "F"))
    if bad.height:
        return [CheckResult("fechas_futuras", ERROR,
                            "Periodos futuros sin bandera de pronóstico", bad.height,
                            bad.select(KEY).head(20).to_dicts())]
    return []


def find_outliers(df: pl.DataFrame, dataset: Dataset, catalog: Catalog) -> pl.DataFrame:
    """Variaciones logarítmicas inusuales, por serie y geografía.

    Criterio (parámetros por indicador en el catálogo): |z robusto| > z (mediana y MAD de
    las variaciones de la propia serie) Y desviación absoluta > cambio_minimo. Solo series
    estrictamente positivas y con al menos 10 variaciones.
    """
    frames = []
    for sid, ind_id in _series_indicator(dataset).items():
        rule = catalog.indicators[ind_id].atipicos
        # Los pronósticos (F) no son datos observados: no se revisan como atípicos.
        pos = (df.filter((pl.col("series_id") == sid) & (pl.col("value") > 0)
                         & (pl.col("obs_status") != "F"))
               .sort(["geo_id", "period_start"]))
        ch = pos.with_columns(
            pl.col("value").shift(1).over("geo_id").alias("value_prev"),
            pl.col("value").log().diff().over("geo_id").alias("dlog"),
        ).filter(pl.col("dlog").is_not_null())
        st = ch.with_columns(pl.col("dlog").median().over("geo_id").alias("med")).with_columns(
            (pl.col("dlog") - pl.col("med")).abs().median().over("geo_id").alias("mad"),
            pl.len().over("geo_id").alias("n"),
        ).filter((pl.col("mad") > 0) & (pl.col("n") >= 10)).with_columns(
            ((pl.col("dlog") - pl.col("med")) / (1.4826 * pl.col("mad"))).alias("z"))
        frames.append(st.filter((pl.col("z").abs() > rule.z)
                                & ((pl.col("dlog") - pl.col("med")).abs() > rule.cambio_minimo)))
    if not frames:
        return pl.DataFrame()
    out = pl.concat(frames)
    return out.with_columns(((pl.col("dlog").exp() - 1) * 100).alias("cambio_pct")).select(
        KEY + ["value_prev", "value", "cambio_pct", "z"]).sort(pl.col("z").abs(), descending=True)


def check_outliers(df: pl.DataFrame, dataset: Dataset, catalog: Catalog) -> list[CheckResult]:
    """Marca atípicos para revisión humana; nunca los borra.

    Los ya revisados en catalog/revisiones/atipicos_{dataset}.yaml (valor_real o
    error_fuente) se reportan como INFO; los nuevos o pendientes, como ADVERTENCIA.
    """
    flagged = find_outliers(df, dataset, catalog)
    if flagged.is_empty():
        return []
    reviews = catalog.outlier_reviews

    ind_of = _series_indicator(dataset)
    siblings: dict[str, list[str]] = {}
    for ds in catalog.datasets.values():
        for spec in ds.series:
            siblings.setdefault(spec.indicador, []).append(f"{ds.id}:{spec.codigo}")

    def reviewed(row: dict) -> bool:
        r = reviews.get((row["series_id"], row["geo_id"], row["period"]))
        if r is not None:
            return r.resolucion != "pendiente"
        # Un "valor_real" describe un suceso, no una fuente: vale para otras series del mismo
        # indicador. Los "dudoso" NO se heredan (un dato dudoso en una fuente puede estar bien en otra).
        for sib in siblings.get(ind_of[row["series_id"]], []):
            r = reviews.get((sib, row["geo_id"], row["period"]))
            if r is not None and r.resolucion == "valor_real":
                return True
        return False

    rows = flagged.to_dicts()
    done = [r for r in rows if reviewed(r)]
    todo = [r for r in rows if not reviewed(r)]
    out = []
    if todo:
        out.append(CheckResult(
            "atipicos", WARN,
            "Variaciones inusuales sin revisar (revisar, no borrar): ejecuta "
            f"`obs atipicos {dataset.id}` para generar la lista de revisión", len(todo), todo))
    if done:
        n_doubt = sum(getattr(reviews.get((r["series_id"], r["geo_id"], r["period"])),
                              "resolucion", None) in ("dudoso", "ruptura_metodologica")
                      for r in done)
        out.append(CheckResult("atipicos_revisados", INFO,
                               f"Variaciones inusuales ya revisadas en el catálogo ({n_doubt} dudosas o "
                               "rupturas: "
                               "se conservan y se señalan en las gráficas que las usan)", len(done)))
    return out


def compare_vintages(
    new: pl.DataFrame, old: pl.DataFrame, thresholds: dict[str, float]
) -> tuple[list[CheckResult], pl.DataFrame]:
    """Revisiones, cambios de unidad y cobertura entre dos vintages."""
    results: list[CheckResult] = []
    joined = new.join(old.select(KEY + [pl.col("value").alias("value_old")]), on=KEY, how="inner")
    revisions = joined.with_columns(
        (pl.col("value") - pl.col("value_old")).alias("delta"),
        ((pl.col("value") / pl.col("value_old") - 1) * 100).alias("delta_pct"),
    ).filter(pl.col("delta") != 0)

    # Cambio de unidades: razón mediana cercana a una potencia de 10 distinta de 1.
    ratios = (joined.filter((pl.col("value_old") != 0) & (pl.col("value") != 0))
              .group_by("series_id")
              .agg((pl.col("value") / pl.col("value_old")).abs().median().alias("ratio")))
    for sid, ratio in ratios.iter_rows():
        k = round(math.log10(ratio)) if ratio > 0 else 0
        if k != 0 and abs(math.log10(ratio) - k) < 0.05:
            results.append(CheckResult("cambio_unidades", ERROR,
                                       f"{sid}: los valores cambiaron por un factor ~10^{k}",
                                       1, [{"series_id": sid, "ratio_mediana": ratio}]))

    warn_pct = thresholds.get("revision_advertencia_pct", 5.0)
    warn_share = thresholds.get("revision_advertencia_share", 0.25)
    for sid in new["series_id"].unique().sort().to_list():
        n_common = joined.filter(pl.col("series_id") == sid).height
        rev = revisions.filter(pl.col("series_id") == sid)
        if not n_common or not rev.height:
            continue
        big = rev.filter(pl.col("delta_pct").abs() > warn_pct)
        share = rev.height / n_common
        sev = WARN if (share > warn_share or big.height) else INFO
        results.append(CheckResult(
            "revisiones", sev,
            f"{sid}: {rev.height} de {n_common} observaciones revisadas ({share:.0%}); "
            f"{big.height} con cambio mayor a {warn_pct}%",
            rev.height,
            big.sort(pl.col("delta_pct").abs(), descending=True)
            .select(KEY + ["value_old", "value", "delta_pct"]).head(20).to_dicts()))

    drop_pct = thresholds.get("caida_cobertura_pct", 2.0)
    n_new = new.group_by("series_id").len().rename({"len": "n_new"})
    n_old = old.group_by("series_id").len().rename({"len": "n_old"})
    cov = n_old.join(n_new, on="series_id", how="left").with_columns(pl.col("n_new").fill_null(0))
    for sid, n_o, n_n in cov.select("series_id", "n_old", "n_new").iter_rows():
        if n_n == 0:
            results.append(CheckResult("cobertura", ERROR, f"{sid}: la serie desapareció", n_o))
        elif (n_o - n_n) / n_o * 100 > drop_pct:
            results.append(CheckResult("cobertura", WARN,
                                       f"{sid}: pasó de {n_o} a {n_n} observaciones", n_o - n_n))
    return results, revisions


def compare_metadata(new: dict[str, dict], old: dict[str, dict]) -> list[CheckResult]:
    """Cambios en el nombre o la definición publicados por la fuente."""
    out = []
    for code, meta in new.items():
        prev = old.get(code)
        if not prev:
            continue
        changed = [k for k in ("name", "sourceNote", "unit") if meta.get(k) != prev.get(k)]
        if changed:
            out.append(CheckResult(
                "cambio_metadatos", WARN,
                f"{code}: cambió {', '.join(changed)} según la fuente (¿cambio de definición?)",
                len(changed),
                [{k: {"antes": prev.get(k), "ahora": meta.get(k)} for k in changed}]))
    return out
