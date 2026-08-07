# Notes — pg-ha-boxman-trial

Tracks scds-infra #91, sprint-011. Plan reviewed and greenlit by command-center
via agent-mailbox on 2026-08-07 (message
`20260807T103008-pg-ha-boxman-trial-plan-reviewed-greenli`).

## 2026-08-07 — created, pre-flight checks

**sc1 resource headroom check** (per command-center's request, re: prior
Work #197 tenant-density pressure):
- `free -h`: 124Gi total, 772Mi free physical, 16Gi `available` (MemAvailable —
  the kernel's own safe-to-allocate estimate, already accounts for reclaimable
  cache), swap 4Gi/4Gi fully used (a legacy-pressure signal from some earlier
  point, not necessarily current active thrashing — Linux doesn't proactively
  swap pages back in once written out).
- 22 VMs currently running across `bprj__sc1-talos`, `bprj__clouddev01-small`,
  `bprj__derboukagpt`, `bprj__salt-lab`, `bprj__hf_hub_alt_pocs` projects.
  16 vCPUs total on the host.
- Disk: 130G free of 932G (86% used) on `/`.
- **Verdict:** proceeding. 3 new VMs need 3 vCPU / 6GiB RAM, comfortably under
  the 16Gi `available` figure even with Docker/etcd/Patroni overhead on top.
  Swap-maxed is a watch-item, not a blocker — noted here per the ask, will
  re-check `free -h` after `up` + `setup` to confirm no new distress.

**Subnet check:** `virsh net-list --all` + `net-dumpxml` on sc1 showed active
NAT networks on 192.168.20/23/77/78/122.0/24 — chose **192.168.101.0/24** for
this task's `nat1`, no collision.

**Password generation:** replicator/superuser passwords are generated fresh
each `./setup.sh` run via `openssl rand -hex 16` (see `setup.sh`), not a fixed
default like the `BOXMAN_ADMIN_PASS` convention used for VM admin login
elsewhere in this repo — per command-center's request to confirm which
approach was used. Printed once at the end of `setup.sh`'s output; not stored
anywhere else (throwaway trial, no persistence needed beyond the run).

## Design notes (carried over from the plan)

- Patroni supervises Postgres **inside** the CNPG-derived image (PID 1 =
  patroni, forks/execs `postgres`) — not Patroni-on-host managing a separate
  container. See `README.md` for the reasoning.
- `network_mode: host` on both `etcd` and `patroni` compose services — the VM
  itself is the isolation boundary for a 3-VM trial, so no bridge/port-mapping
  plumbing needed.
- One etcd member per VM — natural 3-node quorum, no 4th VM.
- Cloud-init stays minimal (`docker.io` added to `packages:`, machine-id reset
  in `runcmd` kept verbatim from `wireguard-boxman-demo`/`saltstack-lab`) —
  boxman's ~120s done-marker poll can't tolerate a slow install baked into the
  template. `setup.sh` has a fallback docker install in case `docker.io`
  didn't land in time.

## TODO as the trial runs

- [ ] Confirm CNPG image's actual Postgres `bin_dir` (detected automatically
      by `setup.sh`, record what it found here).
- [ ] `./run.sh up` — VM provisioning result.
- [ ] `./run.sh setup` — cluster bootstrap result (1 Leader + 2 Replicas?).
- [ ] `./run.sh failover-test --switchover` — measured time.
- [ ] `./run.sh failover-test --kill-leader` — measured time, rejoin outcome.
- [ ] `./run.sh backup-test` — dump/restore + pg_basebackup result.
- [ ] Post-run `free -h` on sc1 — confirm no new memory distress.
- [ ] Final recommendation, written into `README.md`.
