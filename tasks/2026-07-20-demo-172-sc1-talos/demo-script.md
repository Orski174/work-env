# Demo & KT — sc1 6-node HA Talos k8s cluster (scds#172)

Audience: @jadshaker, @mherkazandjian. Repo: `~/git/hpc-k8s-infra`.

## Pre-flight (checked 2026-07-20, see "Blocker found during prep" below)
- `kubectl --context sc1 get nodes` → **6/6 Ready** (talos-2ur-ha6, talos-8hg-lii,
  talos-g61-hy6, talos-jrh-c9r, talos-q3f-ier, talos-r3d-mdh — 3 CP + 3 worker, 21d uptime)
- `flux --context sc1 get all -A` → `gitrepository/flux-system` **Ready=True**, synced to
  `main@sha1:411b437b`. `kustomization/flux-system` **Ready=True**.
  `kustomization/infrastructure` is currently **NOT Ready** — see blocker below.
  `kustomization/services` does not exist yet (blocked behind infrastructure).

## Blocker found during prep (new, doc originally said flux was fully green)
- Commit `16035f3` ("replace local-path-provisioner plan with Rook-Ceph, 2 tiers") landed
  on `main` and added a `CephBlockPool` manifest, but the Rook-Ceph operator/CRDs were
  never installed on sc1.
- `kustomization/infrastructure` is failing dry-run:
  `CephBlockPool/rook-ceph/workertier-pool dry-run failed: no matches for kind "CephBlockPool" in version "ceph.rook.io/v1"`
- This is also blocking apply of cert-manager, traefik, and the rook-ceph namespaces that
  are bundled in the same kustomization.
- **Flagged, not fixed** — node health is unaffected (6/6 Ready), fine to demo live as-is.
  If asked live: this is a known in-progress storage migration, not a cluster outage.

## Script

1. **Topology** — `cd ~/git/hpc-k8s-infra`, walk `CLAUDE.md` node table: 3 CP (2vCPU/4GB/50GB)
   + 3 workers (4vCPU/6GB/150GB) + 1 mgmt VM (Ubuntu, Omni self-hosted), all libvirt on sc1,
   `/mnt/data` storage pool. Total 20 vCPU / 38 GB / 1.05 TB.
2. **Provisioning path** (#150 → #143):
   - `boxman/sc1-talos-cluster/` config → `boxman up` provisions the 7 VMs
   - Talos VMs boot via `cdroms:` + `boot_order: [cdrom, hd]` from an Omni-specific ISO
     (`omnictl download iso`) — this ISO-boot capability didn't exist before #150
   - Omni auto-registers nodes via SideroLink once booted → cluster template → etcd bootstrap
3. **Live: Omni UI walkthrough** — Machines page (6 registered), cluster health, machine configs.
4. **Live: cluster health**
   ```
   kubectl --context sc1 get nodes -o wide
   flux --context sc1 get all -A
   ```
   Expect `kustomization/infrastructure` to show not-ready — that's the known blocker above,
   not a surprise. Don't dwell on it unless asked.
5. **GitOps repo tour** (`~/git/hpc-k8s-infra`):
   - `clusters/sc1/` = flux bootstrap entry point, `kustomization.yaml` orders
     `infrastructure.yaml` → `services.yaml`
   - `infrastructure/{base,overlays/sc1}` — cert-manager, metallb, storage, monitoring
   - `services/{base,overlays/sc1}` — same base/overlay pattern for workloads
   - `boxman/` — VM lifecycle config; `talos/` — Omni machine-config backups (review only)
6. **Blockers hit & fixed** (talking points, no live repro needed):
   - Omni TLS/SideroLink cert mismatch
   - Hetzner NTP UDP 123 outbound block
   - `on_reboot=destroy` VM XML setting caused reboots to wipe the VM — fixed
   - Missing `virtio-serial` guest-agent channel
7. **Q&A / handoff** — what's needed to reprovision or extend: boxman config +
   `flux bootstrap gitlab --owner=Orski174 --repository=hpc-k8s-infra --branch=main
   --path=clusters/sc1`, Omni ISO re-download, SOPS-encrypted `age.key` for secrets.

## Close-out
- [ ] Demo delivered to @jadshaker and @mherkazandjian
- [ ] Follow-up items captured as new scds-infra tickets — strong candidate: install
  Rook-Ceph operator/CRDs on sc1 to unblock `kustomization/infrastructure`
- Comment the outcome on scds-infra#172 (mirrors to Vikunja Work #128 description per the
  resolution-documentation convention) and check both Outcome boxes before closing.
