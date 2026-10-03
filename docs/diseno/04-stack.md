# 04 · Stack tecnológico

## 1. Criterios

En orden de importancia para este proyecto:

1. **Reproducibilidad y trazabilidad.** Todo debe ser código y texto versionable.
2. **Mantenibilidad por una o dos personas durante años.** Pocas piezas, herramientas con comunidad amplia y formatos abiertos.
3. **Calidad de la visualización narrativa.** Control fino del diseño, anotaciones e interactividad.
4. **Costo.** Cercano a cero en las fases iniciales.
5. **Automatización.** Actualizaciones programadas sin intervención manual.
6. **Escalabilidad suficiente.** Decenas de millones de observaciones, no miles de millones.

## 2. Comparación por capa

### Lenguaje principal

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **Python** | Ecosistema de ingesta (HTTP, SDMX, APIs), ingeniería de datos (DuckDB, Polars), pruebas, CLI; amplio uso fuera de la academia. | Algunos métodos estadísticos especializados están más maduros en R. | **Principal** |
| **R** | Estadística (paquete `survey` para microdatos con diseño muestral complejo, `fable`), tidyverse, excelente para análisis académico. | Más débil para ingeniería de pipelines y conectores. | **Complementario** para módulos específicos (p. ej., microdatos ENIGH con diseño muestral). Se comunica con Python mediante Parquet. |

### Motor y almacenamiento

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **Parquet** | Columnar, comprimido, tipado, abierto; lo leen Python, R, DuckDB y el navegador. | No es una base de datos por sí sola. | **Formato de almacenamiento** |
| **DuckDB** | Motor analítico embebido, sin servidor, muy rápido, SQL sobre Parquet; también corre en el navegador (DuckDB-WASM). | No está pensado para muchos escritores concurrentes. | **Motor de consulta** |
| PostgreSQL | Robusto, concurrente, extensible. | Requiere servidor, respaldos y administración; más lento para análisis columnar; no lo necesitamos. | Descartado por ahora (reconsiderar si hay edición colaborativa en tiempo real). |
| DuckLake / Iceberg | Versionado nativo (instantáneas) sobre Parquet. | DuckLake es joven (2025); Iceberg es excesivo para esta escala. | Vigilar: DuckLake podría sustituir parte de nuestro manejo de *vintages* más adelante. |

### DataFrames

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **Polars** | Rápido, tipado estricto, API consistente, evaluación diferida. | Algunas librerías estadísticas esperan pandas. | **Principal** para transformaciones |
| Pandas | Ubicuo; lo requieren statsmodels y otras librerías. | Tipos laxos, índices implícitos, más propenso a errores silenciosos. | Solo en la frontera con librerías que lo requieran. |

### Orquestación

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **CLI propia (Typer) + `make` + GitHub Actions** | Mínima, transparente, gratuita, suficiente para un DAG simple. | Sin interfaz gráfica de linaje; la incrementalidad se programa a mano. | **Fase 1** |
| Dagster | Activos de datos, linaje, interfaz, programación. | Más piezas que operar; curva de aprendizaje. | Ruta de migración si superamos ~30 fuentes. |
| Prefect / Airflow | Maduros. | Pensados para equipos e infraestructura propia. | Descartados. |
| dbt / SQLMesh | Linaje, documentación y pruebas para transformaciones SQL. | El linaje es a nivel de tabla; necesitamos linaje a nivel de **indicador** (filas). Las transformaciones estadísticas son mejores en Python. | Descartados por ahora. |

### Validación

| Opción | Veredicto |
|---|---|
| **Pandera** (compatible con Polars) | Esquemas de DataFrames: tipos, nulos, rangos, unicidad. |
| **Controles propios** | Revisiones, rupturas, cambios de unidad, discrepancias entre fuentes: lógica específica del dominio que ninguna librería trae. |
| Great Expectations | Potente pero pesado; su valor principal (documentación y reportes) lo cubrimos con nuestros reportes. Descartado. |

### Exploración

| Opción | Veredicto |
|---|---|
| **marimo** | Notebooks reactivos guardados como `.py`: diffs limpios en git, sin estados ocultos. **Recomendado para exploración.** |
| Jupyter | Válido; se exigen salidas limpias (`nbstripout`). |
| Quarto (`.qmd`) | Para análisis que se convierten en notas metodológicas o informes. |

### Visualización

| Opción | A favor | En contra | Uso |
|---|---|---|---|
| **Observable Plot** | Gramática concisa, excelente para anotaciones, *small multiples* (facetas) y series de tiempo; mismo autor que D3. | JavaScript. | **Gráficas publicadas** |
| **D3.js** | Control total (redes, diseños a la medida, transiciones). | Verboso; más código que mantener. | Piezas a la medida (redes, líneas de tiempo complejas). |
| Altair / Vega-Lite | Declarativo, en Python, especificaciones JSON portables. | Anotaciones complejas y diseños a la medida son más difíciles. | Exploración y gráficas internas. |
| Plotly | Interactividad inmediata. | Estética difícil de controlar, archivos pesados, aspecto de "dashboard genérico". | No recomendado para publicación. |
| matplotlib | Estático, preciso. | Sin interactividad. | Figuras para PDF si hiciera falta. |

