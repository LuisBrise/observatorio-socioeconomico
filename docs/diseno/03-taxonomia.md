# 03 · Taxonomía de indicadores

## 1. Estructura propuesta: cinco niveles + facetas

Una lista plana de temas no sirve para comparar fuentes ni para detectar duplicados. Propongo
una jerarquía con cinco niveles, más atributos transversales (facetas):

```text
Dimensión        Seguridad y justicia
└─ Subdimensión  Violencia letal
   └─ Concepto   Homicidio intencional
      └─ Indicador   Tasa de homicidios por 100 mil habitantes
         ├─ Serie    INEGI · defunciones por homicidio (certificado de defunción, año de ocurrencia)
         ├─ Serie    SESNSP · víctimas de homicidio doloso (carpetas de investigación, fecha de registro)
         └─ Serie    UNODC · homicidio intencional (compilación internacional)
```

La distinción **indicador / serie** permite que varias fuentes midan el mismo indicador, que
el sistema compare automáticamente sus valores y que cada discrepancia quede documentada.

### Facetas (atributos de cada indicador)

| Faceta | Valores | Para qué sirve |
|---|---|---|
| **Tipo de medición** | administrativo · encuesta · cuentas nacionales · índice de expertos · eventos codificados · estimación modelada · percepción | Saber qué sesgos esperar. |
| **Posición en la cadena** | contexto · insumo · proceso · resultado · percepción | No confundir gasto (insumo) con resultado, ni percepción con incidencia. |
| **Ritmo** | estructural (cambia en décadas) · intermedio · coyuntural (cambia en meses) | Responder "¿estructural o coyuntural?". |
| **Dirección normativa** | más es mejor · menos es mejor · neutral · **en disputa** | Determina si se permite una codificación de color con valoración (solo en los dos primeros casos). |
| **Cobertura geográfica** | mundo · ALC · nacional · estatal · municipal | Filtrar por escala. |
| **Frecuencia y rezago** | D/S/M/T/A · días de rezago típico | Saber qué tan "presente" es el dato. |
| **Desagregaciones** | sexo · edad · decil · urbano/rural · grupo étnico | Habilitar lentes transversales. |
| **Prioridad** | fase 1 · 2 · 3 | Planear la ingesta. |

## 2. Cambios respecto a la lista inicial

1. **Pobreza y desigualdad aparecían en Economía y en Sociedad.** Se agrupan en una dimensión
   propia, *Bienestar, pobreza y distribución*, para evitar duplicados.
2. **Se separa *Población y territorio*** como dimensión base: aporta los denominadores de
   casi todo y tiene un ritmo (estructural) distinto al de la economía.
3. **Política se divide** en elecciones y representación, opinión pública, instituciones y
   Estado de derecho, libertades, acción colectiva y cambio institucional. Son fenómenos
   con fuentes y lógicas de medición muy distintas.
4. **Seguridad incluye justicia** (impunidad, procesamiento de delitos), porque la cadena
   delito → denuncia → investigación → sanción explica muchas brechas entre fuentes.
5. **Energía y ambiente** se separan de **Ciencia y tecnología**.
6. **Relaciones internacionales, geopolítica y comercio exterior** se integran en
   *Inserción internacional*. Regla: los agregados macro (exportaciones totales, cuenta
   corriente) van en Economía; la estructura por socio (con quién, qué, cuánto depende) va en Inserción internacional.
7. **Se agrega una meta-dimensión: *Calidad y capacidad estadística*.** Nos dice cuánto
   confiar en los datos de cada país y periodo.
8. **Lentes transversales** (no dimensiones): género, territorio, generación/cohorte y
   distribución (mirar deciles y distribuciones, no solo promedios).
9. **Los eventos no son indicadores:** forman un dataset propio (línea de tiempo) que anota
   gráficas y habilita estudios de evento.

## 3. Taxonomía detallada (versión inicial)

Códigos de dimensión: `dem` · `eco` · `bie` · `pol` · `seg` · `ene` · `tec` · `int` · `meta`.
Fase: 1 = MVP; 2 = siguiente; 3 = posterior.

