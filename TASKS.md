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

### 2026-08-07 — pg-ha-boxman-trial

- **Dir:** tasks/2026-08-07-pg-ha-boxman-trial/
- **Goal:** Evaluate HA Postgres via Patroni on 3 boxman VMs (pg1/pg2/pg3), using CNPG's own Postgres image as the container base under Docker — non-k8s fallback since CNPG itself is a k8s operator. Tracks scds-infra #91, sprint-011.
- **Status:** done
- **External repos:** boxman (`~/git/boxman` on sc1)
- **Notes:** Plan reviewed/greenlit by command-center via agent-mailbox. Ran on sc1 like wireguard-boxman-demo/saltstack-lab; six real bootstrap bugs hit and fixed (see notes.md). Result: 6s failover (both graceful switchover and simulated hard-kill), clean backup/restore. Recommendation: adopt selectively as one shared cluster, not one per service. VMs torn down after. This session did not touch the scds-infra GitLab issue directly — findings reported back via agent-mailbox for command-center to post.

### 2026-07-20 — demo-173-opencode-proxy

- **Dir:** tasks/2026-07-20-demo-173-opencode-proxy/
- **Goal:** Demo/KT prep for OpenCode Go models in Claude Code's `/model` picker. Tracks scds-infra #173.
- **Status:** done
- **External repos:** `~/projects/claudeStuff/gateways/opencode-go`
- **Notes:** KT/demo content only (`demo-script.md`), nothing to execute. Corrected the source script during prep: LiteLLM bridge is obsolete (proxy.py now does OpenAI-compat translation in-process), `opencode-litellm.service` is a dead unit, not a gap to fix — follow-up candidate is disabling/removing it. Model count corrected to 22 (was 14 in ticket).

### 2026-07-20 — demo-172-sc1-talos

- **Dir:** tasks/2026-07-20-demo-172-sc1-talos/
- **Goal:** Demo/KT prep for the sc1 6-node HA Talos k8s cluster. Tracks scds-infra #172.
- **Status:** done
- **External repos:** `~/git/hpc-k8s-infra`
- **Notes:** KT/demo content only (`demo-script.md`), nothing to execute. Found during prep: `kustomization/infrastructure` on sc1 is failing (Rook-Ceph CRDs missing after commit `16035f3` added a `CephBlockPool` manifest) — flagged in the script per user's call, not fixed. Node health unaffected.

### 2026-07-08 — signal-server-viability

- **Dir:** tasks/2026-07-08-signal-server-viability/
- **Goal:** Determine whether `signalapp/Signal-Server` can be self-hosted as a genuine standalone server real Signal clients can use. Tracks scds-infra #148.
- **Status:** done
- **External repos:** none
- **Notes:** Research/writing task, no deployment. Conclusion: not practically viable — FoundationDB + private `spam-filter` submodule are build blockers, Contact Discovery Service's SGX-enclave/x86-only native build is a hard wall every hands-on attempt hits, and the furthest-reaching community guide only works by stripping `zkgroup` and requiring a forked non-official client. #26's self-hosted-Matrix decision remains the actual independent backup; #148 resolves as a documented finding, not an infra change.

### 2026-06-23 — backup-comm-channel

- **Dir:** tasks/2026-06-23-backup-comm-channel/
- **Goal:** Compare Matrix, Discord, Slack, Signal as backup comms channel for a small team (scds-infra #26).
- **Status:** done
- **External repos:** none
- **Notes:** Research/writing task. Deliverable is notes.md. Rev 1 rec: Signal as primary. Rev 2 (Teams→Signal migration context): Matrix self-hosted as permanent backup; Teams as transitional backup during migration.

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
