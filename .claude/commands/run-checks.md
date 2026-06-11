---
description: Run basic repo checks (syntax + structure)
---

Run lightweight sanity checks on the repo.

Steps:

1. Inspect the `Makefile` for a `check` target.
2. If `make check` exists, run it. (It checks shell + Python syntax, expected
   directories, and that `.env` isn't tracked.)
3. If there's no Makefile/target, run reasonable lightweight checks yourself:
   - Shell: `bash -n` on each `*.sh` under `scripts/`, `bin/`, `tasks/`.
   - Python: `python3 -m py_compile` on each `*.py` (use `.venv/bin/python` if
     it exists). If `ruff` is already installed, a quick `ruff check` is fine.
4. **Report** what passed, what failed, and a suggested fix for each failure.

Do **not** install heavy dependencies to run checks. Prefer tools already present
(stdlib, the repo `.venv`). If a useful linter is missing, mention it rather than
installing it.