### `dem` · Población y territorio

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Tamaño y crecimiento | Población total, tasa de crecimiento | Estimación modelada / censo | UN WPP, CONAPO, INEGI (censos) | 1 |
| Estructura por edad | Edad mediana, razón de dependencia, población en edad de trabajar | Modelada / censo | UN WPP, CONAPO | 1 |
| Mortalidad y longevidad | Esperanza de vida, mortalidad infantil, exceso de mortalidad | Administrativo / modelada | UN WPP, INEGI, OMS | 1 |
| Fecundidad | Tasa global de fecundidad, fecundidad adolescente, nacimientos | Administrativo / encuesta | UN WPP, INEGI, CONAPO | 2 |
| Migración | Migrantes internacionales (stock), migración neta, mexicanos en EE.UU., encuentros fronterizos, migración en tránsito | Administrativo / encuesta | UN DESA, CONAPO, US Census (ACS), CBP, UPM-SEGOB | 2 |
| Urbanización | % urbano, población en zonas metropolitanas | Censo | UN WUP, INEGI, CONAPO | 2 |

### `eco` · Economía

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Actividad y crecimiento | PIB real y su crecimiento, PIB per cápita (PPA), IGAE, producción industrial | Cuentas nacionales | INEGI, Banco Mundial, FMI, Maddison | 1 |
| Productividad y estructura | Productividad laboral, productividad total de los factores, composición sectorial, complejidad económica | Cuentas nacionales / modelada | INEGI (KLEMS), Penn World Table, Growth Lab (Harvard) | 2 |
| Precios y política monetaria | Inflación general y subyacente, tasa objetivo, tasa real *ex ante*, expectativas | Administrativo / encuesta | INEGI, Banxico | 1 |
| Mercado laboral | Desocupación, participación, informalidad, subocupación, empleo formal registrado, salario real, salario mínimo real | Encuesta / administrativo | INEGI (ENOE), IMSS, CONASAMI, OIT | 1 |
| Finanzas públicas | Ingresos tributarios/PIB, gasto, balance primario, RFSP, SHRFSP, costo financiero de la deuda | Administrativo | SHCP, FMI, CEPAL, OCDE | 1–2 |
| Sector externo | Cuenta corriente, IED, remesas, tipo de cambio real, reservas | Administrativo | Banxico, INEGI, FMI | 1 |
| Inversión y crédito | Formación bruta de capital fijo/PIB, crédito al sector privado/PIB | Cuentas nacionales | INEGI, Banco Mundial | 2 |

### `bie` · Bienestar, pobreza y distribución

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Pobreza | Pobreza multidimensional, pobreza por ingresos, líneas internacionales, pobreza según CEPAL | Encuesta | INEGI (antes CONEVAL), Banco Mundial (PIP), CEPAL | 1 |
| Desigualdad | Gini, participación del 10 % y 1 % superior, razón de Palma | Encuesta / modelada | ENIGH, SEDLAC, PIP, WID | 1 |
| Ingreso de los hogares | Ingreso corriente real per cápita por decil | Encuesta | INEGI (ENIGH) | 2 |
| Salud | Acceso y carencia de servicios de salud, gasto de bolsillo, mortalidad materna, principales causas de muerte | Administrativo / encuesta | INEGI, SSA, OMS | 2 |
| Educación | Escolaridad promedio, matrícula y abandono escolar, aprendizajes (PISA) | Administrativo / evaluación | SEP, INEGI, UNESCO-UIS, OCDE | 2 |
| Vivienda y servicios | Hacinamiento, agua, drenaje, electricidad, internet en el hogar | Encuesta / censo | INEGI | 2 |
| Protección social | Cobertura de pensiones, transferencias sociales, carencia de seguridad social | Encuesta / administrativo | INEGI, OIT, CEPAL | 2 |
| Movilidad social | Movilidad intergeneracional | Encuesta | CEEY (ESRU-EMOVI), INEGI (MMSI) | 3 |

