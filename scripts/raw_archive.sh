#!/usr/bin/env bash
# Archivo de datos crudos con costo cero: un release de GitHub ("raw-archive") cuyos
# assets son vintages comprimidos e inmutables: {fuente}__{dataset}__{vintage}.tar.gz
#   scripts/raw_archive.sh restore   # descarga y extrae todos los vintages en data/raw
#   scripts/raw_archive.sh upload    # sube los vintages locales que aún no están archivados
# Requiere `gh` autenticado (GH_TOKEN en CI).
set -euo pipefail
TAG=raw-archive
RAW=${OBS_DATA_DIR:-data}/raw
mode=${1:?uso: raw_archive.sh restore|upload}

case "$mode" in
  restore)
    if ! gh release view "$TAG" >/dev/null 2>&1; then
      echo "Aún no existe el release $TAG: nada que restaurar."; exit 0
    fi
    tmp=$(mktemp -d)
    gh release download "$TAG" --dir "$tmp" --pattern '*.tar.gz' || true
    mkdir -p "$RAW"
    for f in "$tmp"/*.tar.gz; do
      if [ -e "$f" ]; then tar -xzf "$f" -C "$RAW"; fi
    done
    ;;
  upload)
    gh release view "$TAG" >/dev/null 2>&1 || \
      gh release create "$TAG" --title "Archivo de datos crudos" \
        --notes "Vintages crudos inmutables. Ver docs/diseno/06-pipeline-y-validacion.md" >/dev/null
    existing=$(gh release view "$TAG" --json assets -q '.assets[].name')
    find "$RAW" -mindepth 3 -maxdepth 3 -type d ! -name '*.partial' | while read -r dir; do
      rel=${dir#"$RAW"/}
      name="${rel//\//__}.tar.gz"
      if ! grep -qx "$name" <<<"$existing"; then
        tar -czf "/tmp/$name" -C "$RAW" "$rel"
        gh release upload "$TAG" "/tmp/$name"
        echo "archivado: $name"
      fi
    done
    ;;
esac
