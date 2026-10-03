"""Registro de transformaciones con nombre y versión.

Cambiar el comportamiento de una transformación exige registrar una versión nueva
(`nombre@2`) y conservar la anterior: así las recetas del catálogo son reproducibles.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

TRANSFORMS: dict[str, Callable] = {}


def transform(name: str, version: int) -> Callable[[Callable], Callable]:
    key = f"{name}@{version}"

    def deco(fn: Callable) -> Callable:
        if key in TRANSFORMS:
            raise ValueError(f"Transformación duplicada: {key}")
        TRANSFORMS[key] = fn
        fn.transform_id = key  # type: ignore[attr-defined]
        return fn

    return deco


def get_transform(key: str) -> Callable:
    try:
        return TRANSFORMS[key]
    except KeyError as exc:
        raise KeyError(f"Transformación no registrada: {key!r}") from exc


@dataclass
class LineageStep:
    transform: str
    params: dict
    inputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"transform": self.transform, "params": self.params, "inputs": self.inputs}
