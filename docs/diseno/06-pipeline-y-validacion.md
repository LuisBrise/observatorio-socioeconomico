# 06 · Pipeline de datos y validación

## 1. Flujo y compuertas de calidad

```text
SOURCE ─► INGESTION ─► RAW ─► STAGING ─► PROCESSED ─► ANALYTICAL ─► VIZ ─► SITE
              │          │        │            │             │          │
             C1         C1       C2           C3            C4         C5
```

| Compuerta | Momento | Qué verifica | Si falla |
|---|---|---|---|
| **C1** Archivo | Tras la descarga | Respuesta HTTP, tamaño, formato, hash, cambio respecto a la versión anterior | Reintento; si persiste, se conserva la última versión válida y se abre un *issue*. |
| **C2** Esquema | Tras el parseo | Columnas, tipos, claves únicas, periodos interpretables, códigos conocidos | El dataset no avanza. |
| **C3** Dominio | Tras la armonización | Rangos, valores imposibles, valores atípicos, revisiones, rupturas, cambios de unidad, cobertura, discrepancias con otras fuentes | ERROR detiene el dataset; ADVERTENCIA avanza con nota. |
| **C4** Derivación | Tras las transformaciones | Identidades contables, sumas de partes, coherencia de agregados, cobertura de agregados | ERROR detiene el indicador derivado. |
| **C5** Publicación | Antes del despliegue | Contrato del dataset de visualización, procedencia completa, licencia, tamaño | El sitio no se despliega con esa gráfica; las demás sí. |

**Principio de aislamiento:** una falla afecta solo al dataset o la gráfica involucrados. El sitio
nunca se cae entero por una fuente.

## 2. Zonas de datos

```text
data/
├── raw/{fuente}/{dataset}/{vintage}/     # bytes originales + _manifest.json  (INMUTABLE)
├── staging/{fuente}/{dataset}/{vintage}.parquet
├── processed/observations/dataset={id}/vintage={v}/part-0.parquet
├── analytical/
│   ├── indicators/indicator={id}/part-0.parquet
│   ├── aggregates/
│   └── panels/
├── validation/{run_id}/report.json · report.md
└── warehouse.duckdb                      # vistas; reconstruible
```

- `vintage` = marca de tiempo UTC de la consulta (`2026-10-03T120000Z`).
- Si el hash del archivo descargado es igual al de la versión anterior, no se crea una
  carpeta nueva: se registra en la bitácora de ingesta que "no hubo cambios".
- `raw/` se respalda en almacenamiento de objetos con **direccionamiento por hash**
  (la ruta del objeto es su SHA-256). El resto se regenera.

## 3. Ingesta

### Interfaz común de conectores

```python
class Connector(Protocol):
    source_id: str

    def list_datasets(self) -> list[DatasetRef]: ...
    def fetch(self, dataset: DatasetRef, previous: VintageManifest | None) -> FetchResult:
        """Descarga los bytes originales. No interpreta contenido.
        Usa peticiones condicionales (ETag / If-Modified-Since) cuando la fuente lo permite."""
```

### Manifiesto de cada versión (`_manifest.json`)

```json
{
  "source_id": "banxico",
  "dataset_id": "banxico_sie_tipo_cambio",
  "vintage": "2026-10-03T120000Z",
  "retrieved_at": "2026-10-03T12:00:04Z",
  "request": {"url": "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos",
              "params": {}, "auth": "env:BANXICO_TOKEN"},
  "response": {"status": 200, "etag": null, "last_modified": null,
               "content_type": "application/json"},
  "files": [{"name": "SF43718.json", "sha256": "9c1e…", "bytes": 482113}],
  "source_declared_version": null,
  "connector": {"name": "banxico", "version": "0.1.0", "git_sha": "3f2a…"},
  "previous_vintage": "2026-10-02T120000Z",
  "changed": true
}
```

### Buenas prácticas incorporadas

- Reintentos con espera exponencial; límites de tasa por fuente; un *User-Agent* identificable.
- Credenciales solo desde variables de entorno o secretos de CI, nunca en el repositorio.
- **Ingesta manual documentada** para fuentes sin API o con registro:
  `obs ingest-manual --dataset latinobarometro_2024 --file … --obtenido-de URL --nota "…"`.
  Genera el mismo manifiesto (con la persona responsable de la ingesta).

## 4. Staging: parseo literal

Un parser por dataset convierte el formato original en una tabla con columnas comunes,
**sin cambiar significado**: conserva los códigos, unidades y banderas de la fuente. Separar
este paso permite depurar errores de parseo sin mezclarlos con decisiones de armonización.

## 5. Armonización (`processed`)

