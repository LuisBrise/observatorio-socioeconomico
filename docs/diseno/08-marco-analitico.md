# 08 · Marco analítico: métodos, comparaciones y prospectiva

## 1. Principio

Usamos la técnica más simple que responde la pregunta. Una técnica sofisticada se justifica
solo si cambia lo que podemos concluir. Cada método del sistema tiene una nota que explica
cuándo es apropiado y cuáles son sus límites.

## 2. Técnicas de análisis temporal

| Técnica | Cuándo es apropiada | Limitaciones |
|---|---|---|
| **Tasa de crecimiento** (log-diferencia, TCAC) | Comparar ritmos entre series o periodos de distinta longitud. | Sensible a los años de inicio y fin; la TCAC oculta la trayectoria intermedia. |
| **Variación interanual** | Series mensuales y trimestrales con estacionalidad. | Efectos base: un mal año previo infla la variación siguiente. |
| **Medias móviles** | Series ruidosas (homicidios mensuales por estado). | Retrasan la detección de cambios; la ventana es una decisión. |
| **Índices base 100** | Comparar trayectorias de series con niveles distintos. | El año base cambia la lectura visual; se elige por regla. |
| **Percentiles históricos** | "¿Qué tan inusual es el dato actual para esta serie?" | Dependen de la ventana histórica; no dicen si el nivel es bueno o malo. |
| **Puntajes z (robustos)** | Comparar la magnitud de desviaciones entre indicadores distintos. | Suponen cierta estabilidad de la distribución; con rupturas, engañan. |
| **Cambios acumulados** | Responder "¿cuánto cambió desde el evento X?". | Muy sensibles a la elección del punto de partida. |
| **Descomposición tendencia–ciclo** (STL; filtro de Hamilton para series anuales) | Separar lo estructural de lo coyuntural. | El filtro Hodrick-Prescott tiene problemas conocidos (Hamilton, 2018), sobre todo al final de la muestra, que es justo "el presente". |
| **Quiebres estructurales** (Bai–Perron, detección de cambios) | Exploración: ¿hubo cambios de nivel o de tendencia? | Exploratorio, no confirmatorio; poca potencia con series cortas; un quiebre estadístico no identifica su causa. |
| **Pre/post evento y series de tiempo interrumpidas** | Describir qué cambió alrededor de un evento. | Confusores, anticipación, eventos simultáneos, reversión a la media. Descriptivo salvo un diseño creíble. |
| **Control sintético** (fase 3) | Estimar un contrafactual de un país a partir de una combinación de otros. | Requiere buen ajuste previo y donantes no afectados por el evento; los resultados pueden ser sensibles a la especificación. |
| **Correlaciones** | Explorar covariación. | Espurias con tendencias: se usan también diferencias o desviaciones de tendencia; Spearman ante valores atípicos; nunca implican causalidad. |
| **Descomposiciones contables** | Explicar *mecánicamente* un cambio (p. ej., PIB per cápita = productividad × tasa de empleo × proporción en edad de trabajar). | Son identidades: dicen "dónde" ocurrió el cambio, no "por qué". |
| **Convergencia (β y σ)** | ¿Se acercan los países entre sí, o México a EE.UU.? | Sensible a la muestra de países y al periodo. |
| **Análisis de sensibilidad** | Siempre que una conclusión dependa de una decisión (fuente, ventana, ponderación, grupo de comparación). | — Es obligatorio para los titulares de los dashboards. |

## 3. Comparaciones

### Reglas

1. **Cada comparación declara qué significa**: unidad, PPA o tipo de cambio de mercado,
   precios constantes o corrientes, denominador de población, definición del grupo y cobertura.
   El sitio genera esta nota automáticamente desde los metadatos ("Qué significa esta comparación").
2. **México dentro de la distribución**, no contra un promedio: mediana, rango intercuartil,
   posición (percentil) y países individuales visibles.
3. **Normalizaciones adecuadas**: per cápita, PPA para niveles de vida, estandarización por
   edad para mortalidad y precios reales para salarios.
4. **Mismo periodo y misma fuente** para todos los países comparados; si no es posible, se indica.

### Grupos de comparación (definidos por regla, versionados)

| Grupo | Regla | Nota |
|---|---|---|
| `G.ALC_CEPAL33` | Los 33 países de América Latina y el Caribe miembros de CEPAL | Grupo regional por defecto. |
| `G.ALC_GRANDES` | Países de ALC con más de 10 millones de habitantes en el año de referencia | Evita que los promedios simples estén dominados por economías pequeñas del Caribe. |
| `G.PARES_ESTRUCTURALES` | Economías de ingreso medio-alto (clasificación del Banco Mundial en el año de referencia) con más de 30 millones de habitantes | La lista resultante se fija y versiona; **comprobación de robustez** con "vecinos más cercanos" según PIB per cápita PPA, población, apertura comercial y estructura de edad. |
| `G.OCDE` | Composición vigente en cada año y, como alternativa, composición fija actual | La membresía cambió (p. ej., Colombia en 2020, Costa Rica en 2021). |
| `G.SOCIOS` | EE.UU., Canadá, China, Unión Europea | Para inserción internacional. |

La composición de cada grupo se publica junto a la gráfica. Cambiar un grupo requiere una
decisión documentada (no se ajusta para "mejorar" una comparación).

## 4. ¿Estructural o coyuntural?

