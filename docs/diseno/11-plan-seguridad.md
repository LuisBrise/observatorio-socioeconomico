# 11 · Plan: homicidios, feminicidios y desapariciones

Propuesto el 2026-10-06 a solicitud del usuario. Será el dashboard **D4 · Violencia letal y
desapariciones** (México, con comparación con ALC y otras regiones del mundo).

## Preguntas

1. ¿Cómo han evolucionado los homicidios en México desde 1990, y qué tan distinto se ven según la fuente?
2. ¿Cómo se compara la tasa de homicidios de México con ALC y con otras regiones del mundo?
3. ¿Qué sabemos —y qué no— sobre los feminicidios y los homicidios de mujeres?
4. ¿Cuántas personas están registradas como desaparecidas, y qué limita la interpretación de esa cifra?

## Fuentes (y su independencia)

| Concepto | Fuente | Qué mide | Acceso |
|---|---|---|---|
| Homicidio | INEGI, estadísticas de defunciones registradas | Defunciones por homicidio según el certificado de defunción (sector salud y registro civil), por año de ocurrencia o registro | ✅ inegi.org.mx (y API del Banco de Indicadores con token) |
| Homicidio | SESNSP, incidencia delictiva | Víctimas de homicidio doloso en carpetas de investigación de las fiscalías | ⛔ www.gob.mx / datos.gob.mx |
| Homicidio (internacional) | UNODC (vía WDI `VC.IHR.PSRC.P5`) | Homicidio intencional por 100 mil, compilación internacional | ✅ api.worldbank.org (redistribución; origen UNODC) |
| Homicidio (internacional) | UNODC directo | Ídem, con más detalle (sexo, mecanismo) | ⛔ dataunodc.un.org |
| Feminicidio | SESNSP | Víctimas del delito de feminicidio (tipo penal; su definición varía por entidad) | ⛔ www.gob.mx |
| Homicidios de mujeres | INEGI | Defunciones de mujeres por homicidio (no equivale a feminicidio) | ✅ inegi.org.mx |
| Desaparición | RNPDNO (Comisión Nacional de Búsqueda) | Personas desaparecidas y no localizadas registradas | ⛔ versionpublicarnpdno.segob.gob.mx |

## Retos metodológicos ya identificados

- **INEGI vs SESNSP** miden cosas distintas (certificado de defunción vs carpeta de investigación;
  momento de registro; clasificación). Se documentará como discrepancia (DIS) con su causa, sin
  elegir arbitrariamente.
- **Categorías vecinas:** el sistema vigilará también "otros delitos que atentan contra la vida" y
  las desapariciones, porque analistas han señalado posibles reclasificaciones.
- **Feminicidio** es un tipo penal cuya definición y aplicación varían por entidad y en el tiempo:
  su evolución mezcla cambios reales y de tipificación. Se mostrará junto con los homicidios de
  mujeres (INEGI), que tienen otra definición, y se explicará la diferencia.
- **Desapariciones:** el registro ha tenido cambios de criterios y depuraciones (2023–2024) que han
  sido objeto de controversia; cualquier serie del RNPDNO llevará esas advertencias y la fecha de corte.
- **Comparación internacional:** la cobertura y calidad del registro de defunciones varía mucho
  entre países; se usarán indicadores de capacidad estadística como metadato de confianza.
- **Ética:** solo agregados; lenguaje sobrio; las cifras representan personas.

## Orden propuesto

1. Homicidios: INEGI (México, 1990–) + UNODC vía WDI (comparación internacional). No requiere dominios nuevos.
2. Homicidios: SESNSP y discrepancia INEGI–SESNSP.
3. Feminicidios y homicidios de mujeres.
4. Desapariciones (RNPDNO).