### Publicación

| Opción | A favor | En contra | Veredicto |
|---|---|---|---|
| **Quarto** | Respaldado por Posit; Python y R nativos; sitios web, informes HTML/PDF/Word, citas bibliográficas (BibTeX/CSL), referencias cruzadas, formato de dashboards, *scrollytelling* (extensión Closeread) y celdas Observable JS. Sitio estático. | Las celdas OJS son algo menos ergonómicas que un entorno JS dedicado. | **Recomendado** |
| Observable Framework | Excelente experiencia de desarrollo en JS, *data loaders* en cualquier lenguaje, DuckDB integrado, sitio estático. Mantenido (versión 1.13.4, marzo de 2026). | La comunidad ha expresado dudas sobre su futuro tras el lanzamiento de Observable Notebooks 2.0; no maneja citas ni informes PDF; ecosistema más pequeño. | **Alternativa viable**; nuestros componentes serán portables a Framework. |
| Streamlit / Dash / Shiny | Rápidos para prototipos interactivos. | Requieren servidor; estética genérica; difícil reproducir "qué se mostró en una fecha"; costo de hospedaje. | Descartados para publicación. Shiny o Streamlit podrían servir para un laboratorio interno de escenarios, pero los escenarios simples pueden correr en el navegador sin servidor. |
| Evidence.dev | "BI como código" con Markdown y SQL. | Componentes orientados a BI; menos control visual. | Descartado. |
| Tableau / Power BI | Rápidos para dashboards corporativos. | Licencias, dependencia del proveedor, control de versiones pobre, trazabilidad por interfaz gráfica, visualizaciones a la medida limitadas. | Descartados. |

## 3. Recomendación concreta

```text
Datos           Python 3.12 · uv (dependencias con lockfile) · httpx + tenacity (HTTP con reintentos)
                sdmx1 (fuentes SDMX: FMI, OCDE, OIT, BIS) · Polars · DuckDB · Parquet (zstd)
Catálogo        YAML + Pydantic (esquemas validados) · fichas generadas para el sitio
Validación      Pandera + módulo propio de controles de dominio
Análisis        statsmodels (ETS/ARIMA, STL) · ruptures (detección de cambios) · scipy
                R opcional (survey) para microdatos con diseño muestral complejo
Exploración     marimo (preferido) o Jupyter con nbstripout
Visualización   Observable Plot + D3 como módulos ES propios con tokens de diseño
                Altair para exploración
Publicación     Quarto (sitio web + informes) · Closeread (scrollytelling)
                DuckDB-WASM para la página de exploración libre
Orquestación    CLI `obs` (Typer) · Makefile · GitHub Actions (CI, actualizaciones, despliegue)
Calidad         pytest · hypothesis · ruff · pre-commit · pruebas de contrato de conectores
Hospedaje       GitHub Pages o Cloudflare Pages (sitio estático)
Archivo crudo   Release de GitHub "raw-archive": un asset inmutable por vintage (costo cero)
Publicaciones   Instantáneas periódicas citables en Zenodo (DOI), opcional
```

### Por qué esta combinación

- **Python + DuckDB + Parquet** cubren ingesta, procesamiento y análisis sin servidores, con
  formatos abiertos que seguirán legibles en diez años.
- **Quarto** une en una sola herramienta narrativa, código, citas, informes y sitio web; es la opción
  más estable a largo plazo para un observatorio analítico. Usar Observable Plot dentro de
  Quarto nos da la calidad visual que buscamos sin atarnos a un framework: los componentes
  son módulos JavaScript estándar que también funcionarían en Observable Framework o en
  cualquier sitio web.
- **GitHub Actions** ejecuta las actualizaciones programadas gratis en repositorios públicos
  y con una cuota mensual generosa en privados.
- **Linaje a nivel de indicador** con un registro propio, porque las herramientas genéricas
  (dbt, Dagster) registran linaje entre tablas, no entre indicadores.

### Costo estimado (fase 1)

| Concepto | Costo |
|---|---|
| Repositorio, CI, sitio (GitHub, repositorio público) | US$0 |
| Archivo de datos crudos (assets de un release de GitHub; límite de 2 GB por archivo) | US$0 |
| APIs (INEGI, Banxico, Banco Mundial, FMI, ONU) | US$0 (algunas requieren token gratuito) |
| Dominio propio | No se usará (decisión D-011: costo cero); el sitio vive en `github.io` |

### Riesgos del stack y mitigación

| Riesgo | Mitigación |
|---|---|
| Cambios incompatibles en Quarto u Observable Plot | Versiones fijadas; componentes con pruebas visuales (capturas comparadas). |
| La API de una fuente cambia (como la del FMI en 2025) | Conectores aislados, pruebas de contrato semanales, último dato válido. |
| Curva de JavaScript para los componentes | Biblioteca pequeña de componentes con documentación; las páginas solo los configuran. |
| Crecimiento más allá del DAG simple | Etapas diseñadas como funciones puras con entradas y salidas explícitas: migrables a activos de Dagster. |
