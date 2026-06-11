#!/usr/bin/env bash
# Basic sanity checks: shell + python syntax, expected structure.
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
cd "$WORK_ENV_ROOT"

status=0

echo "==> checking shell scripts"
while IFS= read -r -d '' f; do
  if bash -n "$f"; then
    echo "  ok   $f"
  else
    echo "  FAIL $f"; status=1
  fi
done < <(find scripts bin tasks -name '*.sh' -type f -print0 2>/dev/null)

echo "==> checking python files"
PY="python3"
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"
while IFS= read -r -d '' f; do
  if "$PY" -m py_compile "$f" 2>/dev/null; then
    echo "  ok   $f"
  else
    echo "  FAIL $f"; status=1
  fi
done < <(find scripts tasks -name '*.py' -type f -print0 2>/dev/null)

echo "==> checking expected directories"
for d in scripts tasks data/raw data/processed outputs logs docs vendor config bin; do
  [ -d "$d" ] && echo "  ok   $d/" || { echo "  MISSING $d/"; status=1; }
done

echo "==> checking secrets are not staged"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "  FAIL .env is tracked by git!"; status=1
  else
    echo "  ok   .env not tracked"
  fi
fi

[ "$status" -eq 0 ] && echo "==> all checks passed" || echo "==> checks FAILED"
exit "$status"
