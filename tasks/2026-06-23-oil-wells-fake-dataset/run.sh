#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Prefer the repo venv if it exists.
PY="python3"
if [ -x "../../.venv/bin/python" ]; then PY="../../.venv/bin/python"; fi

"$PY" main.py --output-dir output --basename OilWells --seed 20260610 "$@"
