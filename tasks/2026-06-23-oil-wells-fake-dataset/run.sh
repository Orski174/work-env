#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Prefer the repo venv if it exists.
PY="python3"
if [ -x "../../.venv/bin/python" ]; then PY="../../.venv/bin/python"; fi

"$PY" main.py --output-dir output --basename OilWells --seed 20260610 \
  --regions iraq,lebanon --lebanon-count 12 --lebanon-seed 20260711 \
  --with-production --production-well IQ-OW-001 --production-basename OilWellProduction \
  "$@"
