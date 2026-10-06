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
| Homicidio | INEGI, estadísticas de defunciones registradas | Defunciones por homicidio según el certificado de defunción (sector salud y registro civil), por año de registro | ✅ servicio de tabulados de inegi.org.mx (2010–); 1990–2009 solo en el sistema de consulta, no automatizable |
| Homicidio | SESNSP, incidencia delictiva | Víctimas de homicidio doloso en carpetas de investigación de las fiscalías | ✅ ZIP en sspcgob-my.sharepoint.com, localizado por el texto del enlace en www.gob.mx |
| Homicidio (internacional) | UNODC (vía WDI `VC.IHR.PSRC.P5`) | Homicidio intencional por 100 mil, compilación internacional | ✅ api.worldbank.org (redistribución; origen UNODC) |
| Homicidio (internacional) | UNODC directo | Ídem, con más detalle (sexo, mecanismo) | ⛔ dataunodc.un.org (sin respuesta) |
| Feminicidio | SESNSP | Víctimas del delito de feminicidio (tipo penal; su definición varía por entidad) | ✅ mismo archivo |
| Homicidios de mujeres | INEGI | Defunciones de mujeres por homicidio (no equivale a feminicidio) | ✅ inegi.org.mx |
| Desaparición | RNPDNO (Comisión Nacional de Búsqueda) | Personas desaparecidas y no localizadas registradas | ✅ versionpublicarnpdno.segob.gob.mx (consultas JSON de la versión pública) |

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

1. ✅ Homicidios: INEGI (México, 2010–) + UNODC vía WDI (México 1990–, ALC y regiones del mundo).
   Hallazgo: para México, la tasa de UNODC es exactamente la de INEGI con la población de la ONU
   (D-023); no son fuentes independientes. Pendiente: entidades federativas (requiere geografías
   subnacionales en el catálogo).
2. ✅ Homicidios: SESNSP (víctimas 2015–2025, metodología 2015–2025) y discrepancia INEGI–SESNSP
   (DIS-003, abierta). Se vigila "otros delitos contra la vida" (3,692 → 17,110 víctimas, 2015–2025).
   Pendiente: serie 2026 con la nueva metodología del SESNSP, como tramo distinto (ruptura).
3. ✅ Feminicidios y homicidios de mujeres (INEGI vs SESNSP, proporción registrada como feminicidio).
3b. ✅ Entidades federativas (INEGI y SESNSP, conteos): diferencia entre registros por entidad y su
   asociación con "otros delitos contra la vida" (Spearman 0.32, IC 95 % −0.03 a 0.60: no concluyente).
   Pendiente: tasas por entidad (población de CONAPO: el archivo redirige a www.datos.gob.mx, que
   hay que permitir).
4b. ✅ Desapariciones por entidad (RNPDNO, una consulta por entidad, espaciadas). Detección automática
   de rezago de carga en el año en curso (Estado de México 2026).
4. ✅ Desapariciones (RNPDNO): instantánea semanal por año de desaparición y estatus (D-024). Se adelantó
   porque el SESNSP requiere permitir sspcgob-my.sharepoint.com. Pendiente: entidades federativas.
