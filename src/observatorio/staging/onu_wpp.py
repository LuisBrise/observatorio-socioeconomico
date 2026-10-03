"""Parser de las proyecciones probabilísticas de ONU WPP 2024 (archivos UN_PPP2024_Output_*.xlsx).

Cada archivo tiene una hoja por variante (Lower 95, Lower 80, Median, Upper 80, Upper 95) y una
columna por definición de edades. Se extrae solo la definición estándar declarada en
`COLUMNS` (p. ej., razón de dependencia con población en edad de trabajar de 15 a 64 años) y
solo el total por sexo. Código de serie: `{indicador}.{columna}.{variante}`.
Todas las cifras son proyecciones (obs_status F). Los valores vienen redondeados a enteros.
"""

from __future__ import annotations

from pathlib import Path

import fastexcel
import polars as pl

VARIANTS = {"Lower 95": "L95", "Lower 80": "L80", "Median": "MED", "Upper 80": "U80",
            "Upper 95": "U95"}
COLUMNS = {"TotalDepRatio": "15-64", "OldAgeDepRatio": "15-64", "ChildDepRatio": "15-64"}


def _load(book, sheet: str) -> pl.DataFrame:
    """Lee una hoja localizando la fila de encabezados (la que empieza con "Index")."""
    raw = book.load_sheet(sheet, header_row=None, dtypes="string").to_polars()
    first = raw.columns[0]
    idx = raw.with_row_index("_i").filter(pl.col(first) == "Index")["_i"]
    if idx.is_empty():
        raise ValueError(f"Hoja {sheet!r}: no se encontró la fila de encabezados ('Index')")
    i = int(idx[0])
    header = [str(v) for v in raw.row(i)]
    return raw.slice(i + 1).rename(dict(zip(raw.columns, header, strict=True)))


def _indicator_from_file(name: str) -> str | None:
    stem = name.removesuffix(".xlsx").removeprefix("UN_PPP2024_Output_").removeprefix("Annual_")
    return stem if stem in COLUMNS else None


def parse_onu_wpp(raw_dir: Path, dataset_id: str, vintage: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    from observatorio.staging import GEO_SCHEMA, STAGING_SCHEMA

    frames = []
    for path in sorted(raw_dir.glob("*.xlsx")):
        ind = _indicator_from_file(path.name)
        if ind is None:
            continue
        col = COLUMNS[ind]
        book = fastexcel.read_excel(path)
        for sheet, var in VARIANTS.items():
            df = _load(book, sheet)
            df = df.filter(pl.col("Sex") == "Total")
            code = pl.when(pl.col("ISO3 Alpha-code").fill_null("") != "").then(
                pl.col("ISO3 Alpha-code")).otherwise(pl.lit("LOC") + pl.col("Location code"))
            frames.append(df.select(
                pl.lit(dataset_id).alias("dataset_id"),
                pl.lit(vintage).alias("vintage_id"),
                pl.lit(f"{ind}.{col}.{var}").alias("source_series"),
                code.alias("source_geo"),
                pl.col("Region, subregion, country or area *").alias("source_geo_name"),
                pl.col("Year").alias("source_period"),
                pl.col(col).cast(pl.Float64, strict=False).alias("value"),
                pl.lit("F").alias("source_obs_status"),
            ))
    obs = pl.concat(frames).cast(STAGING_SCHEMA) if frames else pl.DataFrame(schema=STAGING_SCHEMA)
    geos = (obs.select("source_geo", pl.col("source_geo_name").alias("name")).unique()
            .with_columns(pl.col("source_geo").str.starts_with("LOC").alias("is_aggregate"))
            .cast(GEO_SCHEMA))
    return obs, geos
