# Observatorio socioeconómico y político

Sistema reproducible para analizar la evolución política, económica y social de
**México**, **América Latina y el Caribe** y **el mundo**: pasado, presente y escenarios futuros.

> **Estado: primera rebanada vertical.** El pipeline completo funciona de punta a punta con el
> Banco Mundial (WDI): ingesta → crudo inmutable → validación → datos procesados → dataset de
> visualización con procedencia → dashboard D1 en Quarto. Aún no se ha publicado con datos reales.

## Uso rápido (Ubuntu)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # una vez: instala uv
make setup        # dependencias
make check        # lint + pruebas + validación del catálogo
make update       # descarga WDI, valida y fija la versión si está limpia
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
| 6 | Descargar e ingerir datos | ✅ Conector WDI · ⏳ primera descarga real |
| 7 | Construir el pipeline | ✅ Primera versión, probada |
| 8 | Validar los datos | ✅ Controles automáticos · ⏳ revisión con datos reales |
| 9 | Primer análisis | ⏳ |
| 10 | Primeras visualizaciones y sistema visual | ✅ Tokens + 2 componentes |
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
