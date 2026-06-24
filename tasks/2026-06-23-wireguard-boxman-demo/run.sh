#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# On sc1 boxman lives in the conda env; prepend it so pytest's subprocess calls find it.
CONDA_BOXMAN="$HOME/.conda/envs/boxman/bin"
if [[ -d "$CONDA_BOXMAN" ]]; then
    export PATH="$CONDA_BOXMAN:$PATH"
fi

exec pytest -m integration test_wireguard_demo.py -v "$@"
