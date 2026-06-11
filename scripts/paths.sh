#!/usr/bin/env bash
# Print useful repo paths.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

printf '%-14s %s\n' "WORK_ENV_ROOT" "$WORK_ENV_ROOT"
printf '%-14s %s\n' "REPOS_ROOT"    "$REPOS_ROOT"
printf '%-14s %s\n' "DATA_ROOT"     "$DATA_ROOT"
printf '%-14s %s\n' "OUTPUTS_ROOT"  "$OUTPUTS_ROOT"
printf '%-14s %s\n' "LOGS_ROOT"     "$LOGS_ROOT"
printf '%-14s %s\n' "tasks"         "$WORK_ENV_ROOT/tasks"
printf '%-14s %s\n' "scripts"       "$WORK_ENV_ROOT/scripts"
printf '%-14s %s\n' "vendor"        "$WORK_ENV_ROOT/vendor"
