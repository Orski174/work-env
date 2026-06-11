#!/usr/bin/env bash
# Shared helpers sourced by other scripts. Not meant to be run directly.

# Resolve repo root from this file's location (robust to where it's called from).
WORK_ENV_ROOT="${WORK_ENV_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Load .env if present (without clobbering already-exported vars).
if [ -f "$WORK_ENV_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$WORK_ENV_ROOT/.env"
  set +a
fi

# Defaults derived from the repo root.
DATA_ROOT="${DATA_ROOT:-$WORK_ENV_ROOT/data}"
OUTPUTS_ROOT="${OUTPUTS_ROOT:-$WORK_ENV_ROOT/outputs}"
LOGS_ROOT="${LOGS_ROOT:-$WORK_ENV_ROOT/logs}"
REPOS_ROOT="${REPOS_ROOT:-$(dirname "$WORK_ENV_ROOT")}"

export WORK_ENV_ROOT DATA_ROOT OUTPUTS_ROOT LOGS_ROOT REPOS_ROOT
