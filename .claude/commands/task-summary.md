---
description: Summarize completed work in a task folder
---

Summarize the work done in a task folder. Target task: `$ARGUMENTS` (a task
folder name/path, or infer the most relevant/recent one under `tasks/`).

Steps:

1. Read the task's files: `README.md`, `notes.md`, `main.py`/`run.sh`, and list
   what's in `output/`.
2. Write a concise summary covering:
   - **What was done** — the outcome in a few sentences.
   - **Commands used** — key commands to reproduce the work.
   - **Outputs produced** — files in `output/` (or `outputs/`) and what they are.
   - **External dependencies** — other local repos used and their
     `$REPOS_ROOT/...` paths.
3. Add or update a `## Summary` section in the task's `README.md` with the above.
   Don't duplicate — update the existing section if present.
4. Optionally update the task's entry in `TASKS.md` (e.g. status → `done`).

Keep it factual and brief. Report only what actually happened — don't invent
outputs or commands.
