# 09 · Primeros dashboards y sistema visual

## 1. Plantilla narrativa común

Cada dashboard sigue la secuencia **pregunta → evidencia → contexto → cambio →
interpretación → incertidumbre**, en siete bloques:

| Bloque | Contenido | Nivel epistémico |
|---|---|---|
| 1. **Titular** | El mensaje principal, en una frase verificable con los datos mostrados. | ANÁLISIS |
| 2. **Contexto** | Por qué importa la pregunta; qué se mide y qué no. | DATO / contexto |
| 3. **Visualización principal** | La gráfica que cuenta la historia. | DATO + ANÁLISIS |
| 4. **Evidencia de apoyo** | Gráficas e indicadores que confirman, matizan o contradicen el titular. | DATO + ANÁLISIS |
| 5. **Contexto histórico** | Cómo se compara con el pasado de México. | ANÁLISIS |
| 6. **Comparación internacional** | Dónde está México respecto a ALC, sus pares y el mundo. | ANÁLISIS |
| 7. **Advertencias** | Qué **no** podemos concluir; rupturas, discrepancias e incertidumbre. | — |

**Los titulares se escriben después del análisis, no antes.** Lo que se registra antes de
mirar los datos son las preguntas, los indicadores, las ventanas y los grupos de comparación.

## 2. Selección de los tres primeros dashboards

Criterios: (1) responden las preguntas de fondo del proyecto, (2) en conjunto ponen a prueba
todo el pipeline, (3) aumentan la dificultad de forma gradual y (4) se apoyan en fuentes con buen acceso.

| | D1 · México en el largo plazo | D2 · Pulso de México | D3 · Democracia e instituciones en ALC |
|---|---|---|---|
| Escala | México vs ALC y el mundo | México (nacional) | ALC y el mundo |
| Horizonte | 1950/1980–hoy (+ proyecciones demográficas) | Últimos 10 años, énfasis en los últimos meses | 1978–hoy |
| Frecuencia | Anual | Diaria a anual | Anual |
| Pone a prueba | Comparaciones internacionales, agregados, PPA, grupos de comparación, proyecciones de la ONU | APIs nacionales con token, alta frecuencia, estacionalidad, revisiones, frescura, detector de cambios | Índices de expertos con incertidumbre, contraste entre fuentes, línea de tiempo de eventos, temas políticamente sensibles |
| Dificultad de ingesta | Baja | Media | Baja |

---

## 3. D1 · México en el largo plazo

**Pregunta rectora:** ¿Cómo ha cambiado México desde 1980 y cómo ha cambiado su posición
respecto a América Latina y a otras economías comparables?

**Preguntas específicas:**

1. ¿Cómo ha evolucionado el ingreso per cápita de México en relación con ALC, sus pares estructurales y EE.UU.?
2. ¿Ese cambio se explica mecánicamente por productividad, empleo o demografía?
3. ¿Cómo cambió la estructura demográfica y qué implica para las próximas décadas (según las proyecciones de la ONU)?
4. ¿Cómo evolucionaron la esperanza de vida, la pobreza y la desigualdad, y cómo se comparan con la región?
5. ¿En qué indicadores ha mejorado o empeorado la posición relativa de México dentro de ALC?

**Visualizaciones propuestas:**

| # | Pregunta | Forma | Qué debe notar el ojo en los primeros 5 segundos | Contexto necesario |
|---|---|---|---|---|
| 1.1 | Ingreso per cápita relativo | **Serie anotada**: México resaltado; países de ALC en gris tenue; banda de rango intercuartil regional; crisis anotadas (1982, 1994–95, 2008–09, 2020) | Dónde está la línea de México respecto a la banda regional, y cómo cambia esa posición | PPA 2021, dólares constantes; composición de ALC; cobertura |
| 1.2 | Convergencia con EE.UU. | **Línea** del PIB per cápita de México como % del de EE.UU. (y de pares seleccionados) | Si la distancia se cierra, se abre o se mantiene | Mismo deflactor y PPA; Maddison para antes de 1990 |
| 1.3 | Fuentes del crecimiento | **Cascada** por década: productividad laboral, tasa de empleo, proporción en edad de trabajar | Qué componente domina en cada década | Es una identidad contable, no una explicación causal |
| 1.4 | Transición demográfica | **Pirámides en *small multiples*** (1980, 2000, 2024, 2050) + **razón de dependencia con abanico** de proyección | El cambio de forma de la pirámide; dónde termina el bono demográfico y con qué incertidumbre | Las proyecciones son de la ONU (WPP 2024), con intervalos del 80 % y el 95 % |
| 1.5 | Bienestar y desigualdad | **Dispersión conectada**: Gini vs PIB per cápita para países de ALC (trayectorias 2000–hoy), México resaltado | La dirección de la trayectoria de México respecto a las demás | Encuestas de ingreso vs consumo; comparación con WID en una nota |
| 1.6 | Posición relativa | **Gráfica de pendiente** 2000 → último dato del percentil de México en ALC para 8–10 indicadores | Qué líneas suben y cuáles bajan | Mismos indicadores, mismas fuentes y misma regla de ventana |

