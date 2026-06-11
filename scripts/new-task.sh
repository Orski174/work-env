#!/usr/bin/env bash
# Create a new task directory: scripts/new-task.sh short-name
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

name="${1:-}"
if [ -z "$name" ]; then
  echo "usage: $(basename "$0") short-name" >&2
  exit 1
fi

# Sanitize: lowercase, spaces/underscores -> dashes, strip junk.
slug="$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' _' '--' | tr -cd 'a-z0-9-')"
date_prefix="$(date +%Y-%m-%d)"
task_dir="$WORK_ENV_ROOT/tasks/${date_prefix}-${slug}"

if [ -e "$task_dir" ]; then
  echo "error: $task_dir already exists" >&2
  exit 1
fi

mkdir -p "$task_dir/input" "$task_dir/output"
touch "$task_dir/output/.gitkeep"

cat > "$task_dir/README.md" <<EOF
# ${slug}

Created: ${date_prefix}

## Goal
What this task does and why.

## External repos / dependencies
- (none) — list paths to other local repos used, e.g. \$REPOS_ROOT/some-repo

## How to run
\`\`\`bash
./run.sh
\`\`\`

## Inputs
Describe what goes in \`input/\`.

## Outputs
Describe what lands in \`output/\` (gitignored).
EOF

cat > "$task_dir/notes.md" <<EOF
# Notes — ${slug}

- ${date_prefix}: created.
EOF

cat > "$task_dir/main.py" <<'EOF'
#!/usr/bin/env python3
"""Entry point for this task."""
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
INPUT = TASK_DIR / "input"
OUTPUT = TASK_DIR / "output"


def main() -> None:
    print(f"task dir: {TASK_DIR}")


if __name__ == "__main__":
    main()
EOF

cat > "$task_dir/run.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Prefer the repo venv if it exists.
PY="python3"
if [ -x "../../.venv/bin/python" ]; then PY="../../.venv/bin/python"; fi

"$PY" main.py "$@"
EOF
chmod +x "$task_dir/run.sh" "$task_dir/main.py"

echo "created: $task_dir"
ls -1 "$task_dir"
