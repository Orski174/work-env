---
description: Scaffold a new task directory following repo conventions
---

Create a new task folder under `tasks/` following this repo's conventions.

Steps:

1. Determine a **short task name** (kebab-case). Infer it from the user's request
   if obvious (`$ARGUMENTS` may contain it); otherwise ask once.
2. Use **today's date** in `YYYY-MM-DD` format.
3. Prefer the existing tooling — run `make new-task name=<short-name>` (or
   `scripts/new-task.sh <short-name>`). This creates
   `tasks/YYYY-MM-DD-short-name/` with `README.md`, `notes.md`, `run.sh`,
   `main.py`, `input/`, and `output/`, makes `run.sh` executable, and adds a
   `.gitkeep` to `output/`. Only hand-create files if the script is unavailable.
4. Fill in the task `README.md` with the goal and any known external repo
   dependencies + their `$REPOS_ROOT/...` paths.
5. Add a new entry to `TASKS.md` using the template there (date, dir, goal,
   status `todo`, external repos, notes).

Keep generated files **minimal and practical** — no boilerplate beyond the
scaffold. Report the path of the created task folder when done.
