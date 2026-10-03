# Registro de decisiones

Las decisiones de arquitectura se documentan aquí como registros breves (formato ADR).
Estado: **Propuesta** → **Aceptada** / **Rechazada** / **Sustituida por D-xxx**.

| ID | Decisión | Estado | Referencia |
|---|---|---|---|
| D-001 | Toda afirmación publicada lleva su nivel epistémico (DATO / ANÁLISIS / INTERPRETACIÓN; las opiniones solo se publican atribuidas a un actor). | Aceptada (2026-10-03) | [Principios editoriales](../principios-editoriales.md) |
| D-002 | Modelo de catálogo concepto → indicador → serie, con facetas. | Aceptada (2026-10-03) | [03 · Taxonomía](../diseno/03-taxonomia.md) |
| D-003 | Python + Polars + DuckDB + Parquet como base de datos y procesamiento; R como complemento opcional. | Aceptada (2026-10-03) | [04 · Stack](../diseno/04-stack.md) |
| D-004 | Quarto como capa de publicación; Observable Plot/D3 en módulos JS portables. | Aceptada (2026-10-03) | [04 · Stack](../diseno/04-stack.md) |
| D-005 | Datos crudos inmutables por *vintage*, archivados como assets inmutables de un release de GitHub (ver D-011); `vintages.lock.yaml` en git. | Aceptada (2026-10-03) | [06 · Pipeline](../diseno/06-pipeline-y-validacion.md) |
| D-006 | No construir un índice compuesto de "cómo va México"; panel multidimensional. | Aceptada (2026-10-03) | [09 · Dashboards](../diseno/09-dashboards-iniciales.md) |
| D-007 | Agregados regionales como distribución + cobertura explícita; grupos de comparación definidos por regla y versionados. | Aceptada (2026-10-03) | [08 · Marco analítico](../diseno/08-marco-analitico.md) |
| D-008 | Orquestación ligera (CLI + `make` + GitHub Actions), con ruta de migración a Dagster. | Aceptada (2026-10-03) | [04 · Stack](../diseno/04-stack.md) |
| D-009 | Vocabulario de prospectiva: proyección / pronóstico / escenario / riesgo, con codificación visual distinta. | Aceptada (2026-10-03) | [Principios editoriales](../principios-editoriales.md) |
| D-010 | Linaje a nivel de indicador con registro propio (no dbt). | Aceptada (2026-10-03) | [04 · Stack](../diseno/04-stack.md) |
| D-011 | **Costo cero y sin ingresos.** Sin servicios de pago ni dominio propio; sitio en GitHub Pages; archivo crudo en un release de GitHub; instantáneas citables opcionales en Zenodo. El proyecto no se monetiza, como salvaguarda de imparcialidad. | Aceptada (2026-10-03) | [04 · Stack](../diseno/04-stack.md) |
| D-012 | Grupo `G.CONTRASTE` (China, Vietnam, Polonia, Chequia, Grecia, Portugal, Rusia, Suecia, Finlandia): países distintos de México, fuera del foco habitual; uso ocasional, nunca como pares. | Aceptada (2026-10-03) | [08 · Marco analítico](../diseno/08-marco-analitico.md) |
| D-013 | `Makefile` en lugar de `just` (viene instalado en Ubuntu). | Aceptada (2026-10-03) | [Makefile](../../Makefile) |
| D-014 | Referentes editoriales y visuales de distintas posturas políticas + prueba de simetría antes de publicar. | Aceptada (2026-10-03) | [Principios editoriales](../principios-editoriales.md) |
| D-016 | Verificación entre fuentes **independientes**: cada serie declara su `origen`; las discrepancias por encima de la tolerancia bloquean la validación cruzada hasta documentarse (`catalog/discrepancies/`). Mismo origen no cuenta como verificación. | Aceptada (2026-10-03) | [05 · Fuentes §6](../diseno/05-fuentes.md) |
| D-017 | Revisión de atípicos con cuatro resoluciones: `valor_real`, `dudoso`, `ruptura_metodologica`, `error_fuente`. Un `valor_real` (suceso documentado) se hereda entre series del mismo indicador; `dudoso` y `ruptura` no, y se advierten en las gráficas. Los pronósticos no se revisan como atípicos. | Aceptada (2026-10-03) | [06 · Pipeline §7](../diseno/06-pipeline-y-validacion.md) |
| D-018 | Proyecciones probabilísticas como series con `variante` (mediana, límites 80 % y 95 %): los límites no se validan como datos (sus colas extremas se informan) ni se comparan como fuentes alternativas. Empalme estimación→proyección en el último año estimado por la fuente (WPP 2024: 2023), no en el último año publicado por quien la redistribuye. Precisión limitada (valores truncados) se reporta como tramo, no como punto. | Aceptada (2026-10-03) | [Pipeline](../../src/observatorio/viz_data/d1.py) |
| D-015 | Foco visual (México) en violeta y comparador en ocre: colores no asociados a partidos mexicanos; paleta validada para daltonismo y contraste en modo claro y oscuro. | Aceptada (2026-10-03) | [Tokens](../../site/styles/tokens.css) |

## Plantilla

```markdown
# D-xxx · Título

- Estado: Propuesta | Aceptada | Rechazada | Sustituida por D-yyy
- Fecha: AAAA-MM-DD

## Contexto
¿Qué problema o tensión motiva la decisión?

## Decisión
¿Qué decidimos?

## Alternativas consideradas
¿Qué otras opciones evaluamos y por qué no las elegimos?

## Consecuencias
¿Qué se vuelve más fácil, qué se vuelve más difícil, qué tendremos que vigilar?
```
