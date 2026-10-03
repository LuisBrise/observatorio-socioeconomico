# Principios editoriales y epistémicos

> Este documento es la "constitución" del observatorio. Todo análisis, gráfica, texto
> o escenario publicado debe cumplirlo. Si una regla técnica entra en conflicto con
> estos principios, ganan los principios.

## 1. Los cuatro niveles epistémicos

Cada afirmación que produce el sistema pertenece a **uno** de estos niveles, y el nivel
debe ser visible para quien lee (etiqueta en el texto y estilo visual distinto).

| Nivel | Qué es | Ejemplo | Requisito mínimo |
|---|---|---|---|
| **DATO** | Lo que una fuente reporta, con su definición. | "INEGI registró *N* defunciones por homicidio en 2024 (estadísticas de defunciones registradas, año de ocurrencia)." | Fuente, dataset, versión (vintage), definición. |
| **ANÁLISIS** | Patrón o relación calculada de forma reproducible a partir de los datos. | "La tasa cayó *x* % entre 2019 y 2024; el cambio es mayor que el rango de variación interanual de 2000–2018." | Método, transformación, ventana temporal, código. |
| **INTERPRETACIÓN** | Explicación posible de un patrón. | "Una explicación propuesta por *A* es…; evidencia a favor…; evidencia en contra…; explicaciones alternativas…" | Atribución, evidencia a favor y en contra, alternativas. |
| **OPINIÓN** | Juicio normativo (qué es deseable). | "El gobierno debería…" | El sistema **no produce** opiniones propias. Solo las reporta atribuidas a un actor identificado. |

## 2. Escalera de evidencia causal y vocabulario permitido

El lenguaje debe corresponder a la fuerza de la evidencia. Esta tabla se aplica en
textos, títulos de gráficas y notas automáticas.

| Evidencia disponible | Verbos permitidos | Verbos prohibidos |
|---|---|---|
| Coincidencia temporal | "coincide con", "ocurrió después de", "durante" | "provocó", "gracias a", "por culpa de" |
| Correlación (con controles básicos: tendencia, población, precios) | "se asocia con", "covaría con" | "explica", "determina" |
| Asociación robusta (varias fuentes, ventanas y especificaciones) | "asociación consistente", "patrón robusto" | "causa" |
| Diseño cuasi-experimental creíble (publicado y revisado) | "evidencia de efecto según *autor/estudio*" | Generalizar fuera del contexto del estudio |
| Consenso de literatura con múltiples diseños | "la evidencia disponible indica que…" (citando) | Presentarlo como verdad cerrada |

## 3. Vocabulario de prospectiva

| Término | Definición en este sistema | Representación visual |
|---|---|---|
| **Proyección** | Extrapolación estadística de una serie bajo el supuesto de que continúan sus patrones pasados. | Línea discontinua + banda de intervalo de predicción. |
| **Pronóstico** | Predicción de una variable bajo un modelo explícito, evaluable *ex post*. Incluye pronósticos de terceros (FMI, Banxico, analistas), siempre atribuidos. | Línea discontinua + banda; etiqueta con modelo/autor y fecha de emisión. |
| **Escenario** | Trayectoria condicional: "si se cumplen los supuestos A, B, C, entonces…". No es una predicción. | Línea punteada, con nombre del escenario y supuestos visibles. |
| **Riesgo** | Evento posible, con evidencia que lo hace plausible, sin afirmar que ocurrirá. | Texto y registro de riesgos; nunca una línea en una serie. |

Reglas:

- Ningún escenario se etiqueta como "probable", "mejor" o "peor" sin una justificación
  cuantitativa explícita. Preferimos nombrarlos por sus supuestos
  ("crecimiento bajo / tasas altas") y, si se usan las etiquetas "base / favorable /
  adverso", se define respecto a qué variable es favorable o adverso.
- No se asignan probabilidades a riesgos salvo que exista una base cuantitativa
  documentada (frecuencias históricas, modelos calibrados, mercados, encuestas de expertos).
- Todo pronóstico propio se archiva y se evalúa contra lo que efectivamente ocurrió.

## 4. Neutralidad política: reglas operativas

