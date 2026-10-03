# 05 · Fuentes de datos

## 1. Cómo evaluamos una fuente

Que una fuente sea conocida no garantiza que su dato sea correcto. Cada fuente recibe una
**ficha de evaluación cualitativa** (no un puntaje) con estos criterios:

| Criterio | Pregunta |
|---|---|
| Mandato y autoridad | ¿Quién la produce y con qué mandato legal o institucional? |
| Metodología | ¿Está publicada y es suficiente para entender qué se mide? |
| Revisiones | ¿Tiene una política de revisiones? ¿Publica versiones anteriores? |
| Continuidad | ¿Hay rupturas? ¿Riesgo de que se descontinúe (financiamiento, cambios institucionales)? |
| Independencia | ¿Qué tan expuesta está a presiones de quien es medido? ¿Ha cambiado su gobernanza? |
| Cobertura | ¿Qué países, periodos y poblaciones cubre? ¿Qué queda fuera? |
| Comparabilidad | ¿Armoniza definiciones entre países o compila definiciones nacionales? |
| Acceso | ¿API, descarga masiva, archivos manuales? ¿Requiere registro o token? |
| Licencia | ¿Qué permite publicar y redistribuir? |
| Oportunidad | ¿Con cuánto rezago publica? ¿Tiene un calendario de publicación? |
| Fuente primaria o compiladora | ¿Produce el dato o lo recopila de otros? Si lo recopila, ¿de dónde? |

**Regla:** preferimos la fuente primaria. Si usamos una compiladora (Our World in Data,
WDI en muchos indicadores, CEPALSTAT en algunos), registramos tanto la compiladora como la fuente original.

## 2. Ficha de catálogo de un dataset (esquema)

Incluye todos los campos solicitados (fuente, URL, fecha de consulta, periodo, frecuencia,
unidad, metodología, población cubierta, revisiones, limitaciones, transformación, versión),
más los necesarios para operar el pipeline:

```yaml
# Ejemplo ilustrativo: los valores se verificarán al crear el catálogo (etapa 4).
id: wb_wdi
nombre: World Development Indicators
fuente: banco_mundial                  # → catalog/sources/banco_mundial.yaml
url: https://datacatalog.worldbank.org/search/dataset/0037712/World-Development-Indicators
acceso:
  metodo: api                          # api | descarga_masiva | manual
  endpoint: https://api.worldbank.org/v2/
  credenciales: ninguna                # o nombre de variable de entorno, p. ej. INEGI_TOKEN
  formato: json
licencia:
  nombre: CC BY 4.0
  url: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets
  redistribucion: permitida_con_atribucion
cobertura:
  geografica: 217 economías + agregados
  temporal: "1960–"
  poblacion: varía por indicador
frecuencia: anual
rezago_tipico_dias: 365
calendario: actualizaciones varias veces al año (sin fecha fija)
version_fuente: se registra en cada vintage (campo "lastupdated" de la API)
metodologia: https://datahelpdesk.worldbank.org/knowledgebase/topics/19286-world-development-indicators-wdi
revisiones: >
  Las series se revisan retroactivamente; los niveles en PPA cambian con cada
  ronda del ICP (2021 adoptada en 2024).
rupturas_conocidas: []
limitaciones: >
  Compila datos de agencias nacionales e internacionales; definiciones no siempre
  homogéneas; huecos en países con baja capacidad estadística.
evaluacion: catalog/sources/banco_mundial.yaml#evaluacion
fecha_alta: 2026-10-03
```

La **fecha de consulta**, el hash y la versión declarada por la fuente no van en la ficha:
se registran en el manifiesto de cada *vintage* (cada descarga), porque cambian en cada actualización.

## 3. Fuentes de la fase 1

Agrupadas por el dashboard que alimentan (ver [09 · Dashboards](09-dashboards-iniciales.md)).

### Fase 1a · Comparación internacional de largo plazo (D1)

