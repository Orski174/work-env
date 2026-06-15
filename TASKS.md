# Task Log

A lightweight running log of tasks done in this repo. Newest at top.
Create task dirs with `make new-task name=short-name`.

## Template

```
### YYYY-MM-DD — short-name
- **Dir:** tasks/YYYY-MM-DD-short-name/
- **Goal:** one line.
- **Status:** todo | in-progress | done | abandoned
- **External repos:** $REPOS_ROOT/... (or none)
- **Notes:** anything worth remembering.
```

---

<!-- Add entries below -->

### 2026-06-15 — terraform-workspaces-eval

- **Dir:** tasks/2026-06-15-terraform-workspaces-eval/
- **Goal:** Tech-scout Terraform workspaces for prod/staging separation vs. duplication. Tracks scds-infra #87.
- **Status:** done — concept + comparison + hands-on (state isolation proven locally) + recommendation in `findings.md` (paste-ready for the ticket).
- **External repos:** (none)
- **Notes:** Greenfield, target S3 backend, single account / naming-separated, prod+staging only. Recommendation: conditional yes (workspaces defensible since same account) with "wrong workspace" guardrails; escape hatch to dir-per-env if envs ever need separate creds/accounts. `demo/` uses the `hashicorp/local` provider (local backend) and proves isolation locally.

### 2026-06-11 — saltstack-lab

- **Dir:** tasks/2026-06-11-saltstack-lab/
- **Goal:** Learn SaltStack — master/minion lab via boxman, apply a state end-to-end, document core concepts vs Ansible. Tracks scds-infra #6.
- **Status:** in-progress — steps 1–3 done (lab up; demo state applied + idempotent). Step 4 (vs Ansible write-up) remaining.
- **External repos:** boxman ($REPOS_ROOT/boxman on sc1)
- **Notes:** Runs on sc1 (scds001), not locally. Two-phase: `boxman up` builds a minimal Ubuntu 24.04 golden template + clones 2 VMs; `setup-salt.sh` installs Salt 3008 over SSH + assigns roles. Demo state (`salt/states/demo`) installs htop + manages a templated config (grains+pillar); `run.sh sync`/`apply` drive it. Authoring here, executing on sc1 via git push/pull.