El sistema **no**:

- recomienda candidatos ni partidos, ni sugiere por quién votar;
- clasifica a políticos o gobiernos como "buenos" o "malos";
- asigna puntuaciones políticas propias ni construye un índice compuesto de "cómo va México";
- usa lenguaje propagandístico, adjetivos valorativos o metáforas cargadas;
- presenta opiniones como hechos.

Salvaguardas concretas contra el sesgo (incluido el sesgo involuntario):

1. **Preguntas e indicadores antes que resultados.** Para cada dashboard o análisis, las
   preguntas, los indicadores y las ventanas temporales se registran en el catálogo
   *antes* de mirar los resultados. Los cambios posteriores quedan en el historial de git
   con su justificación.
2. **Ventanas temporales por regla.** Por defecto se muestra la serie completa disponible
   o periodos estandarizados (p. ej., 10/20/30 años). Cualquier recorte distinto se justifica.
   Nunca se elige un año de inicio porque "se ve mejor".
3. **Simetría.** Los mismos indicadores, métricas y tratamiento se aplican a todos los
   gobiernos, partidos, periodos y países.
4. **Atribución temporal cuidadosa.** Se dice "durante el periodo 2019–2024", no
   "resultado del gobierno X". Se documentan rezagos de política, herencias y choques
   externos (crisis 2008–2009, pandemia 2020, cambios en política comercial, etc.).
5. **Inclusión de fuentes por calidad, no por resultado.** Una fuente solo se excluye por
   criterios de calidad documentados, nunca porque su resultado incomode o favorezca una narrativa.
6. **Afirmaciones controvertidas:** se atribuyen a quien las hace, se presenta la evidencia
   a favor y en contra, y se señalan los datos que faltan para resolverlas.
7. **Color sin juicio.** No se usa rojo/verde para indicadores cuya dirección deseable está
   en disputa (p. ej., tamaño del gasto público, deuda, salario mínimo). Los colores de
   partidos se usan solo en gráficas electorales y siguen la convención institucional de cada partido.
8. **Revisión de sesgo antes de publicar** (ver lista de verificación abajo).

## 5. Incertidumbre

- Si la fuente publica incertidumbre (intervalos de confianza, errores estándar,
  intervalos de credibilidad, rangos), se muestra.
- Si varias fuentes miden lo mismo y difieren, la diferencia es información: se muestra
  el rango y se explica el porqué.
- "No lo sabemos" y "los datos no permiten concluir" son respuestas válidas.
- Datos preliminares, estimados, imputados o sujetos a revisión se marcan como tales.

## 6. Ética y datos sensibles

- Los datos sobre víctimas, personas desaparecidas, salud o migración se publican solo
  en forma agregada; nunca se publican microdatos que permitan identificar personas.
- Se respetan las licencias de cada fuente; si una licencia impide redistribuir datos,
  se publican solo los derivados permitidos.
- Las cifras de violencia representan personas: el lenguaje y el diseño lo reflejan
  (sin estética sensacionalista).

## 7. Lista de verificación antes de publicar una gráfica o un dashboard

- [ ] ¿La pregunta que responde la gráfica está escrita?
- [ ] ¿El título describe el mensaje y se sostiene con los datos mostrados?
- [ ] ¿Cada número tiene fuente, fecha del dato y versión del dataset?
- [ ] ¿Las etiquetas DATO / ANÁLISIS / INTERPRETACIÓN están asignadas a los textos?
- [ ] ¿El lenguaje causal corresponde al nivel de evidencia?
- [ ] ¿La ventana temporal sigue la regla, o el recorte está justificado?
- [ ] ¿Se muestran la incertidumbre y las rupturas de serie conocidas?
- [ ] ¿La comparación internacional es válida (unidades, PPA, precios, población, definiciones)?
- [ ] ¿Hay al menos una explicación alternativa para cada interpretación?
- [ ] ¿Las advertencias ("qué no podemos concluir") están escritas?
- [ ] ¿Funcionaría igual esta gráfica si el resultado favoreciera a otro actor político?
- [ ] ¿La licencia de la fuente permite publicar lo que se publica?
