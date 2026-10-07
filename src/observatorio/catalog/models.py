"""Esquemas del catálogo.

El catálogo (YAML en `catalog/`) es la fuente de verdad sobre qué medimos y cómo.
Estos modelos validan su estructura; `load.py` valida además las referencias cruzadas.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccessMethod(StrEnum):
    API = "api"
    BULK = "descarga_masiva"
    MANUAL = "manual"


class Redistribution(StrEnum):
    ALLOWED_WITH_ATTRIBUTION = "permitida_con_atribucion"
    NON_COMMERCIAL_WITH_ATTRIBUTION = "no_comercial_con_atribucion"
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
    """Ruptura de serie conocida. Si declara `geo`, la armonización marca esa observación como B
    (inicio de un nuevo tramo comparable) aunque la fuente no lo indique."""

    serie: str
    fecha: str
    descripcion: str
    geo: str | None = None
    evidencia: str | None = None  # referencia que documenta la ruptura


class SeriesSpec(_Base):
    """Serie que un dataset debe traer, con su código original en la fuente."""

    codigo: str
    indicador: str
    unidad: str
    multiplicador: float = 1.0
    # Productor original de la cifra (no quien la redistribuye). Dos series con el mismo
    # origen NO son fuentes independientes: compararlas no verifica nada.
    origen: str
    # Variante de la serie: una estimación (dato) o un componente de una proyección
    # probabilística. Los límites de un intervalo nunca se tratan como datos ni como otra fuente.
    variante: Literal["estimacion", "mediana", "inferior_80", "superior_80",
                      "inferior_95", "superior_95"] = "estimacion"


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
    # Para conectores de descarga de archivos: URLs de los archivos originales.
    archivos: list[str] = Field(default_factory=list)
    umbrales: dict[str, float] = Field(default_factory=dict)
    # Tabulados con muchas combinaciones (edad × sexo…): usar solo las series declaradas; las
    # demás quedan en el archivo crudo y se reportan como INFO (no como error).
    solo_series_declaradas: bool = False
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
    """Límites de lo IMPOSIBLE (no de lo inusual).

    Un valor fuera de rango es un error de datos con certeza (población negativa, esperanza
    de vida mayor a 100). Lo extremo pero posible (p. ej., la esperanza de vida en Camboya
    en 1977) lo detecta el control de atípicos y lo revisa una persona.
    """

    min: float | None = None
    max: float | None = None


class OutlierRule(_Base):
    """Parámetros del control de atípicos para un indicador.

    Se marca una variación logarítmica si |z robusto| > `z` Y su desviación respecto a la
    mediana de la serie supera `cambio_minimo` (proporción, 0.15 ≈ 15 %). El segundo
    criterio evita marcar movimientos pequeños en series muy suaves (estimaciones modeladas).
    """

    z: float = 6.0
    cambio_minimo: float = 0.10
    # Se ignoran variaciones cuando ambos valores (anterior y actual) están por debajo de este piso:
    # los cambios relativos sobre bases casi nulas (p. ej., pobreza de 0.1 % a 0.3 %) no son informativos.
    piso: float = 0.0


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
    atipicos: OutlierRule = OutlierRule()
    # Diferencia relativa entre fuentes a partir de la cual se exige una explicación documentada.
    tolerancia_entre_fuentes: float = 0.05
    notas_interpretacion: str = ""
    preguntas: list[str] = Field(default_factory=list)
    fecha_alta: date


class OutlierResolution(StrEnum):
    REAL = "valor_real"            # extremo pero real; se conserva con nota
    SOURCE_ERROR = "error_fuente"  # error confirmado (con referencia); se corrige con transformación
    BREAK = "ruptura_metodologica"  # cambio de territorio, censo o método: no es un cambio real
    DOUBTFUL = "dudoso"            # sin explicación documentada; se conserva, se señala y se verifica
    PENDING = "pendiente"          # aún sin revisar


class OutlierReview(_Base):
    """Revisión humana de un valor marcado como atípico."""

    serie: str
    geo: str
    periodo: str
    resolucion: OutlierResolution
    nota: str
    revisado_por: str
    fecha: date


class DiscrepancyCause(_Base):
    tipo: str  # definicion | cobertura | metodo | momento_de_registro | revision | ppa | error | otra
    descripcion: str


class Discrepancy(_Base):
    """Diferencia documentada entre fuentes (docs/diseno/06-pipeline-y-validacion.md §7)."""

    id: str
    indicador: str
    series: list[str]
    diferencia_observada: str
    causas_documentadas: list[DiscrepancyCause]
    presentacion: str  # ambas_series_con_nota | rango | principal_con_referencia
    estado: str  # abierta | explicada | sin_explicar
    fecha: date


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
