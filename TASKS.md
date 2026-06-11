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

### 2026-06-11 — saltstack-lab

- **Dir:** tasks/2026-06-11-saltstack-lab/
- **Goal:** Learn SaltStack — master/minion lab via boxman, apply a state end-to-end, document core concepts vs Ansible. Tracks scds-infra #6.
- **Status:** in-progress
- **External repos:** boxman ($REPOS_ROOT/boxman on sc1)
- **Notes:** Runs on sc1 (scds001), not locally. Two-phase: `boxman up` builds an Ubuntu 24.04 golden template with Salt 3008 baked in + clones 2 VMs; `setup-salt.sh` assigns roles. Authoring here, executing on sc1 via git push/pull.
