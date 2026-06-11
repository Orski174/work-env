---
description: Plan a task before implementing it
---

Plan the task before writing implementation code. Target task: `$ARGUMENTS`
(a task folder name/path, or infer the most relevant/recent one under `tasks/`).

Steps:

1. Read the task's `README.md` and `notes.md` if they exist. Skim any files in
   `input/`.
2. **Summarize the goal** in 1–2 sentences.
3. Identify:
   - **Inputs** — what data/files/args the task consumes.
   - **Outputs** — what it should produce and where (`output/` or `outputs/`).
   - **Dependencies** — stdlib vs. external packages; any other local repos
     (note their `$REPOS_ROOT/...` paths) and whether an editable install fits.
   - **Risks** — anything error-prone, slow, destructive, or ambiguous.
4. Propose a **short, concrete implementation plan** (a handful of steps).

Keep it lightweight — **avoid over-engineering**. Don't propose frameworks or
broad refactors. Ask **at most one** clarifying question, and only if you are
genuinely blocked; otherwise state your assumptions and present the plan.
