"""Análisis reproducible: ¿por qué difieren WDI (Banco Mundial) y WEO (FMI) en el PIB per cápita PPA?

Uso: uv run python analyses/2026-10-03_wdi_vs_weo.py
Lee los vintages fijados en catalog/vintages.lock.yaml y escribe
analyses/resultados/2026-10-03_wdi_vs_weo.md. Sustenta DIS-001 y DIS-002.

Identidad usada: pc = PIB / población. Si pc_fmi/pc_bm = (PIB_fmi/PIB_bm) · (pob_bm/pob_fmi),
la diferencia per cápita se descompone en una parte del denominador (población) y una del PIB total.
Es una descomposición contable, no una explicación causal de por qué cada fuente estima distinto.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from observatorio.catalog import load_catalog
from observatorio.paths import default_paths
from observatorio.pipeline import load_current, read_lock

paths = default_paths()
cat = load_catalog(paths.catalog)
obs = load_current(paths).filter(pl.col("obs_status") != "F", ~pl.col("geo_id").str.starts_with("G."))


def s(sid: str, name: str) -> pl.DataFrame:
    return obs.filter(pl.col("series_id") == sid).select("geo_id", "period", pl.col("value").alias(name))


d = (s("wb_wdi:NY.GDP.PCAP.PP.KD", "pc_bm").join(s("fmi_weo:NGDPRPPPPC", "pc_fmi"), on=["geo_id", "period"])
     .join(s("wb_wdi:SP.POP.TOTL", "pob_bm"), on=["geo_id", "period"], how="left")
     .join(s("fmi_weo:LP", "pob_fmi"), on=["geo_id", "period"], how="left")
     .with_columns(anio=pl.col("period").cast(pl.Int32),
                   dif_pc=pl.col("pc_fmi") / pl.col("pc_bm") - 1,
                   dif_pob=pl.col("pob_bm") / pl.col("pob_fmi") - 1)
     .with_columns(dif_pib=(1 + pl.col("dif_pc")) / (1 + pl.col("dif_pob")) - 1))

alc = cat.groups["G.ALC_CEPAL33"].miembros
pct = lambda c: (pl.col(c) * 100).round(2)  # noqa: E731


def md(df: pl.DataFrame) -> str:
    cols = df.columns
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in df.iter_rows()]
    return "\n".join(rows)


por_distancia = (d.with_columns(distancia=((pl.col("anio") - 2021).abs() // 5 * 5))
                 .group_by("distancia").agg(pl.len().alias("n"),
                                            (pl.col("dif_pc").abs().median() * 100).round(2)
                                            .alias("mediana_abs_%")).sort("distancia"))
componentes = d.select((pl.col(c).abs().median() * 100).round(2).alias(f"{c}_mediana_abs_%")
                       for c in ("dif_pc", "dif_pob", "dif_pib"))
peores = (d.filter(pl.col("anio") == 2021).with_columns(pl.col("dif_pc").abs().alias("_a"))
          .sort("_a", descending=True).head(12)
          .select("geo_id", pct("dif_pc").alias("dif_pc_%"), pct("dif_pob").alias("dif_pob_%"),
                  pct("dif_pib").alias("dif_pib_%")))
mex = (d.filter(pl.col("geo_id") == "MEX").sort("anio")
       .select("period", pl.col("pc_bm").round(0), pl.col("pc_fmi").round(0),
               pct("dif_pc").alias("dif_pc_%"), pct("dif_pob").alias("dif_pob_%")))
alc_tab = (d.filter(pl.col("geo_id").is_in(alc)).group_by("geo_id")
           .agg((pl.col("dif_pc").abs().median() * 100).round(1).alias("mediana_abs_pc_%"),
                (pl.col("dif_pc").abs().max() * 100).round(1).alias("max_abs_pc_%"),
                (pl.col("dif_pob").abs().median() * 100).round(1).alias("mediana_abs_pob_%"))
           .sort("mediana_abs_pc_%", descending=True))
# Último año observado en ambas fuentes para México.
ultimo = d.filter(pl.col("geo_id") == "MEX")["anio"].max()
rangos = []
for col in ("pc_bm", "pc_fmi"):
    r = d.filter(pl.col("geo_id").is_in(alc), pl.col("anio") == ultimo).with_columns(
        pl.col(col).rank(descending=True).alias("rk"))
    rangos.append((col, int(r.filter(pl.col("geo_id") == "MEX")["rk"][0]), r.height))

lock = read_lock(paths)
out = Path(__file__).parent / "resultados" / "2026-10-03_wdi_vs_weo.md"
out.parent.mkdir(exist_ok=True)
out.write_text(f"""# WDI vs WEO: PIB per cápita PPA (precios constantes, ICP 2021)

Generado por `analyses/2026-10-03_wdi_vs_weo.py` con los vintages
`wb_wdi@{lock['wb_wdi']['vintage']}` y `fmi_weo@{lock['fmi_weo']['vintage']}`.
Solo datos observados (se excluyen proyecciones del FMI) y solo países.

## 1. ¿Crece la diferencia al alejarse del año de referencia de la PPA (2021)?

[ANÁLISIS] Poco: la mediana pasa de ~1.6 % cerca de 2021 a ~3 % hace 30 años. La extrapolación
de la PPA no es la causa principal.

{md(por_distancia)}

## 2. Descomposición contable: ¿población o PIB total?

{md(componentes)}

Países con mayor diferencia en 2021 (año de referencia de la PPA):

{md(peores)}

[ANÁLISIS] En algunos países toda la diferencia viene del denominador (dif_pib ≈ 0: las fuentes usan
poblaciones distintas); en otros, del PIB total (cuentas nacionales o revisiones distintas).

## 3. México

{md(mex)}

[ANÁLISIS] Para México las fuentes coinciden: la diferencia del PIB per cápita es menor a 1 % en
todos los años. La población del FMI es ~1 % mayor que la de ONU WPP en los años recientes.

Posición de México en ALC en {ultimo}: {"; ".join(f"{c}: {r} de {n}" for c, r, n in rangos)}.

## 4. América Latina y el Caribe

{md(alc_tab)}
""", encoding="utf-8")
print(f"Escrito {out}")