### `pol` · Política y gobierno

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Calidad democrática | Índices de democracia electoral, liberal, participativa, deliberativa e igualitaria (con intervalos); clasificación de régimen | Índice de expertos | V-Dem, Freedom House, IDEA (GSoD) | 1 |
| Elecciones y competencia | Participación electoral, porcentaje de votos, número efectivo de partidos, margen de victoria, alternancia, volatilidad (Pedersen) | Administrativo | INE, OPLE, organismos electorales de ALC, IDEA (Voter Turnout) | 2 |
| Representación | Composición legislativa, desproporcionalidad (índice de Gallagher), mujeres en el Congreso, gobierno unificado o dividido | Administrativo | INE, Cámara de Diputados, Senado, IPU Parline | 2 |
| Opinión pública | Aprobación presidencial, confianza en instituciones, apoyo a la democracia, satisfacción con la democracia | Percepción | Executive Approval Database, encuestadoras (agregadas), Latinobarómetro, LAPOP | 2–3 |
| Estado de derecho y corrupción | Estado de derecho, controles al ejecutivo, independencia judicial, corrupción (percepción y experiencia) | Expertos / encuesta | WJP, WGI, V-Dem, TI (CPI), INEGI (ENCIG) | 2 |
| Libertades | Libertad de prensa, agresiones contra periodistas, espacio cívico | Expertos / administrativo | RSF, V-Dem, Artículo 19 | 2 |
| Acción colectiva | Protestas y movilización social | Eventos codificados | ACLED (licencia), Mass Mobilization Project | 3 |
| Cambio institucional | Reformas constitucionales publicadas, creación o extinción de órganos, leyes aprobadas | Administrativo (DOF) | DOF, Cámara de Diputados | 3 |
| Polarización | Polarización política y social (expertos); polarización afectiva (encuestas) | Expertos / encuesta | V-Dem, LAPOP | 3 |

### `seg` · Seguridad y justicia

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Violencia letal | Homicidios (tasa), feminicidio, otros delitos contra la vida | Administrativo | INEGI, SESNSP, UNODC | 1 |
| Desapariciones | Personas desaparecidas y no localizadas | Administrativo (con controversia de registro) | RNPDNO | 2 |
| Delitos y victimización | Incidencia delictiva, prevalencia de victimización, cifra negra | Administrativo / encuesta | SESNSP, INEGI (ENVIPE) | 2 |
| Percepción | Percepción de inseguridad | Percepción | INEGI (ENSU, ENVIPE) | 1 |
| Justicia | Impunidad, prisión preventiva, personas privadas de la libertad sin sentencia | Administrativo | INEGI (censos de gobierno), México Evalúa | 3 |
| Capacidades y gasto | Gasto en seguridad, elementos por habitante, participación de las fuerzas armadas en seguridad pública | Administrativo | SHCP, INEGI (censos de gobierno) | 3 |
| Violencia organizada | Eventos de violencia organizada | Eventos codificados | UCDP, ACLED | 3 |

### `ene` · Energía, ambiente y recursos

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Oferta y consumo | Consumo de energía per cápita, intensidad energética | Administrativo | Energy Institute (Statistical Review), SENER | 2 |
| Hidrocarburos | Producción de petróleo y gas, importaciones de combustibles y gas natural | Administrativo | SENER, Pemex, EIA (EE.UU.) | 2 |
| Electricidad y transición | Generación por fuente, participación de renovables | Administrativo | Ember, SENER | 2 |
| Emisiones y clima | Emisiones de GEI totales y per cápita, anomalía de temperatura, sequía | Modelada / administrativo | EDGAR, Global Carbon Project, INECC, CONAGUA | 2–3 |
| Agua y suelo | Disponibilidad de agua, deforestación | Administrativo / satelital | CONAGUA, Global Forest Watch | 3 |

### `tec` · Ciencia, tecnología y digitalización

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Investigación y desarrollo | Gasto en I+D/PIB, investigadores por millón de habitantes | Administrativo | UNESCO-UIS, OCDE, INEGI | 2 |
| Innovación | Solicitudes de patentes por residentes | Administrativo | OMPI (WIPO), IMPI | 3 |
| Digitalización | Usuarios de internet, banda ancha, pagos digitales | Encuesta / administrativo | INEGI (ENDUTIH), UIT, Banxico | 2 |
| Inteligencia artificial | Inversión, talento y adopción de IA | Mixto | Stanford AI Index, OCDE.AI | 3 |

