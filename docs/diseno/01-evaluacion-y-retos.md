# 01 · Evaluación del proyecto y retos metodológicos

## 1. Evaluación general

### Lo que está bien planteado

- **El principio epistémico (dato / análisis / interpretación / opinión)** es el activo más
  valioso del proyecto. Casi ningún tablero público lo hace explícito. Lo convertimos en
  una regla del sistema: cada texto lleva etiqueta y cada gráfica, su trazabilidad
  (ver [principios editoriales](../principios-editoriales.md)).
- **La trazabilidad como requisito, no como extra.** Obliga a diseñar primero el modelo
  de metadatos y el almacenamiento, y después las gráficas. Es el orden correcto.
- **Tres escalas (México, ALC, mundo)** permiten lo que más falta en el debate público:
  contexto comparativo. Muchas "noticias" sobre México son, en realidad, tendencias regionales
  o globales, y al revés.
- **Rechazar un índice compuesto de México** evita el error metodológico más común de
  los observatorios (ponderaciones arbitrarias que esconden juicios normativos).

### Riesgos principales

| Riesgo | Por qué importa | Mitigación propuesta |
|---|---|---|
| **Alcance excesivo** | 9 dimensiones × más de 100 indicadores × 3 escalas × pasado/presente/futuro. Un sistema que ingiere 300 series pero no responde bien ninguna pregunta no sirve. | Construir **rebanadas verticales**: pocas preguntas respondidas de punta a punta (fuente → dashboard) antes de ampliar. El catálogo puede ser amplio; la ingesta, gradual. |
| **Costo de mantenimiento** | Cada fuente es una dependencia que se rompe. Ejemplo real: en noviembre de 2025 el FMI retiró su portal y su API heredados y reorganizó IFS y DOTS en nuevos *dataflows* SDMX; todo código basado en la API anterior dejó de funcionar. | Conectores aislados, pruebas de contrato semanales, política de "último dato válido" (si una fuente falla, el sitio sigue con la versión anterior y lo indica). |
| **El instrumento de medición cambia** | En México, varias instituciones que producen o regulan datos cambiaron: la medición de pobreza pasó de CONEVAL a INEGI (reforma publicada el 20/12/2024; leyes secundarias vigentes desde el 17/07/2025); se extinguieron órganos autónomos (INAI, COFECE, IFT, CRE, CNH, Mejoredu); la reforma judicial cambió la integración del Poder Judicial (elección de junio de 2025); hay propuestas de reforma electoral en discusión. | Registrar los cambios institucionales como **eventos con efecto potencial sobre series**; verificar la continuidad metodológica de cada serie afectada; anotar rupturas en las gráficas. |
| **Sesgo de selección y de narrativa** | Elegir indicadores, años de inicio o comparadores ya es una decisión con consecuencias políticas. | Preguntas e indicadores definidos antes de ver los resultados; ventanas por regla; grupos de comparación fijos y versionados (ver principios editoriales §4). |
| **Licencias** | ACLED, Latinobarómetro, LAPOP, IHME-GBD y EIU tienen restricciones de acceso o redistribución. | La licencia es un campo obligatorio del catálogo; un control automático impide publicar datos que la licencia no permite. |
| **Falsa precisión sobre el presente y el futuro** | "El presente" mezcla datos de este mes con datos de hace dos años; los pronósticos fallan con frecuencia. | Toda cifra muestra la fecha a la que corresponde; se archivan pronósticos y se mide su error. |
| **Continuidad de fuentes** | Algunas series dependen de financiamiento externo que puede desaparecer (en 2025 se suspendieron programas estadísticos financiados por cooperación internacional, como las encuestas DHS). | Indicar fuentes alternativas para cada concepto clave; evitar depender de una sola fuente en los indicadores centrales. |

### Recomendación estratégica

1. **Profundidad antes que amplitud.** Los primeros seis meses deben producir 3 dashboards
   impecables y un pipeline robusto, no 30 dashboards frágiles.
2. **El catálogo es el producto central.** Las gráficas cambian; el catálogo de fuentes,
   conceptos, indicadores, transformaciones y discrepancias es lo que da valor acumulativo.