Se responde con evidencia, en tres pasos:

1. **Ritmo esperado** (declarado en la ficha): demografía y productividad son lentas; la inflación, rápida.
2. **Descomposición** tendencia–ciclo de la serie.
3. **Persistencia multi-ventana:** se compara la posición de México con sus grupos de
   comparación en ventanas de 1, 5, 10, 20 y 30 años. Una brecha que persiste en todas las
   ventanas se clasifica como *persistente*; una que aparece solo en la más reciente, como *reciente*.

La clasificación es una etiqueta **analítica** (no un dato) y se muestra con su criterio.

## 5. "¿Qué está cambiando rápido?" (detector de cambios)

Para cada indicador:

1. Se calcula el cambio en una ventana (p. ej., 12 meses o 3 años).
2. Se compara con la distribución histórica de cambios de la misma longitud en esa serie
   (excluyendo periodos con rupturas conocidas).
3. Se obtiene un valor p empírico y se corrige por comparaciones múltiples (Benjamini–Hochberg)
   sobre todos los indicadores evaluados.
4. Se exige una longitud mínima de la serie.

La salida es una lista ordenada de **cambios inusuales respecto a la historia de cada serie**,
no de "alarmas". Un cambio inusual no es necesariamente bueno ni malo.

## 6. Eventos y análogos históricos

- **Línea de tiempo de eventos** con criterios de inclusión escritos antes de poblarla.
- **Estudios de evento entre países:** trayectoria de un indicador alrededor de eventos del
  mismo tipo (p. ej., crisis bancarias según Laeven y Valencia), mostrando la distribución
  de trayectorias, no solo el promedio.
- **Análogos históricos** (fase 3): búsqueda de episodios país-año con condiciones similares
  (vecinos más cercanos en variables estandarizadas: inflación, crecimiento, deuda, cuenta
  corriente…) y visualización de lo que ocurrió *después* en esos episodios.
  Advertencias obligatorias: muestras pequeñas, contextos distintos, resultado descriptivo,
  no predictivo.

## 7. Prospectiva

### Tipos (ver [principios editoriales §3](../principios-editoriales.md#3-vocabulario-de-prospectiva))

| Tipo | Métodos en el sistema | Validación |
|---|---|---|
| **Proyección** | ETS/ARIMA con intervalos; proyecciones demográficas de la ONU (probabilísticas) | Validación fuera de muestra (*backtesting*) con origen móvil. |
| **Pronóstico** | Archivo de pronósticos de terceros (FMI WEO, encuestas de expectativas de Banxico) por edición; pronósticos propios simples y documentados | **Evaluación *ex post***: error medio, sesgo y comparación contra una referencia ingenua. |
| **Escenario** | Modelos contables transparentes con supuestos explícitos | Sensibilidad a cada supuesto; escenarios alternativos. |
| **Riesgo** | Registro de riesgos con evidencia e indicadores de seguimiento | Sin probabilidades salvo base cuantitativa documentada. |

### Plantilla obligatoria de escenario

```yaml
id: ESC-001
pregunta: ¿Cómo evolucionaría la deuda pública/PIB de México bajo distintos supuestos?
modelo: >
  Dinámica de deuda: d_t = d_{t-1} · (1 + i_t) / (1 + g_t) − bp_t + ajustes_t
  d = deuda/PIB; i = tasa de interés nominal implícita; g = crecimiento del PIB nominal;
  bp = balance primario/PIB.
horizonte: 2026–2032
variables: [crecimiento real, inflación (deflactor), tasa implícita, balance primario]
supuestos:
  referencia: >
    Supuestos publicados por terceros (p. ej., FMI WEO de octubre de 2026 o el
    Paquete Económico de SHCP), atribuidos y con fecha.
  alternativos:
    - nombre: crecimiento bajo
      cambio: g real −1 pp respecto a la referencia
    - nombre: tasas altas
      cambio: i +150 pb
    - nombre: consolidación fiscal
      cambio: bp +1 pp del PIB
incertidumbre: >
  Gráfica de abanico a partir de la distribución histórica conjunta de los choques
  a g, i y bp (enfoque estocástico simple).
sensibilidad: gráfica de tornado (efecto sobre d en 2032 de mover cada supuesto)
etiquetas: >
  Los escenarios se nombran por sus supuestos; no se califican como probables,
  mejores o peores.
```

Ventaja de empezar con la dinámica de deuda: es una identidad contable que todos pueden
verificar, por lo que el debate se centra en los supuestos, que es donde debe estar. Además,
puede ejecutarse completamente en el navegador (controles para mover supuestos sin servidor).

## 8. Mapa de evidencia (fase 3)

Para responder "¿qué evidencia hay a favor y en contra de una interpretación?":

```yaml
id: AF-001
afirmacion: "<texto literal de la afirmación>"
atribuida_a: "<actor, documento y fecha>"
tipo: [descriptiva | causal | predictiva]
evidencia_a_favor:
  - {grafica: d2/..., indicador: ..., nota: ...}
evidencia_en_contra:
  - {estudio: "<cita>", nota: ...}
datos_faltantes: "<qué haría falta para resolverla>"
estado: [sustentada | en disputa | no sustentada | no verificable con los datos disponibles]
revisado: 2026-10-03
```

El estado se asigna con criterios publicados y se revisa cuando llegan datos nuevos.
