# terraform-workspaces-eval

Created: 2026-06-15 — GitLab issue **scds-infra#87**

## Goal
Tech-scouting evaluation of Terraform **CLI workspaces** for separating prod vs. staging
from a shared codebase, with a clear-eyed recommendation (including when *not* to use them).
The deliverable is **`findings.md`** — written to be pasted directly into the ticket.

## Layout
- `findings.md` — the evaluation: concept, comparison table, hands-on proof, recommendation.
- `demo/` — throwaway, local-only Terraform config proving per-workspace state isolation.
- `notes.md` — running log + raw command output + doc sources.

## External repos / dependencies
- (none) — self-contained. Requires the `terraform` CLI (tested on v1.14.8).

## How to run the demo
```bash
./run.sh            # wrapper -> demo/run.sh
# or:
cd demo && ./run.sh
```
The demo uses the `hashicorp/local` provider (`local_file`) and the local backend — no
cloud, no cost. It creates `staging` + `prod` workspaces, applies in each, and prints proof
that state is isolated.

## Outputs
Terraform working files, state, and the workspace-named markers are written under `demo/`
and are **gitignored** (`demo/.gitignore`) — never committed.