3. **Diseñar para una o dos personas manteniendo el sistema.** Eso descarta infraestructura
   con servidores propios y favorece sitios estáticos, archivos Parquet y automatización en CI.

---

## 2. Retos metodológicos

### A. Medición: concepto ≠ indicador ≠ serie

El error más frecuente es tratar un número como si fuera el fenómeno. El sistema separa:

- **Concepto**: el fenómeno (p. ej., "pobreza").
- **Indicador**: una operacionalización (p. ej., "% de la población con ingreso menor a una línea").
- **Serie**: una medición concreta de una fuente, con su metodología y versión
  (p. ej., "Banco Mundial PIP, línea de US$8.30 PPA 2021, versión de junio de 2025").

Cada tipo de medición tiene sesgos característicos:

| Tipo de medición | Ejemplos | Sesgos típicos |
|---|---|---|
| Registros administrativos | Defunciones (INEGI), carpetas de investigación (SESNSP), empleo formal (IMSS) | Subregistro, cambios en criterios de registro, incentivos institucionales a clasificar de cierta forma. |
| Encuestas de hogares | ENIGH, ENOE, ENVIPE | Error muestral, no respuesta, subdeclaración de ingresos altos, cambios de cuestionario. |
| Cuentas nacionales | PIB, consumo, inversión | Revisiones, cambios de año base, estimaciones preliminares. |
| Índices de expertos | V-Dem, Freedom House, WJP | Juicio humano, agregación, posibles sesgos de codificadores; los resultados dependen del concepto de democracia usado. |
| Datos de eventos basados en medios | ACLED, GDELT | Dependen de la cobertura mediática, que no es uniforme en el territorio ni en el tiempo. |
| Estimaciones modeladas | UN WPP, IHME-GBD, WID, estimaciones modeladas de la OIT | Dependen de supuestos del modelo; pueden diferir mucho de los datos nacionales. |
| Encuestas de percepción | Confianza, aprobación, percepción de inseguridad | Miden opiniones, no condiciones objetivas; sensibles a la redacción, al modo de levantamiento y al contexto. |

**Ejemplos de discrepancias legítimas entre fuentes (no errores):**

- **Homicidios.** INEGI (certificados de defunción, por año de ocurrencia o registro)
  y SESNSP (víctimas en carpetas de investigación iniciadas por las fiscalías) miden cosas
  distintas, en momentos distintos y por canales distintos. Históricamente, INEGI reporta
  más homicidios que SESNSP. Algunos analistas señalan además posibles reclasificaciones
  hacia categorías vecinas ("otros delitos que atentan contra la vida", desapariciones);
  el sistema debe vigilar esas categorías junto con el homicidio.
- **Pobreza.** La medición oficial multidimensional (CONEVAL hasta 2022; INEGI desde la
  medición 2024), las líneas internacionales del Banco Mundial (US$3.00, 4.20 y 8.30 diarios
  en PPA 2021 desde junio de 2025; antes US$2.15, 3.65 y 6.85 en PPA 2017) y la metodología
  de CEPAL producen cifras distintas y todas son legítimas: responden preguntas distintas.
- **Desigualdad.** Las encuestas de hogares (ENIGH) subestiman los ingresos más altos. WID
  combina encuestas, datos fiscales y cuentas nacionales, y obtiene una concentración del
  ingreso mucho mayor. Las dos cifras no se contradicen: miden con distinta cobertura de la cola superior.

### B. Rupturas de serie y revisiones

Rupturas que ya sabemos que debemos manejar:

| Serie | Ruptura | Implicación |
|---|---|---|
| PIB (SCNM, INEGI) | Cambio de año base (base 2018) | Empalmar series de bases distintas con un método documentado. |
| INPC | Base 2ª quincena de julio de 2018 = 100; cambios de canasta | Cambio en la ponderación de los bienes de la canasta. |
| Empleo | ENE → ENOE (2005); suspensión por pandemia y ETOE (2020); ENOEᴺ (desde 2020) | Rupturas de diseño muestral y de cuestionario. |
| Incidencia delictiva (SESNSP) | Metodología anterior (1997–2017) vs nueva (2015 en adelante) | No son series continuas; el traslape 2015–2017 permite estudiar la diferencia. |
| Pobreza multidimensional | Cambio de institución (CONEVAL → INEGI); ajustes metodológicos a lo largo del tiempo | Verificar continuidad con los documentos metodológicos de INEGI. |
| PPA (Banco Mundial) | Rondas del ICP (2011 → 2017 → 2021) | Las comparaciones en PPA cambian retroactivamente con cada ronda. |
| Libertad de prensa (RSF) | Nueva metodología en 2022 | Los puntajes anteriores y posteriores no son comparables directamente. |
| Percepción de corrupción (TI) | Nueva escala en 2012 | No comparar puntajes anteriores con posteriores. |
| Población (UN WPP, CONAPO) | Revisiones completas cada 2–3 años | Cambian los denominadores de todas las tasas per cápita, retroactivamente. |

**Revisiones:** un mismo dato (p. ej., el PIB del 2T de 2024) cambia con el tiempo. Por eso
cada descarga se guarda como una **versión (vintage)** fechada. Así podemos
(1) reproducir lo que se sabía en una fecha, (2) medir revisiones y (3) evaluar pronósticos
con la información disponible en su momento.

### C. Comparabilidad

- **Nominal vs real; tipo de cambio de mercado vs PPA.** Para comparar niveles de vida se
  usan PPA; para comparar peso económico internacional, tipos de cambio de mercado. Cada
  comparación declara cuál usa y por qué.
- **Denominadores.** Las tasas per cápita dependen de la población estimada; un cambio de
  proyección de población puede mover una tasa de homicidios más que la variación real.
- **Estructura por edad.** La mortalidad por enfermedades crónicas debe estandarizarse por edad para
  compararla entre países o periodos.
- **Agregados regionales.** "América Latina" no es una sola cosa:
  - definiciones distintas (Banco Mundial ALC, los 33 países de CEPAL, "Hemisferio Occidental" del FMI);
  - ponderaciones distintas (promedio simple, por población, por PIB);
  - composición cambiante por datos faltantes (Venezuela tiene huecos importantes desde
    mediados de la década de 2010; también Cuba, Haití y Nicaragua en varias series).

  **Propuesta:** mostrar a México *dentro de la distribución* regional (mediana, rango
  intercuartil, países individuales) en lugar de "México vs promedio". Cuando se reporte
  un agregado, informar su cobertura (qué porcentaje de la población regional tiene dato).
- **Calidad estadística heterogénea.** Ejemplos: las estadísticas de inflación de Argentina
  entre 2007 y 2015 (el FMI emitió una declaración de censura en 2013) y los huecos de
  publicación del Banco Central de Venezuela. El sistema incorpora indicadores de capacidad
  estadística (Statistical Performance Indicators del Banco Mundial) como metadatos de confianza.
- **Grupos de comparación.** Se definen por criterios explícitos *antes* del análisis,
  se versionan y no se cambian para "mejorar" una comparación.

### D. Tiempo

- **El "presente" es heterogéneo.** El PIB oportuno sale unos 30 días después del trimestre, el IGAE con
  unos dos meses de rezago, la pobreza cada dos años con meses de rezago, V-Dem una vez al año (marzo) y
  muchas series del Banco Mundial con uno o dos años de rezago. Cada cifra muestra
  "dato a: [periodo]" y "publicado: [fecha]".
- **Estacionalidad.** Las series mensuales y trimestrales se comparan contra el mismo
  periodo del año anterior o se usan cifras desestacionalizadas publicadas por la fuente;
  la desestacionalización propia se documenta.
- **Periodos de gobierno.** Comparar sexenios es legítimo pero difícil: hay rezagos de
  política, condiciones heredadas, choques externos y reversión a la media. El sistema
  muestra periodos, no atribuye resultados.
- **Elección de ventanas.** El año de inicio puede invertir una conclusión. Por eso las
  ventanas se definen por regla (ver principios editoriales §4.2) y se incluye análisis de
  sensibilidad a la ventana.

### E. Inferencia

