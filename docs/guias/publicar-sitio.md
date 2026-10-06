# Publicar el sitio en GitHub Pages (sin entorno local)

El sitio se construye y se publica con GitHub Actions; no hace falta tu computadora. Es gratis
porque el repositorio es público.

Dirección final: **https://luisbrise.github.io/observatorio-socioeconomico/**

## Cómo funciona

1. **«Actualizar datos»** (`.github/workflows/update-data.yml`) descarga las fuentes, valida, guarda
   los archivos crudos en el release `raw-archive` del repositorio y abre un pull request que
   actualiza `catalog/vintages.lock.yaml` (las versiones de datos que se publican).
2. Al integrar ese pull request en la rama principal, **«Publicar sitio»**
   (`.github/workflows/deploy-site.yml`) restaura los archivos crudos del release, reconstruye los
   datos fijados, genera las gráficas y publica el sitio.

## Configuración (una sola vez)

En GitHub, dentro del repositorio:

1. **Settings → Pages → Build and deployment → Source: «GitHub Actions».**
2. **Settings → Actions → General → Workflow permissions:** marca «Read and write permissions» y
   la casilla «Allow GitHub Actions to create and approve pull requests». Guarda.

## Primera publicación (arranque)

Los vintages fijados en el lockfile se descargaron en una sesión de trabajo y aún no están en el
release `raw-archive`, así que la primera vez hay que descargarlos todos en GitHub:

1. **Actions → «Actualizar datos» → «Run workflow»**, marca **«Descargar TODAS las fuentes…»** y
   ejecútalo en la rama principal. Tarda varios minutos (WID y el FMI son los más pesados).
2. Al terminar, aparece un pull request **«Actualización de datos»** con el reporte de validación.
   Revísalo: si algún dataset quedó «pendiente de revisión humana» (atípicos nuevos), no se fijó y
   hay que revisarlo antes de publicar (se puede hacer en una sesión con Claude).
3. Integra el pull request (**Merge**). Eso dispara «Publicar sitio».
4. En **Actions → «Publicar sitio»** verás el avance; al terminar, el enlace aparece en el resumen
   del job `deploy` y en **Settings → Pages**.

## Después

- «Actualizar datos» corre solo cada lunes y abre un pull request cuando hay datos nuevos. Cada vez
  que integras uno, el sitio se vuelve a publicar.
- Cualquier cambio integrado en la rama principal también vuelve a publicar el sitio.
- Si una publicación falla, el registro del job dice qué paso falló (por ejemplo, un vintage fijado
  que no está en el release).
