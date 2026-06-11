# work-env

A personal/work **scratch environment** for miscellaneous tasks that don't belong
in a dedicated project repo: small scripts, experiments, one-off utilities,
automation, notes, and glue code.

Optimized for **Python and shell** by default, but language-flexible.

## What goes here

✅ Good fits:
- One-off scripts and quick experiments
- Automation / glue code tying tools or repos together
- Throwaway data wrangling, exploration notebooks
- Notes, scratch utilities, CLI snippets

🚫 Keep out:
- Anything that deserves its own repo (give it one once it grows up)
- Secrets, credentials, private data committed to git (use `.env`, see below)
- Large datasets or generated artifacts (live in `data/` / `outputs/`, gitignored)
- Code copied wholesale from other repos (reference or vendor instead — see below)

## Layout

```
work-env/
  README.md          this file
  TASKS.md           running log of tasks
  Makefile           common commands
  .env.example       copy to .env and fill in
  scripts/           reusable helper scripts (lib, new-task, paths, check)
  tasks/             one dir per task: tasks/YYYY-MM-DD-short-name/
  notebooks/         Jupyter / scratch notebooks
  data/raw/          inputs, never edited in place        (gitignored)
  data/processed/    derived data                          (gitignored)
  outputs/           results / artifacts                   (gitignored)
  logs/              run logs                              (gitignored)
  docs/              longer-form notes / references
  vendor/            intentionally vendored external code  (gitignored)
  config/            shared config files
  bin/               small executables / dispatchers on PATH
```

## Setup

```bash
make setup                  # creates .venv (uv if available, else venv+pip)
source .venv/bin/activate
cp .env.example .env        # then edit .env
```

Python is **3.x**; this machine has no `uv`, so `make setup` falls back to
`venv` + `requirements.txt`. If you install `uv` later, `make setup` uses it
automatically.

## Common commands

```bash
make help                       # list targets
make setup                      # create venv + install requirements
make new-task name=scrape-foo   # scaffold tasks/YYYY-MM-DD-scrape-foo/
make paths                      # print resolved repo paths
make check                      # syntax + structure sanity checks
make clean                      # remove caches/temp (keeps venv + data)
```

## Creating a new task

```bash
make new-task name=resize-images
# -> tasks/2026-06-11-resize-images/ with:
#    README.md  run.sh  main.py  input/  output/  notes.md
```

Each task is **self-contained**. Convention:

```
tasks/YYYY-MM-DD-short-name/
  README.md   goal, external deps, how to run
  run.sh      entry point (uses repo .venv if present)
  main.py     Python entry point
  input/      task inputs
  output/     task outputs (gitignored)
  notes.md    running notes
```

## Running scripts

```bash
./scripts/paths.sh                       # helper scripts are directly runnable
tasks/2026-06-11-resize-images/run.sh    # run a task
```

`run.sh` prefers the repo `.venv` if it exists, else falls back to system
`python3`.

## Referencing other local repos

Other tasks may need code/data/CLIs from repos elsewhere on this machine.
Do it **safely**:

- Set `REPOS_ROOT` in `.env` (defaults to this repo's parent dir) and reference
  repos via `$REPOS_ROOT/<repo>` — **avoid hardcoded absolute paths**.
- Prefer an **editable install** when you need a sibling repo as a package:
  ```bash
  source .venv/bin/activate
  pip install -e "$REPOS_ROOT/some-lib"
  ```
- **Don't copy code** from other repos. Reference it, import it, or — only when
  you deliberately want a frozen snapshot — **vendor** it into `vendor/`
  (gitignored by default; commit deliberately if you must).
- **Document external repo paths** in each task's `README.md` so the task is
  reproducible.
- Keep **secrets and private data out of git** — put them in `.env` (gitignored)
  and read them via environment variables.

## Where things live

| Kind                     | Location            | Tracked?            |
|--------------------------|---------------------|---------------------|
| Reusable helpers         | `scripts/`, `bin/`  | yes                 |
| Task code                | `tasks/.../`        | yes (except output) |
| Raw / processed data     | `data/`             | no (gitignored)     |
| Results / artifacts      | `outputs/`          | no (gitignored)     |
| Run logs                 | `logs/`             | no (gitignored)     |
| Temp / scratch           | `tmp/`, `*.tmp`     | no (gitignored)     |
| Secrets / env            | `.env`              | no (gitignored)     |
| Notes (longer)           | `docs/`             | yes                 |
| Notes (per task)         | `tasks/.../notes.md`| yes                 |
| Task log                 | `TASKS.md`          | yes                 |

See `TASKS.md` for the running task log.
