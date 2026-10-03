"""Esquemas del catálogo.

El catálogo (YAML en `catalog/`) es la fuente de verdad sobre qué medimos y cómo.
Estos modelos validan su estructura; `load.py` valida además las referencias cruzadas.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccessMethod(StrEnum):
    API = "api"
    BULK = "descarga_masiva"
    MANUAL = "manual"


class Redistribution(StrEnum):
    ALLOWED_WITH_ATTRIBUTION = "permitida_con_atribucion"
    AGGREGATES_ONLY = "solo_agregados"
    NOT_ALLOWED = "no_permitida"


class MeasurementType(StrEnum):
    ADMINISTRATIVE = "administrativo"
    SURVEY = "encuesta"
    NATIONAL_ACCOUNTS = "cuentas_nacionales"
    EXPERT_INDEX = "indice_expertos"
    EVENT_CODED = "eventos_codificados"
    MODELLED = "estimacion_modelada"
    PERCEPTION = "percepcion"


class ChainPosition(StrEnum):
    CONTEXT = "contexto"
    INPUT = "insumo"
    PROCESS = "proceso"
    OUTCOME = "resultado"
    PERCEPTION = "percepcion"


class Pace(StrEnum):
    STRUCTURAL = "estructural"
    INTERMEDIATE = "intermedio"
    CYCLICAL = "coyuntural"


class NormativeDirection(StrEnum):
    HIGHER_BETTER = "mas_es_mejor"
    LOWER_BETTER = "menos_es_mejor"
    NEUTRAL = "neutral"
    CONTESTED = "en_disputa"


class Evaluation(_Base):
    """Ficha de evaluación cualitativa de una fuente (no es un puntaje)."""

    mandato: str
    metodologia: str
    revisiones: str
    continuidad: str
    independencia: str
    primaria_o_compiladora: str


class Source(_Base):
    id: str
    nombre: str
    tipo: str
    url: HttpUrl
    evaluacion: Evaluation
    fecha_alta: date


class Access(_Base):
    metodo: AccessMethod
    endpoint: str | None = None
    credenciales: str = "ninguna"  # o "env:NOMBRE_VARIABLE"
    formato: str


class License(_Base):
    nombre: str
    url: HttpUrl
    redistribucion: Redistribution


class KnownBreak(_Base):
    serie: str
    fecha: str
    descripcion: str


class SeriesSpec(_Base):
    """Serie que un dataset debe traer, con su código original en la fuente."""

    codigo: str
    indicador: str
    unidad: str
    multiplicador: float = 1.0


class Dataset(_Base):
    id: str
    nombre: str
    fuente: str
    conector: str
    url: HttpUrl
    acceso: Access
    licencia: License
    cobertura: dict[str, str]
    frecuencia: str
    rezago_tipico_dias: int
    calendario: str
    metodologia: HttpUrl
    revisiones: str
    limitaciones: str
    rupturas_conocidas: list[KnownBreak] = Field(default_factory=list)
    series: list[SeriesSpec]
    umbrales: dict[str, float] = Field(default_factory=dict)
    fecha_alta: date


class Facets(_Base):
    tipo_medicion: MeasurementType
    cadena: ChainPosition
    ritmo: Pace
    direccion_normativa: NormativeDirection
    cobertura: list[str]


class Derivation(_Base):
    receta: str  # nombre@version de una transformación registrada
    parametros: dict[str, object] = Field(default_factory=dict)


class ValidRange(_Base):
    min: float | None = None
    max: float | None = None


class Indicator(_Base):
    id: str
    nombre: str
    concepto: str
    definicion: str
    unidad: str
    facetas: Facets
    series: list[str] = Field(default_factory=list)
    derivacion: Derivation | None = None
    rangos_validos: ValidRange = ValidRange()
    notas_interpretacion: str = ""
    preguntas: list[str] = Field(default_factory=list)
    fecha_alta: date


class GroupRule(_Base):
    """Regla para resolver la composición de un grupo a partir de datos."""

    universo: str
    indicador: str
    minimo: float
    anio_referencia: int


class Group(_Base):
    id: str
    nombre: str
    descripcion: str
    tipo: str  # comparacion | contraste | regional | socios
    miembros: list[str] = Field(default_factory=list)
    regla: GroupRule | None = None
    nota: str = ""
    version: int = 1


class Event(_Base):
    id: str
    fecha_inicio: str
    fecha_fin: str | None = None
    geo: list[str]
    tipo: str
    titulo: str
    descripcion: str
    fuentes: list[str]
    criterio: str


class Concept(_Base):
    id: str
    nombre: str


class Subdimension(_Base):
    id: str
    nombre: str
    conceptos: list[Concept] = Field(default_factory=list)


class Dimension(_Base):
    id: str
    nombre: str
    subdimensiones: list[Subdimension] = Field(default_factory=list)
