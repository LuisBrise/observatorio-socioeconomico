# Tareas del observatorio. `make help` lista las disponibles.
.PHONY: help setup test lint check update comparar viz site preview stop-preview clean-quarto clean-derived

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

comparar:  ## Compara fuentes que miden el mismo indicador
	uv run obs comparar

viz:  ## Construye los datasets de visualización
	uv run obs build-viz d1

site: viz  ## Construye el sitio (requiere Quarto)
	quarto render site

preview: viz  ## Vista previa local del sitio (Ctrl+C para detenerla)
	@if pgrep -f "[q]uarto.*preview" >/dev/null; then \
	  echo "Ya hay un 'quarto preview' en ejecución (bloquea el caché del proyecto)."; \
	  echo "Detenlo con Ctrl+C en su terminal, o con: make stop-preview"; exit 1; fi
	quarto preview site

stop-preview:  ## Detiene cualquier 'quarto preview' en ejecución
	-pkill -f "[q]uarto.*preview"

clean-quarto:  ## Borra el caché de Quarto (útil ante "database is locked")
	rm -rf site/.quarto site/_site

clean-derived:  ## Borra datos derivados (nunca toca data/raw)
	rm -rf data/staging data/processed data/analytical site/data