| Fuente | Qué aporta | Acceso | Frecuencia | Limitaciones a tener en cuenta |
|---|---|---|---|---|
| **Banco Mundial · WDI** | Base comparativa: PIB, población, salud, educación, empleo | API v2 / descarga masiva | Varias veces al año | Compilación; huecos; PPA revisadas en 2024 (ICP 2021). |
| **Banco Mundial · PIP** | Pobreza y desigualdad comparables entre países | API | Varias veces al año | Mezcla encuestas de ingreso y de consumo; nuevas líneas desde junio de 2025 (US$3.00 / 4.20 / 8.30, PPA 2021). |
| **FMI · World Economic Outlook** | Macroeconomía + **pronósticos** (abril y octubre) | Nuevo portal SDMX (`api.imf.org`); la API heredada se retiró en noviembre de 2025 | Semestral | Archivar cada edición para evaluar pronósticos; las cifras de los años recientes son estimaciones. |
| **ONU · World Population Prospects 2024** | Población, estructura por edad, fecundidad, mortalidad, **proyecciones probabilísticas** (intervalos del 80 % y del 95 %) | Descarga masiva CSV | Cada ~2 años | Estimaciones modeladas; pueden diferir de CONAPO e INEGI. |
| **Maddison Project Database** | PIB per cápita de muy largo plazo | Descarga (Excel/Stata) | Irregular (última edición: 2023) | Los años antiguos son reconstrucciones con mucha incertidumbre. |
| **Banco Mundial · SPI** | Capacidad estadística (metadato de confianza) | API / descarga | Anual | Indicador compuesto; úsese como contexto, no como juicio. |

### Fase 1b · Pulso de México (D2)

| Fuente | Qué aporta | Acceso | Frecuencia | Limitaciones |
|---|---|---|---|---|
| **INEGI · Banco de Información Económica / Banco de Indicadores** | PIB, IGAE, INPC, ENOE y cientos de series | API (token gratuito) | Mensual / trimestral | Cambios de base; cifras preliminares; series desestacionalizadas revisadas cada mes. |
| **Banxico · SIE** | Tipo de cambio, tasas, remesas, balanza de pagos, encuesta de expectativas | API REST (token gratuito) | Diaria a trimestral | Revisiones en la balanza de pagos. |
| **IMSS · datos abiertos** | Empleo formal registrado y salario base de cotización | Descarga mensual | Mensual | Mide solo el empleo afiliado al IMSS (no el total); cambios regulatorios (p. ej., reforma de subcontratación de 2021) afectan la serie. |
| **SHCP · Estadísticas oportunas de finanzas públicas** | Ingresos, gasto, balance, RFSP, deuda | Datos abiertos | Mensual / trimestral | Definiciones amplias vs estrechas del déficit; elegir y documentar. |
| **SESNSP · Incidencia delictiva** | Víctimas y carpetas por delito, entidad y municipio | Datos abiertos (CSV) | Mensual | Registro administrativo de fiscalías; metodología nueva desde 2015; subregistro (cifra negra). |
| **INEGI · Defunciones registradas** | Homicidios desde 1990 (certificados de defunción) | Datos abiertos / microdatos | Anual (rezago de varios meses) | Clasificación por causa; diferencias entre año de ocurrencia y de registro. |
| **INEGI · ENSU** | Percepción de inseguridad en ciudades | Datos abiertos | Trimestral | Solo zonas urbanas; mide percepción, no incidencia. |
| **INEGI · Pobreza multidimensional** | Pobreza oficial (bienal) | Datos abiertos | Bienal | Transición institucional desde CONEVAL (2025): verificar continuidad metodológica. |

### Fase 1c · Instituciones y democracia (D3)

| Fuente | Qué aporta | Acceso | Frecuencia | Limitaciones |
|---|---|---|---|---|
| **V-Dem (v16, marzo de 2026)** | Índices de democracia y cientos de indicadores, **con intervalos de credibilidad**, desde 1789 | Descarga (CSV/R/Stata) | Anual (marzo) | Juicio experto agregado; revisiones retroactivas entre versiones; debate metodológico sobre la medición del retroceso democrático. |
| **Freedom House · Freedom in the World** | Derechos políticos y libertades civiles | Descarga (Excel) | Anual | Escala ordinal gruesa; metodología y financiamiento propios (vigilar continuidad). |
| **International IDEA · Global State of Democracy** | Índices con intervalos de confianza | Descarga | Anual | Parcialmente construido con insumos similares a los de V-Dem: no es del todo independiente. |
| **Banco Mundial · WGI** | Gobernanza (seis dimensiones) con errores estándar | Descarga | Anual | Agregado de percepciones de múltiples fuentes. |
| **CEPALSTAT** | Indicadores sociales armonizados para ALC (pobreza según CEPAL, gasto social) | API | Variable | Metodología CEPAL distinta de las oficiales nacionales. |