### `int` · Inserción internacional y geopolítica

| Subdimensión | Indicadores iniciales | Tipo | Fuentes | Fase |
|---|---|---|---|---|
| Comercio por socio | Exportaciones e importaciones por socio y producto; participación de México en las importaciones de EE.UU. | Administrativo | INEGI, US Census, UN Comtrade | 2 |
| Inversión y flujos financieros | IED por país de origen, remesas por origen | Administrativo | Secretaría de Economía, Banxico | 2 |
| Cadenas de valor | Valor agregado extranjero en las exportaciones | Modelada | OCDE (TiVA) | 3 |
| Relación México–EE.UU. | Comercio, migración, remesas, aranceles, revisión del T-MEC | Mixto | Fuentes anteriores + eventos | 2 |
| ALC–China / ALC–Europa | Comercio, préstamos e inversión de origen chino y europeo | Administrativo / compilación | UN Comtrade, Boston University (préstamos chinos), CEPAL | 3 |
| Alineamiento diplomático | Votaciones en la Asamblea General de la ONU | Administrativo | UNGA Voting Data (Voeten et al.) | 3 |
| Seguridad internacional | Gasto militar, transferencias de armas, conflictos | Administrativo / compilación | SIPRI, UCDP | 2–3 |
| Peso en el mundo | Participación en el PIB mundial (PPA y tipo de cambio de mercado), en la población y en el comercio | Cuentas nacionales | FMI, Banco Mundial | 2 |

### `meta` · Calidad y capacidad estadística

| Subdimensión | Indicadores iniciales | Fuentes | Fase |
|---|---|---|---|
| Capacidad estadística | Statistical Performance Indicators | Banco Mundial | 1 |
| Apertura de datos | Open Data Inventory (ODIN) | Open Data Watch | 2 |
| Cobertura de registros | Cobertura del registro de defunciones, año del último censo | OMS, UNSD | 2 |

### Dataset de eventos (no es un indicador)

Tipos iniciales: elecciones · cambios de gobierno · crisis económicas (con criterio
explícito, p. ej., la base de crisis bancarias de Laeven y Valencia) · reformas
constitucionales y legales relevantes (publicadas en el DOF) · cambios institucionales
(creación o extinción de órganos) · choques externos (pandemia, crisis financieras globales,
cambios de política comercial) · desastres naturales mayores · **cambios metodológicos de las fuentes**.

Cada evento tiene fecha, alcance geográfico, descripción factual (sin adjetivos), fuente
y criterio de inclusión. Los criterios se escriben antes de poblar la lista.

## 4. Esquema de la ficha de indicador (borrador)

```yaml
id: seg.violencia_letal.homicidio.tasa
nombre: Tasa de homicidios por 100 mil habitantes
concepto: seg.violencia_letal.homicidio
definicion: >
  Número de víctimas de homicidio intencional en el periodo, por cada 100 mil
  habitantes. El numerador depende de la serie (ver notas).
unidad: por 100 mil habitantes
facetas:
  tipo_medicion: administrativo
  cadena: resultado
  ritmo: intermedio
  direccion_normativa: menos_es_mejor
  cobertura: [mundo, nacional, estatal, municipal]
series:
  - id: inegi_defunciones:homicidio
    rol: principal_historica          # serie larga y basada en certificados
  - id: sesnsp_idefc:homicidio_doloso_victimas
    rol: oportuna                     # mensual, con menor rezago
  - id: unodc:intentional_homicide
    rol: comparacion_internacional
derivacion:
  receta: tasa_por_poblacion@1
  parametros: {escala: 100000, poblacion: dem.poblacion.total.conapo}
rangos_validos: {min: 0, max: 300}
rupturas_conocidas:
  - serie: sesnsp_idefc:homicidio_doloso_victimas
    fecha: 2015-01
    descripcion: Nueva metodología de registro; no empalmar con la serie 1997–2017.
notas_interpretacion: >
  INEGI y SESNSP difieren por diseño (fuente del registro, momento de registro,
  criterios de clasificación). Ver discrepancia DIS-001.
preguntas: [D1, D2]
fecha_alta: 2026-10-03
```
