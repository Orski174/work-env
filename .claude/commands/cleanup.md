---
description: Clean temporary files safely
---

Clean up temporary/scratch files without destroying anything important.

Steps:

1. Read `.gitignore`, the `Makefile`, and repo conventions (CLAUDE.md) to decide
   what is safe to remove. Safe-to-clean things: `__pycache__/`, `*.py[co]`,
   `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `tmp/`, `.cache/`, `*.tmp`.
2. If the `Makefile` has a `clean` target, **prefer `make clean`** (it removes
   caches/temp but keeps the venv, data, and outputs).
3. For anything beyond `make clean`, **show what would be deleted first** (e.g.
   the file list) and get confirmation before deleting when the deletion is
   nontrivial.

Never delete without asking:
- source files or helper scripts,
- task `notes.md` / `README.md`,
- raw inputs (`data/raw/`, task `input/`),
- outputs that aren't clearly disposable/undocumented.

When in doubt, ask. Preserve the lightweight, recoverable state of the repo —
don't touch `.git/`, `.env`, or the `.venv` unless explicitly asked.