| Paso | Qué hace | Control asociado |
|---|---|---|
| Geografía | Mapea los códigos de la fuente a `geo_id` mediante la tabla de equivalencias | Un código sin mapear es ERROR (nunca se descarta en silencio). |
| Unidades | Aplica multiplicadores (miles, millones), registra moneda y base de precios | Detección de saltos de potencias de 10. |
| Periodos | Normaliza a `period`, `period_start`, `period_end`, `freq` | Fechas imposibles o futuras sin bandera de pronóstico = ERROR. |
| Estatus | Traduce banderas de la fuente a códigos SDMX (`P`, `E`, `F`, `B`…) | Banderas desconocidas = ADVERTENCIA. |
| Versionado | Asigna `vintage_id` a cada observación | — |

## 6. Versiones y revisiones

- Cada observación conserva la versión de la que proviene. La vista `observations_current`
  toma, para cada dataset, la versión fijada en `catalog/vintages.lock.yaml`.
- La tabla `revisions` compara versiones consecutivas: qué periodos cambiaron, cuánto y en qué sentido.
- **Construcción "a fecha":** `obs build --as-of 2025-06-30` reconstruye el sitio usando solo
  las versiones disponibles en esa fecha. Sirve para auditar publicaciones pasadas y evaluar pronósticos en tiempo real.

## 7. Catálogo de controles de validación

| Problema | Método de detección | Severidad por defecto |
|---|---|---|
| **Valores faltantes** | Porcentaje de nulos por serie/país/periodo; huecos dentro de la serie; comparación con la cobertura de la versión anterior | ADVERTENCIA (ERROR si cae la cobertura de un indicador de fase 1) |
| **Valores imposibles** | Rangos declarados en la ficha del indicador (tasas en [0, 100], población > 0, porcentajes que suman ~100) | ERROR |
| **Duplicados** | Unicidad de (`series_id`, `geo_id`, `period`, `vintage_id`) | ERROR |
| **Problemas de fechas** | Periodos imposibles, frecuencia inconsistente, fechas futuras sin bandera de pronóstico | ERROR |
| **Valores atípicos** | Puntaje z robusto (mediana y MAD) sobre niveles y sobre variaciones, por serie; nunca se eliminan automáticamente | ADVERTENCIA → revisión humana |
| **Cambios de unidades** | Razón entre versiones o entre periodos adyacentes cercana a 10³ o 10⁶; cambio en el campo de unidad declarado | ERROR |
| **Revisiones históricas** | Comparación entre versiones: porcentaje de valores revisados, magnitud y periodos afectados; umbrales por dataset | INFO; ADVERTENCIA si supera el umbral |
| **Rupturas de serie** | (a) Rupturas conocidas declaradas en el catálogo → anotación automática; (b) detección exploratoria de cambios de nivel o de tendencia | INFO / ADVERTENCIA |
| **Cambios de metodología o definición** | Cambio en los metadatos declarados por la fuente (nombre, definición, nota metodológica, unidad); el conector guarda los metadatos en cada versión y los compara | ADVERTENCIA → revisión humana |
| **Cambios de fronteras o población** | Entidades con vigencia temporal (p. ej., Sudán del Sur desde 2011, municipios nuevos en México); cambios de denominador al cambiar la revisión de población | ADVERTENCIA |
| **Inconsistencias internas** | Identidades (exportaciones − importaciones = balanza), suma de entidades = total nacional, componentes = total | ERROR si la diferencia supera la tolerancia |
| **Inconsistencias entre fuentes** | Para cada concepto con varias series: diferencia relativa por país y periodo; comparación con la discrepancia documentada | ADVERTENCIA si es nueva o cambia de magnitud |
| **Datos desactualizados** | Fecha del último periodo vs frecuencia y rezago esperados | ADVERTENCIA |

### Política para valores atípicos

1. El sistema los **marca**, nunca los borra.
2. Una persona revisa y anota la resolución en `catalog/revisiones/atipicos_{dataset}.yaml`
   (`obs atipicos {dataset}` agrega los nuevos como `pendiente`):
   - `valor_real`: extremo pero real (coincide con un suceso documentado); se conserva con nota.
     Se hereda a otras series del mismo indicador, porque describe el suceso, no la fuente.
   - `dudoso`: sin explicación documentada; se conserva, se advierte en las gráficas y se consulta.
   - `ruptura_metodologica`: el cambio refleja territorio, censo o método, no un cambio real
     (p. ej., Sudán 2011 por la independencia de Sudán del Sur); se advierte en las gráficas.
   - `error_fuente`: error confirmado con referencia; se corrige con una transformación documentada.
   Los pronósticos (F) no se revisan como atípicos.
3. Las resoluciones quedan versionadas en git.

### Protocolo de discrepancias entre fuentes

Cuando dos fuentes difieren más allá de la tolerancia, **no se elige una arbitrariamente**:

1. **Alinear:** ¿mismo concepto, unidad, cobertura, periodo y momento de registro?
2. **Cuantificar:** diferencia absoluta y relativa en el tiempo; ¿es estable o cambia?
3. **Diagnosticar la causa:** definición · cobertura · método · momento de registro ·
   revisión · error de una de las fuentes. Consultar la documentación metodológica de ambas.