- **Antes/después de un evento.** Hay confusores, anticipación, eventos simultáneos y
  reversión a la media. Las comparaciones pre/post son **descriptivas** salvo que exista un
  diseño cuasi-experimental creíble.
- **Comparaciones múltiples.** Si escaneamos 200 indicadores buscando "cambios
  significativos", alrededor de 10 aparecerán por azar con un umbral del 5 %. El detector de
  cambios usa control de la tasa de falsos descubrimientos (Benjamini–Hochberg) y lo dice.
- **Series cortas.** Con 30–50 observaciones anuales, la detección de quiebres y los
  pronósticos tienen poca potencia. Se reportan intervalos amplios honestamente.
- **Correlaciones espurias.** Dos series con tendencia correlacionan casi siempre; se
  analizan diferencias o desviaciones de tendencia, además de niveles.
- **Falacia ecológica.** Una correlación entre estados no implica la misma relación entre personas.

### F. Política y opinión pública

- **Resultados electorales en México.** Las coaliciones complican la atribución de votos (votos
  por combinaciones de partidos de una coalición); hay redistritaciones; partidos que nacen
  y pierden registro. Se necesita una tabla de equivalencias de partidos versionada y documentada.
- **Clasificación ideológica.** Ubicar partidos en izquierda/derecha está en disputa. Si se
  usa, se toma de fuentes expertas externas (p. ej., V-Party) atribuidas, nunca de una
  clasificación propia.
- **Encuestas de aprobación.** Difieren por casa encuestadora, modo (telefónico vs cara a
  cara), población objetivo y redacción. Agregarlas requiere un modelo con efectos de casa
  encuestadora, y su incertidumbre debe mostrarse.
- **Índices de democracia.** Son juicios expertos agregados. Existe un debate académico
  activo sobre si captan bien el "retroceso democrático" (Little y Meng, 2024, frente a la
  respuesta de Knutsen et al., 2024, en *PS: Political Science & Politics*). El sistema
  muestra varias fuentes, sus intervalos de incertidumbre y este debate, atribuido.
- **Reflexividad.** En México, las instituciones que producen datos (INEGI, INE) y las
  que se miden (Poder Judicial, órganos autónomos) son también objeto del debate político.
  Esto exige una documentación todavía más cuidadosa de cambios institucionales.

### G. Prospectiva

- Los pronósticos macroeconómicos tienen errores grandes, sobre todo cerca de recesiones.
  El sistema archiva pronósticos (FMI WEO, encuestas de expectativas) y muestra su historial de aciertos.
- Los escenarios son condicionales; su valor está en hacer explícitos los supuestos y la
  sensibilidad, no en "acertar".

### H. Ética

- Víctimas y personas desaparecidas: solo agregados; lenguaje cuidadoso.
- Microdatos: solo los que publican las fuentes oficiales, sin intentos de reidentificación.

---

## 3. De los retos a los mecanismos del sistema

| Reto | Mecanismo en el sistema |
|---|---|
| Concepto ≠ indicador ≠ serie | Modelo de catálogo de tres niveles ([taxonomía](03-taxonomia.md)). |
| Fuentes que difieren | Registro de discrepancias con causa documentada ([pipeline](06-pipeline-y-validacion.md)). |
| Rupturas | Campo `rupturas_conocidas` por dataset; detección automática; anotación en gráficas. |
| Revisiones | Almacenamiento por *vintage*; tabla de revisiones; reconstrucción "a fecha". |
| Agregados regionales | Distribuciones + cobertura explícita; ponderación declarada. |
| Calidad heterogénea | Metadatos de capacidad estadística y banderas de calidad por país y periodo. |
| Presente heterogéneo | "Dato a" y "publicado" obligatorios en cada cifra. |
| Comparaciones múltiples | Detector de cambios con control de falsos descubrimientos. |
| Sesgo de selección | Preguntas e indicadores registrados antes del análisis; ventanas por regla. |
| Pronósticos | Archivo de pronósticos y evaluación *ex post*. |
| Licencias | Campo de licencia obligatorio + control antes de publicar. |
| Fuentes frágiles | Conectores aislados, pruebas de contrato, último dato válido. |
