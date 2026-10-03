# Observatorio socioeconómico y político

Sistema reproducible para analizar la evolución política, económica y social de
**México**, **América Latina y el Caribe** y **el mundo**: pasado, presente y escenarios futuros.

> **Estado: fase 0, diseño.** Todavía no hay código ni datos. La propuesta de arquitectura
> está en [`docs/diseno/`](docs/diseno/README.md) y espera validación.

## Principios

- **Separar DATO, ANÁLISIS, INTERPRETACIÓN y OPINIÓN.** El sistema informa; no persuade.
- **Trazabilidad completa:** gráfica → dataset → transformación → fuente original.
- **Reproducibilidad:** los datos crudos nunca se sobrescriben; cada publicación se puede reconstruir.
- **Neutralidad política verificable:** preguntas e indicadores definidos antes de ver los
  resultados; mismas reglas para todos los actores.
- **La incertidumbre se muestra** y las discrepancias entre fuentes se explican.

Ver [principios editoriales](docs/principios-editoriales.md).

## Hoja de ruta

| Etapa | Descripción | Estado |
|---|---|---|
| 1 | Diseñar la arquitectura | ✅ Propuesta (en revisión) |
| 2 | Elegir el stack | ✅ Propuesta (en revisión) |
| 3 | Crear la estructura del proyecto | ⏳ |
| 4 | Crear el catálogo de datos | ⏳ |
| 5 | Seleccionar los primeros datasets | Propuesta en `docs/diseno/05-fuentes.md` |
| 6 | Descargar e ingerir datos | ⏳ |
| 7 | Construir el pipeline | ⏳ |
| 8 | Validar los datos | ⏳ |
| 9 | Primer análisis | ⏳ |
| 10 | Primeras visualizaciones y sistema visual | ⏳ |
| 11 | Primer dashboard | ⏳ |
| 12–13 | Revisar y mejorar | ⏳ |
| 14 | Automatizar la actualización | ⏳ |
| 15 | Documentar | En curso desde la etapa 1 |

## Documentación

- [Diseño (fase 0)](docs/diseno/README.md)
- [Principios editoriales](docs/principios-editoriales.md)
- [Registro de decisiones](docs/decisiones/README.md)
