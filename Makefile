# Tareas del observatorio. `make help` lista las disponibles.
.PHONY: help setup test lint check update viz site preview clean-derived

help:  ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

setup:  ## Instala dependencias (requiere uv)
	uv sync

test:  ## Ejecuta las pruebas
	uv run pytest -q

lint:  ## Revisa estilo
	uv run ruff check .

check: lint test  ## Lint + pruebas + catálogo
	uv run obs catalog-check

update:  ## Descarga, valida y (si está limpio) fija WDI
	uv run obs run wb_wdi

viz:  ## Construye los datasets de visualización
	uv run obs build-viz d1

site: viz  ## Construye el sitio (requiere Quarto)
	quarto render site

preview: viz  ## Vista previa local del sitio
	quarto preview site

clean-derived:  ## Borra datos derivados (nunca toca data/raw)
	rm -rf data/staging data/processed data/analytical site/data
