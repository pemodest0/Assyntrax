#!/usr/bin/env bash
set -euo pipefail

SRC="results/latest"
DST="website/public/data/latest"

mkdir -p "$DST"
cp -R "$SRC/"* "$DST/"
echo "Synced $SRC -> $DST"