## 4. Fuentes de las fases 2 y 3 (resumen)

| Dimensión | Fuentes |
|---|---|
| Elecciones y representación | INE (resultados y cómputos; Atlas de resultados electorales federales), OPLE, IDEA (Voter Turnout), IPU Parline, CLEA, organismos electorales nacionales de ALC |
| Opinión pública | Executive Approval Database, encuestas publicadas en México (agregadas con modelo), Latinobarómetro (registro), LAPOP (registro) |
| Desigualdad y bienestar | INEGI (ENIGH, microdatos), SEDLAC (CEDLAS–Banco Mundial), WID.world, UNESCO-UIS, OMS (GHO), OCDE (PISA), CEEY (movilidad social) |
| Seguridad | RNPDNO, ENVIPE, UNODC, censos de gobierno de INEGI, UCDP, ACLED (licencia) |
| Economía | Penn World Table, INEGI KLEMS, OCDE, OIT (ILOSTAT, SDMX), CONASAMI, Growth Lab (Harvard) |
| Energía y ambiente | SENER, Pemex, Ember, Energy Institute, EIA (EE.UU.), EDGAR, Global Carbon Project, INECC, CONAGUA |
| Inserción internacional | UN Comtrade, US Census (comercio), Secretaría de Economía (IED), OCDE TiVA, SIPRI, UNGA Voting Data, Boston University (préstamos chinos) |
| Historia económica | MOxLAD (Montevideo-Oxford), Clio-Infra, INEGI (Estadísticas históricas de México), base de crisis bancarias de Laeven y Valencia |
| Geografía | INEGI (Marco Geoestadístico), Natural Earth, geoBoundaries |

## 5. Fuentes con restricciones de acceso o licencia

| Fuente | Restricción | Implicación |
|---|---|---|
| **ACLED** | El acceso abierto gratuito ofrece datos agregados; los datos por evento requieren un nivel de acceso de investigación (con un rezago de 12 meses) o licencias pagadas; los términos limitan la redistribución. | Usar agregados permitidos; considerar UCDP (CC BY) como alternativa abierta para violencia organizada. |
| **Latinobarómetro / LAPOP** | Registro; términos de uso. | Publicar solo estimaciones agregadas, citando la fuente. |
| **IHME (GBD)** | Licencia no comercial; registro. | Usar si la licencia es compatible con el sitio. |
| **EIU Democracy Index** | Derechos de autor. | Citar resultados publicados; no redistribuir la base. |
| **UN Comtrade** | Clave de API y cuotas. | Descargas incrementales; caché. |
| **GADM** | Uso no comercial. | Preferir INEGI, Natural Earth o geoBoundaries. |

La licencia de cada dataset queda en el catálogo, y un control automático bloquea la
publicación de datos cuya licencia no lo permite.

## 6. Pares de fuentes que contrastaremos desde el inicio

Estas comparaciones alimentan el **registro de discrepancias**. La hipótesis sobre la causa
se escribe antes y se verifica con los datos.

| Concepto | Fuentes | Causas esperadas de diferencia |
|---|---|---|
| Homicidios | INEGI · SESNSP · UNODC | Fuente del registro (certificado médico vs fiscalía), momento de registro, criterios de clasificación, unidad (víctimas vs carpetas). |
| Pobreza | Oficial de México · Banco Mundial (PIP) · CEPAL | Definición (multidimensional vs monetaria), líneas, escalas de equivalencia, ajuste a cuentas nacionales. |
| Desigualdad | ENIGH / SEDLAC · WID | Cobertura de ingresos altos (encuesta vs datos fiscales y cuentas nacionales). |
| PIB per cápita (PPA) | WDI · FMI WEO · Maddison · Penn World Table | Ronda de PPA, año base, métodos de extrapolación. |
| Población | CONAPO · ONU WPP · INEGI (censo) | Supuestos de migración y mortalidad, conciliación demográfica. |
| Democracia | V-Dem · Freedom House · IDEA · EIU | Concepto de democracia, codificadores, agregación, escala. |
| Desempleo | INEGI (ENOE) · OIT (estimaciones modeladas) | Ajustes de armonización internacional. |
