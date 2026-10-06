# Observatorio socioeconómico y político

Sistema reproducible para analizar la evolución política, económica y social de
**México**, **América Latina y el Caribe** y **el mundo**: pasado, presente y escenarios futuros.

> **Estado:** pipeline completo con datos reales de seis fuentes (Banco Mundial WDI y PIP, FMI WEO,
> proyecciones probabilísticas de ONU WPP 2024, medición oficial de pobreza y defunciones por homicidio de INEGI, CEPAL, WID, SESNSP y el registro de personas desaparecidas), validación, revisión de atípicos, comparación entre
> fuentes y dashboard D1 en Quarto (ingreso, contraste internacional, transición demográfica, pobreza
> y desigualdad) y primera parte de D4 (homicidios en México, ALC y regiones del mundo; INEGI vs SESNSP; mujeres asesinadas y feminicidio;
> personas desaparecidas).
> Aún no se ha publicado el sitio.

## Uso rápido (Ubuntu)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # una vez: instala uv
make setup        # dependencias
make check        # lint + pruebas + validación del catálogo
make update       # descarga WDI, valida y fija la versión si está limpia
uv run obs run fmi_weo   # FMI WEO (solo tras sus ediciones de abril y octubre)
make comparar     # compara fuentes independientes del mismo indicador
make viz          # construye los datasets de las gráficas
make preview      # vista previa del sitio (requiere Quarto: https://quarto.org)
```

Los datos quedan en `data/` (no se versiona). `data/raw/` nunca se modifica: cada descarga distinta
es una versión nueva. Los tokens de API van en `.env` (ver [guía](docs/guias/tokens-api.md)).

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
| 1 | Diseñar la arquitectura | ✅ Aceptada |
| 2 | Elegir el stack | ✅ Aceptado |
| 3 | Crear la estructura del proyecto | ✅ |
| 4 | Crear el catálogo de datos | ✅ Esquemas + primeras fichas (WDI) |
| 5 | Seleccionar los primeros datasets | ✅ `docs/diseno/05-fuentes.md` |
| 6 | Descargar e ingerir datos | ✅ WDI y FMI WEO con datos reales |
| 7 | Construir el pipeline | ✅ Primera versión, probada |
| 8 | Validar los datos | ✅ Controles, revisión de atípicos y comparación entre fuentes |
| 9 | Primer análisis | 🟡 WDI vs WEO (`analyses/`) |
| 10 | Primeras visualizaciones y sistema visual | ✅ Tokens + 3 componentes (incluye abanico de proyección) |
| 11 | Primer dashboard | 🟡 D1 en construcción |
| 12–13 | Revisar y mejorar | ⏳ |
| 14 | Automatizar la actualización | 🟡 Flujos de trabajo escritos, sin probar en GitHub |
| 15 | Documentar | En curso desde la etapa 1 |

## Documentación

- [Diseño (fase 0)](docs/diseno/README.md)
- [Principios editoriales](docs/principios-editoriales.md)
- [Registro de decisiones](docs/decisiones/README.md)
- [Guía de tokens de API](docs/guias/tokens-api.md)

## Licencias

Código: MIT. Contenido y datos derivados: CC BY 4.0, salvo restricciones de cada fuente
(registradas en el catálogo). El proyecto no se monetiza.