**Advertencias anticipadas:** revisiones de PPA; incertidumbre del Maddison para los años
antiguos; la descomposición contable no identifica causas; pobreza con definiciones distintas.

---

## 4. D2 · Pulso de México

**Pregunta rectora:** ¿Cómo está México ahora, en cada dimensión, en relación con su propia historia reciente?

**Diseño central: no hay índice compuesto ni semáforo.** Cada indicador se presenta con su
propio contexto histórico, y cada dimensión se lee por separado.

**Tarjeta de contexto histórico (componente principal):**

```text
┌───────────────────────────────────────────────────────┐
│ Inflación general anual (INPC)                [ficha] │
│ 3.9 %                       dato a: ago 2026 (P)      │
│ ─────────────────────────────── publicado: 09/09/2026 │
│ ▁▂▃▅▇█▆▄▃▂▂▃  ← últimos 10 años, banda = rango 2000–hoy│
│ Percentil en su historia: ──────●────  (p62)          │
│ Cambio en 12 meses: −0.6 pp (rango típico: ±1.1 pp)   │
└───────────────────────────────────────────────────────┘
(valores ilustrativos, no reales)
```

Cada tarjeta muestra: último dato, periodo y fecha de publicación, estatus (preliminar o
revisado), una línea mínima con el rango histórico, el percentil del dato actual en la
historia de la serie (en color **neutral**, porque "alto" no siempre es malo) y el cambio
reciente comparado con su rango típico.

**Secciones:** actividad económica · empleo e ingresos · precios y tasas · finanzas públicas ·
sector externo · seguridad · percepción · demografía (contexto anual) · política e
instituciones (contexto anual en la fase 1; aprobación agregada de encuestas en la fase 2).

**Visualizaciones propuestas:**

| # | Pregunta | Forma | Qué debe notar el ojo en los primeros 5 segundos | Contexto necesario |
|---|---|---|---|---|
| 2.1 | ¿Qué está fuera de lo habitual? | **Mapa de calor de percentiles**: filas = indicadores, columnas = meses (últimos 5–10 años), color = percentil en su propia historia | Columnas donde muchos indicadores se vuelven inusuales a la vez (p. ej., 2020) y filas inusuales hoy | Escala secuencial neutra; los percentiles no son juicios |
| 2.2 | ¿Qué cambió de forma inusual recientemente? | **Lista ordenada** generada por el detector de cambios (con corrección por comparaciones múltiples) | Los pocos cambios que destacan estadísticamente | "Inusual" ≠ "malo"; método enlazado |
| 2.3 | Violencia letal: dos fuentes | **Dos series** (INEGI anual, SESNSP mensual) en la misma escala de tasa, con la brecha sombreada y la discrepancia DIS-001 explicada | Que las dos fuentes difieren, y cómo | Por qué difieren; categorías vecinas |
| 2.4 | Tarjetas por dimensión | Rejilla de tarjetas de contexto histórico | — | Fechas de cada dato |

**Advertencias anticipadas:** el "presente" mezcla periodos; las cifras preliminares se
revisan; el percentil depende de la ventana histórica; las encuestas de percepción no miden incidencia.

---

## 5. D3 · Democracia e instituciones en América Latina (recomendado)

**Pregunta rectora:** ¿Cómo han evolucionado la democracia y las instituciones en América
Latina y en México desde 1978, según distintas fuentes, y con qué grado de certeza?

**Preguntas específicas:**

1. ¿Cómo han cambiado los índices de democracia en cada país de ALC?
2. ¿En qué componentes (elecciones limpias, libertades, controles al Ejecutivo, independencia
   judicial, igualdad ante la ley) se concentran los cambios de México?
3. ¿Coinciden V-Dem, Freedom House e IDEA? ¿Dónde difieren y por qué?
4. ¿Qué tan seguros podemos estar de los cambios recientes, dado el margen de incertidumbre?
5. ¿Qué debate metodológico existe sobre la medición del retroceso democrático?

**Visualizaciones propuestas:**

| # | Pregunta | Forma | Qué debe notar el ojo en los primeros 5 segundos | Contexto necesario |
|---|---|---|---|---|
| 3.1 | Trayectorias por país | ***Small multiples*** (un panel por país de ALC) del índice de democracia electoral de V-Dem con **banda de intervalo de credibilidad**; México primero y resaltado | La forma de cada trayectoria y el ancho de su incertidumbre | Qué mide el índice; escala 0–1; intervalos |
| 3.2 | Componentes en México | ***Small multiples*** de 6–8 componentes de V-Dem con eventos anotados (alternancias, reformas, cambios institucionales) | Qué componentes se mueven y cuáles no | Los eventos son contexto, no causas |
| 3.3 | Acuerdo entre fuentes | **Paneles por país** con V-Dem, Freedom House e IDEA en escala común (percentil mundial), con la región de desacuerdo sombreada | Dónde coinciden y dónde divergen | Conceptos y escalas distintos; IDEA usa insumos parcialmente comunes con V-Dem |
| 3.4 | Mapa regional | **Mapa** de ALC con el cambio en 10 años (escala divergente con 0 como centro) + tabla de clasificación de régimen | El patrón geográfico del cambio | El cambio en 10 años depende del año de inicio: ventana fija por regla |
| 3.5 | El debate | **Recuadro** con los argumentos de Little y Meng (2024) y la respuesta de Knutsen et al. (2024), atribuidos, con la evidencia de cada parte | — | Es un debate académico abierto |

