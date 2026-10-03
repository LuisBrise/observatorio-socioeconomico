# Registro de decisiones

Las decisiones de arquitectura se documentan aquí como registros breves (formato ADR).
Estado: **Propuesta** → **Aceptada** / **Rechazada** / **Sustituida por D-xxx**.

| ID | Decisión | Estado | Referencia |
|---|---|---|---|
| D-001 | Toda afirmación publicada lleva su nivel epistémico (DATO / ANÁLISIS / INTERPRETACIÓN; las opiniones solo se publican atribuidas a un actor). | Propuesta | [Principios editoriales](../principios-editoriales.md) |
| D-002 | Modelo de catálogo concepto → indicador → serie, con facetas. | Propuesta | [03 · Taxonomía](../diseno/03-taxonomia.md) |
| D-003 | Python + Polars + DuckDB + Parquet como base de datos y procesamiento; R como complemento opcional. | Propuesta | [04 · Stack](../diseno/04-stack.md) |
| D-004 | Quarto como capa de publicación; Observable Plot/D3 en módulos JS portables. | Propuesta | [04 · Stack](../diseno/04-stack.md) |
| D-005 | Datos crudos inmutables por *vintage*, archivados por hash en almacenamiento de objetos; `vintages.lock.yaml` en git. | Propuesta | [06 · Pipeline](../diseno/06-pipeline-y-validacion.md) |
| D-006 | No construir un índice compuesto de "cómo va México"; panel multidimensional. | Propuesta | [09 · Dashboards](../diseno/09-dashboards-iniciales.md) |
| D-007 | Agregados regionales como distribución + cobertura explícita; grupos de comparación definidos por regla y versionados. | Propuesta | [08 · Marco analítico](../diseno/08-marco-analitico.md) |
| D-008 | Orquestación ligera (CLI + `just` + GitHub Actions), con ruta de migración a Dagster. | Propuesta | [04 · Stack](../diseno/04-stack.md) |
| D-009 | Vocabulario de prospectiva: proyección / pronóstico / escenario / riesgo, con codificación visual distinta. | Propuesta | [Principios editoriales](../principios-editoriales.md) |
| D-010 | Linaje a nivel de indicador con registro propio (no dbt). | Propuesta | [04 · Stack](../diseno/04-stack.md) |

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
