#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "--yes" ]]; then
  echo "Dry-run. Re-run with --yes to delete:"
  echo "  api"
  echo "  dados"
  echo "  legado"
  echo "  results"
  echo "  website"
  echo "  venv"
  echo "  n sei c pode exluir"
  echo "  data/external"
  echo "  data/yfinance_cache"
  echo "  data/processed"
  echo "  author.png"
  exit 1
fi

rm -rf \
  api \
  dados \
  legado \
  results \
  website \
  venv \
  "n sei c pode exluir" \
  data/external \
  data/yfinance_cache \
  data/processed \
  author.png

if [[ -d data/raw/ONS/ons_carga_diaria ]]; then
  rm -f data/raw/ONS/ons_carga_diaria/CARGA_ENERGIA_*.csv
  rm -f data/raw/ONS/ons_carga_diaria/ons_carga_diaria_2016_2025.csv
fi

echo "Cleanup complete."