**Advertencias anticipadas:** son juicios expertos; las versiones nuevas revisan años
anteriores; los cambios dentro del margen de incertidumbre no son concluyentes; ninguna de
estas fuentes mide la opinión ciudadana (eso requiere encuestas, fase 2).

### Alternativa para D3: Violencia letal en México

Si prefieres empezar por seguridad: homicidios según INEGI, SESNSP y UNODC (1990–hoy),
tasas por estado (*small multiples* y mapa), categorías vecinas y desapariciones, y la
comparación internacional. Es el mejor caso de estudio del protocolo de discrepancias, pero
su ingesta es más laboriosa (microdatos de defunciones, datos municipales). Lo recomiendo como D4.

---

## 6. Sistema visual (borrador, se desarrollará en la etapa 10)

### Principios

1. **El título dice el mensaje; el subtítulo, la pregunta y la unidad.**
2. **Etiquetas directas** en lugar de leyendas siempre que sea posible.
3. **Contexto en gris, foco en color.** El color se usa para dirigir la atención, no para decorar.
4. **Anotaciones como parte de la gráfica**: eventos, rupturas, cambios de fuente.
5. **Fuente debajo de cada gráfica** y panel de procedencia desplegable.
6. **Sin 3D, sin gráficas de pastel, sin semáforos ni gradientes decorativos.**

### Tipografía

- Titulares y narrativa: una serif legible (candidata: *Source Serif 4*).
- Interfaz, ejes y números: una sans con cifras tabulares (candidatas: *Inter* o *IBM Plex Sans*).
- Las dos son fuentes abiertas (licencia OFL).

### Color

| Uso | Regla |
|---|---|
| Neutros | Escala de grises cálida para ejes, contexto y países no resaltados. |
| Foco (México) | Un solo color de acento, **no asociado a ningún partido político mexicano** (se evitan guinda, azul PAN, rojo y verde PRI, naranja MC, verde PVEM, rojo PT). Candidato a validar: verde azulado profundo. |
| Comparador secundario | Un segundo acento sobrio (p. ej., ocre) para EE.UU. o la mediana regional. |
| Categóricos | Máximo 6 colores, aptos para daltonismo; si hay más categorías, *small multiples*. |
| Secuenciales | Un solo tono (mapas de calor, coropletas). |
| Divergentes | Solo si el punto medio tiene significado (cero, promedio) y la dirección no está en disputa. |
| Partidos | Solo en gráficas electorales, con los colores institucionales de cada partido. |
| Valoración (bien/mal) | Solo para indicadores con dirección normativa no disputada, y nunca con rojo/verde puros. |

### Codificación del estatus epistémico (consistente en todo el sitio)

| Estatus | Codificación |
|---|---|
| Observado | Línea continua |
| Preliminar | Línea continua con el último punto hueco |
| Estimado o imputado | Trazo más claro |
| Proyección o pronóstico | Línea discontinua + banda de intervalo |
| Escenario | Línea punteada con su nombre y sus supuestos |
| Incertidumbre de la medición | Banda semitransparente |
| Ruptura de serie | Corte en la línea + marcador con nota |
| Evento | Línea vertical fina con etiqueta |

### Componentes reutilizables (biblioteca inicial)

`SerieAnotada` · `SmallMultiples` · `Pendiente` · `Ranking` (*bump chart*) ·
`DistribucionGrupo` (país dentro de su grupo) · `Abanico` (*fan chart*) ·
`MapaCalorPercentiles` · `DispersionConectada` · `Cascada` · `Piramide` · `MapaMX` (estados) ·
`MapaMundo` · `LineaDeTiempo` · `TarjetaContexto` · `PieDeFuente` · `PanelProcedencia` ·
`EtiquetaEpistemica` (DATO / ANÁLISIS / INTERPRETACIÓN) · `RecuadroAdvertencias`.

### Accesibilidad

Contraste AA como mínimo; paletas probadas con simulación de daltonismo; navegación con
teclado; texto alternativo generado a partir de los datos; descarga de los datos de cada
gráfica en tabla; diseño legible en el celular.

## 7. Definición de "terminado" para cada dashboard

- [ ] Preguntas, indicadores, ventanas y grupos registrados en el catálogo antes del análisis.
- [ ] Todas las gráficas con procedencia completa y pasando la compuerta C5.
- [ ] Titular verificado contra los datos y con análisis de sensibilidad.
- [ ] Advertencias escritas; discrepancias relevantes documentadas.
- [ ] Lista de verificación de los [principios editoriales](../principios-editoriales.md) completa.
- [ ] Probado en escritorio y en celular, en modo claro y oscuro.
- [ ] Revisado por ti antes de publicarse.
