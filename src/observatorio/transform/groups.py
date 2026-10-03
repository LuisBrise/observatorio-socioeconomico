"""Resolución de grupos de comparación (lista explícita o regla basada en datos)."""

from __future__ import annotations

import polars as pl

from observatorio.catalog import Catalog


def resolve_group(catalog: Catalog, group_id: str, indicator_values: dict[str, pl.DataFrame]) -> list[str]:
    """Devuelve la lista de geografías del grupo.

    `indicator_values` mapea id de indicador → valores (necesario para grupos con regla).
    """
    g = catalog.groups[group_id]
    if g.regla is None:
        members: list[str] = []
        for m in g.miembros:
            members.extend(resolve_group(catalog, m, indicator_values) if m in catalog.groups
                           else [m])
        return sorted(set(members))
    r = g.regla
    universe = resolve_group(catalog, r.universo, indicator_values)
    vals = indicator_values.get(r.indicador)
    if vals is None:
        raise KeyError(f"Grupo {group_id}: faltan valores de {r.indicador} para aplicar la regla")
    ref = vals.filter((pl.col("period") == str(r.anio_referencia))
                      & pl.col("geo_id").is_in(universe)
                      & (pl.col("value") > r.minimo))
    return sorted(ref["geo_id"].to_list())