4. **Documentar** en `catalog/discrepancies/DIS-xxx.yaml` (causa, evidencia, fecha, autor).
5. **Decidir la presentación** y justificarla: mostrar ambas, mostrar el rango o usar una
   como principal con la otra como referencia. La decisión depende de la pregunta, no del resultado.

```yaml
id: DIS-001
concepto: seg.violencia_letal.homicidio
series: [inegi_defunciones:homicidio, sesnsp_idefc:homicidio_doloso_victimas]
diferencia_observada: "INEGI > SESNSP en la mayoría de los años desde 2015 (a cuantificar)"
causas_documentadas:
  - tipo: fuente_del_registro
    descripcion: Certificado de defunción (sector salud y registro civil) vs carpeta de investigación (fiscalías).
  - tipo: momento_de_registro
    descripcion: Año de ocurrencia o de registro vs fecha de inicio de la carpeta.
  - tipo: clasificacion
    descripcion: Criterios distintos de homicidio intencional; posibles reclasificaciones a categorías vecinas (a investigar).
presentacion: ambas_series_con_nota
estado: abierta          # abierta | explicada | sin_explicar
```

## 8. Transformaciones

- Cada transformación es una función **pura**, con nombre y versión, probada con casos
  conocidos y con pruebas basadas en propiedades (hypothesis).
- Las recetas de los indicadores derivados se declaran en el catálogo; el código solo las ejecuta.
- Cambiar el comportamiento de una transformación crea una versión nueva (`@2`); la anterior se conserva.

| Transformación | Uso |
|---|---|
| `per_capita@1`, `tasa_por_poblacion@1` | Normalizar por población (con la serie de población declarada). |
| `deflactar@1` | Convertir valores nominales a reales (deflactor y año base declarados). |
| `var_anual@1`, `var_periodo@1`, `tcac@1` | Crecimiento interanual, entre periodos y tasa de crecimiento anual compuesta. |
| `media_movil@1` | Suavizar series ruidosas (ventana declarada). |
| `indice_base@1` | Índice base 100 en un periodo elegido por regla. |
| `empalme_razon@1` | Empalmar series de bases distintas usando un periodo de traslape. |
| `percentil_historico@1`, `z_robusto@1` | Ubicar el dato actual en la distribución histórica de la propia serie. |
| `agregado_regional@1` | Agregados con ponderación declarada (simple, población, PIB) y **cobertura mínima** (p. ej., 80 % de la población del grupo); por debajo, el valor es nulo con bandera. |
| `distribucion_grupo@1` | Mediana, cuartiles y posición de un país dentro de un grupo. |

## 9. Datasets de visualización

**Contrato:** cada gráfica recibe una tabla mínima (solo las columnas que dibuja) y un
archivo `provenance.json`:

```json
{
  "chart_id": "d1/ingreso-relativo",
  "question": "¿Cómo ha evolucionado el PIB per cápita de México respecto al de EE.UU.?",
  "built_at": "2026-10-03T12:10:00Z",
  "git_sha": "3f2a…",
  "indicators": ["eco.actividad.pib_pc.relativo_eeuu"],
  "series": [{"id": "wb_wdi:NY.GDP.PCAP.PP.KD", "vintage": "2026-09-30T060000Z"}],
  "transformations": [{"name": "razon@1", "params": {"num": "MEX", "den": "USA"}}],
  "caveats": ["PPA 2021; los niveles cambiaron con la adopción de la ronda ICP 2021."],
  "license": "CC BY 4.0 (Banco Mundial)",
  "validation": {"warnings": 0, "notes": ["Ruptura conocida: ninguna"]}
}
```

Las salidas se verifican con pruebas de *snapshot*: si un cambio de código altera una gráfica
sin que cambien los datos, la prueba lo detecta.

## 10. Reproducibilidad

| Elemento | Cómo se garantiza |
|---|---|
| Código | git; cada salida registra el `git_sha`. |
| Entorno | `uv.lock` para Python; versión fijada de Quarto y de las librerías JS. |
| Datos de entrada | Archivo crudo direccionado por hash + `catalog/vintages.lock.yaml` en git. |
| Proceso | Etapas deterministas; mismas entradas → mismas salidas (verificado en CI). |
| Historia | `obs build --as-of FECHA` reconstruye cualquier publicación pasada. |

## 11. Errores y bitácoras

- Bitácoras estructuradas (JSON) con un `run_id` por ejecución.
- Cada etapa devuelve un estado por dataset: `ok`, `sin_cambios`, `advertencia`, `error`.
- El reporte de cada ejecución se guarda en `data/validation/{run_id}/` y su resumen
  alimenta la página "Estado de los datos" del sitio.
