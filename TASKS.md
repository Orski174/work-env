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

### 2026-06-23 — wireguard-boxman-demo

- **Dir:** tasks/2026-06-23-wireguard-boxman-demo/
- **Goal:** Boxman conf.yml + pytest integration test for wireguard_server + wireguard_client roles in a local libvirt environment (split-tunnel, iptables, dnsmasq). Tracks scds-infra #119.
- **Status:** todo
- **External repos:** $REPOS_ROOT/boxman-orig (CLI), $REPOS_ROOT/hpccluster (roles, playbooks, smoke tests)
- **Notes:** conf.yml and test live in this task dir (not in boxman-orig). Ref branch orski/73-wireguard-clouddev01 for role var choices (iptables backend, eth1 egress, 10.1.30.0/24 split-tunnel). Server writes /root/boxman_client.conf; client reads it via wireguard_client_connections[0].config_src.

### 2026-06-23 — oil-wells-fake-dataset

- **Dir:** tasks/2026-06-23-oil-wells-fake-dataset/
- **Goal:** Synthetic Iraq oil-well CSV + point shapefile (75 wells, seed 20260610, WGS84) for GeoServer demo.
- **Status:** done
- **External repos:** copied from $REPOS_ROOT/cams_geospatial_platform (branch orski/oil-wells-demo-dataset)
- **Notes:** Reference dataset committed under dataset/; run.sh regenerates into output/. Generator is pure stdlib — no pip deps.

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
