# CLAUDE.md — work-env

Project instructions for Claude Code working in this repo.

## What this repo is

A general-purpose **scratch/work environment** for miscellaneous tasks that don't
belong in a dedicated repo: small scripts, experiments, one-off utilities,
automation, notes, and glue code. Optimized for **Python and shell**, but
language-flexible.

**Treat this as a flexible workbench, not a production app.** Keep it lightweight.
Prefer simple, readable scripts over frameworks and abstraction. Don't introduce
complex tooling, package managers, hooks, or CI unless already present or clearly
useful for the task at hand.

## Repo structure

```
scripts/           reusable helper scripts (lib.sh, new-task, paths, check)
tasks/             one dir per task: tasks/YYYY-MM-DD-short-name/
notebooks/         Jupyter / scratch notebooks
data/raw/          inputs, never edited in place        (gitignored)
data/processed/    derived data                          (gitignored)
outputs/           results / artifacts                   (gitignored)
logs/              run logs                              (gitignored)
docs/              repo-wide / longer-form notes
vendor/            intentionally vendored external code  (gitignored)
config/            shared config files
bin/               small executables (e.g. the `we` dispatcher)
CLAUDE.md  README.md  TASKS.md  Makefile  .env.example  requirements.txt
```

## Tasks

One-off work lives in `tasks/YYYY-MM-DD-short-name/`. A task folder may contain:

```
README.md   goal, external deps + paths, how to run
run.sh      entry point (uses repo .venv if present)
main.py     Python entry point
input/      task inputs
output/     task outputs (gitignored)
notes.md    running notes
```

Each task is self-contained. Don't scatter a task's files across the repo.

### Creating a new task

Prefer the existing tooling — don't reinvent it:

```bash
make new-task name=short-name      # or: scripts/new-task.sh short-name
```

This scaffolds `tasks/<today>-short-name/` with the files above, makes `run.sh`
executable, and creates `input/` + `output/`. Use **today's date** in
`YYYY-MM-DD`. After creating a task, add an entry to `TASKS.md`.

## Dependencies from other local repos

Some tasks depend on code/data/CLIs from other repos on this machine.

- Reference them via **`$REPOS_ROOT/<repo>`** (set in `.env`; defaults to this
  repo's parent). **Prefer environment variables over hardcoded absolute paths.**
- To use a sibling repo as a package, prefer an **editable install**:
  `pip install -e "$REPOS_ROOT/<repo>"`.
- Prefer **shell-level references or editable installs over copying code.**
- **Ask before vendoring** code into `vendor/`. Vendoring is opt-in and means a
  deliberate frozen snapshot; record the source repo + commit.
- **Document the dependency and its path in the task's `README.md`** so the task
  stays reproducible.

## Secrets, data, outputs, logs

- Local config goes in **`.env`** (gitignored). Only **`.env.example`** is
  committed. Read config via environment variables.
- **Never commit** secrets, private data, large raw datasets, virtual
  environments, or generated outputs.
- Generated artifacts → **`outputs/`** or task-local **`output/`**.
- Run logs → **`logs/`**.
- Raw inputs → **`data/raw/`** (treat as read-only); derived → `data/processed/`.

## What to avoid

- Don't treat this like a production codebase or add heavy structure.
- Don't make broad refactors unless directly useful for the current task.
- Don't commit secrets, private data, large datasets, venvs, or outputs.
- Don't hardcode absolute machine paths — use `$REPOS_ROOT`, `$DATA_ROOT`, etc.
- Don't copy code from other repos without reason; reference or (with a prompt)
  vendor instead.
- Don't delete source files, task notes, raw inputs, or undocumented outputs
  without asking.

## Preferred commands

```bash
make setup                      # create .venv (uv if present, else venv+pip)
make new-task name=short-name   # scaffold a task
make paths                      # print resolved repo paths
make check                      # syntax + structure + secret-leak checks
make clean                      # remove caches/temp (keeps venv + data)
```

`bin/we new|paths|check` is a shortcut for the same helpers.

## Coding style

- Simple and readable over clever. Small scripts, few dependencies.
- **Python:** standard library first; PEP 8; type hints where they help; a
  `main()` guarded by `if __name__ == "__main__":`. Match the style of the
  scaffolded `main.py`.
- **Shell:** `#!/usr/bin/env bash` + `set -euo pipefail`; quote variables;
  resolve paths relative to the script, not the CWD.
- Keep reusable helpers in `scripts/`; keep one-off logic inside the task folder.

## Documentation

- Each task's `README.md`: goal, external repo deps + paths, how to run, inputs,
  outputs. Keep `notes.md` as a running log.
- Repo-wide or longer-form notes go in `docs/`.
- Update `TASKS.md` when starting or finishing a task.
- Keep generated files **minimal and practical** — no boilerplate for its own sake.
