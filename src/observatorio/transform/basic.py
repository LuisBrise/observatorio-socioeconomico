"""Transformaciones básicas. Todas son funciones puras sobre DataFrames de Polars.

Formato de entrada "valores de indicador": columnas `geo_id`, `period`, `period_start`, `value`.
"""

from __future__ import annotations

import polars as pl

from observatorio.transform.registry import transform

VALUE_COLS = ["geo_id", "period", "period_start", "value"]


@transform("razon_geo", 1)
def razon_geo(values: pl.DataFrame, geo_denominador: str, escala: float = 1.0) -> pl.DataFrame:
    """Valor de cada geografía dividido entre el de `geo_denominador` en el mismo periodo."""
    den = values.filter(pl.col("geo_id") == geo_denominador).select(
        "period", pl.col("value").alias("_den"))
    return (values.join(den, on="period", how="inner")
            .filter(pl.col("_den") != 0)
            .with_columns((pl.col("value") / pl.col("_den") * escala).alias("value"))
            .select(VALUE_COLS))


@transform("per_capita", 1)
def per_capita(values: pl.DataFrame, poblacion: pl.DataFrame, escala: float = 1.0) -> pl.DataFrame:
    """Divide entre la población del mismo país y periodo (solo donde ambas existen)."""
    pop = poblacion.select("geo_id", "period", pl.col("value").alias("_pop"))
    return (values.join(pop, on=["geo_id", "period"], how="inner")
            .filter(pl.col("_pop") > 0)
            .with_columns((pl.col("value") / pl.col("_pop") * escala).alias("value"))
            .select(VALUE_COLS))


@transform("var_anual", 1)
def var_anual(values: pl.DataFrame) -> pl.DataFrame:
    """Variación porcentual respecto al periodo anterior (series anuales, sin huecos)."""
    s = values.sort("geo_id", "period_start").with_columns(
        pl.col("value").shift(1).over("geo_id").alias("_prev"),
        pl.col("period_start").dt.year().shift(1).over("geo_id").alias("_prev_year"),
    )
    return (s.filter(pl.col("_prev_year") == pl.col("period_start").dt.year() - 1)
            .filter(pl.col("_prev") != 0)
            .with_columns(((pl.col("value") / pl.col("_prev") - 1) * 100).alias("value"))
            .select(VALUE_COLS))


@transform("indice_base", 1)
def indice_base(values: pl.DataFrame, periodo_base: str) -> pl.DataFrame:
    """Índice = 100 en `periodo_base` para cada geografía que tenga dato en ese periodo."""
    base = values.filter(pl.col("period") == periodo_base).select(
        "geo_id", pl.col("value").alias("_base"))
    return (values.join(base, on="geo_id", how="inner")
            .filter(pl.col("_base") != 0)
            .with_columns((pl.col("value") / pl.col("_base") * 100).alias("value"))
            .select(VALUE_COLS))


@transform("distribucion_grupo", 1)
def distribucion_grupo(
    values: pl.DataFrame,
    miembros: list[str],
    poblacion: pl.DataFrame | None = None,
    cobertura_minima: float = 0.8,
) -> pl.DataFrame:
    """Distribución de un indicador dentro de un grupo, por periodo.

    Devuelve n, mediana, cuartiles, mínimo y máximo (no ponderados: cada país cuenta
    igual) y la cobertura: proporción de miembros con dato y, si se da `poblacion`,
    proporción de la población del grupo cubierta. Si la cobertura de población (o de
    miembros, sin población) es menor que `cobertura_minima`, los estadísticos se anulan
    y `cobertura_suficiente` es falso: preferimos un hueco a un agregado engañoso.
    """
    v = values.filter(pl.col("geo_id").is_in(miembros))
    stats = v.group_by("period", "period_start").agg(
        pl.len().alias("n"),
        pl.col("value").median().alias("mediana"),
        pl.col("value").quantile(0.25, interpolation="linear").alias("p25"),
        pl.col("value").quantile(0.75, interpolation="linear").alias("p75"),
        pl.col("value").min().alias("minimo"),
        pl.col("value").max().alias("maximo"),
        pl.col("geo_id").alias("_geos"),
    ).with_columns((pl.col("n") / len(miembros)).alias("cobertura_miembros"))

    if poblacion is not None:
        pop = poblacion.filter(pl.col("geo_id").is_in(miembros)).select(
            "geo_id", "period", pl.col("value").alias("_pop"))
        total = pop.group_by("period").agg(pl.col("_pop").sum().alias("_pop_total"))
        covered = (v.select("geo_id", "period").join(pop, on=["geo_id", "period"], how="inner")
                   .group_by("period").agg(pl.col("_pop").sum().alias("_pop_cov")))
        stats = (stats.join(total, on="period", how="left").join(covered, on="period", how="left")
                 .with_columns((pl.col("_pop_cov") / pl.col("_pop_total"))
                               .alias("cobertura_poblacion"))
                 .drop("_pop_total", "_pop_cov"))
        cov_col = "cobertura_poblacion"
    else:
        stats = stats.with_columns(pl.lit(None, dtype=pl.Float64).alias("cobertura_poblacion"))
        cov_col = "cobertura_miembros"

    ok = pl.col(cov_col).fill_null(0) >= cobertura_minima
    stat_cols = ["mediana", "p25", "p75", "minimo", "maximo"]
    return (stats.with_columns(ok.alias("cobertura_suficiente"))
            .with_columns([pl.when(ok).then(pl.col(c)).otherwise(None).alias(c)
                           for c in stat_cols])
            .drop("_geos")
            .sort("period_start"))


@transform("suma", 1)
def suma(*partes: pl.DataFrame) -> pl.DataFrame:
    """Suma de varias series por geografía y periodo (solo donde todas tienen dato)."""
    out = partes[0].select("geo_id", "period", "period_start", pl.col("value").alias("_v0"))
    for i, p in enumerate(partes[1:], start=1):
        out = out.join(p.select("geo_id", "period", pl.col("value").alias(f"_v{i}")),
                       on=["geo_id", "period"], how="inner")
    cols = [f"_v{i}" for i in range(len(partes))]
    return out.with_columns(pl.sum_horizontal(cols).alias("value")).select(VALUE_COLS)
