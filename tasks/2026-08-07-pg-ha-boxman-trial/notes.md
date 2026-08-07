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

## 2026-08-07 — provisioning + bootstrap (with gotchas)

**`bin_dir`:** confirmed `/usr/lib/postgresql/16/bin` inside the built image
(CNPG's `postgresql:16` is Debian **bullseye**, not bookworm — no PEP 668
`--break-system-packages` enforcement, plain `pip install` is correct there).

**`./run.sh up`:** all 3 VMs provisioned cleanly — pg1 192.168.101.120, pg2
192.168.101.79, pg3 192.168.101.76. One environment fix needed first: boxman's
conda env on sc1 was missing `passlib` (cloud-init templating dependency) —
`pip install passlib` into `~/.conda/envs/boxman`, one-time, additive.

**`./run.sh setup` — five real bugs hit and fixed before the cluster came up
healthy** (all fixed in the committed scripts, not worked around by hand):

1. `ip_for()` parsed `HostName` (mixed case) but boxman's generated
   `ssh_config` uses `Hostname` — awk field match is case-sensitive, so IP
   resolution silently returned empty. Fixed to `tolower($1)=="hostname"`.
2. Dockerfile used `pip install --break-system-packages` assuming a
   bookworm-style base; the CNPG image is bullseye (pip 20.3.4), which doesn't
   have that flag at all. Removed it.
3. `docker.io` (Ubuntu's classic package) doesn't ship the `docker compose`
   v2 plugin subcommand — needed the separate `docker-compose-v2` archive
   package. Added as a fallback check alongside the existing docker.io
   fallback.
4. **etcd crashlooped:** the compose service set both `ETCD_NAME` (env) and
   `--name=...` (a `command:` override) — etcd v3.5.17 fatals on that
   combination ("conflicting environment variable is shadowed by
   corresponding command-line flag"). Removed the `command:` override
   entirely; env-only config is sufficient. This also caused `run.sh status`
   to hang indefinitely (`patronictl list` retrying forever against a dead
   DCS with no timeout) — added a 15s `timeout` around every `patronictl`
   invocation as a result.
5. **Patroni container ran as root**, and:
   - `initdb: cannot be run as root` — the Dockerfile's `USER root` (needed
     for the apt/pip install layer) was never reverted before running
     Patroni. Fixed by dropping to the image's existing `postgres` user
     (uid 26) via `setpriv` in `entrypoint.sh`, after `chown -R
     postgres:postgres` on the (root-owned-by-default) named volume.
   - that then broke on `$HOME` — `setpriv` (unlike `su -`) doesn't reset
     `$HOME`, so it stayed `/root` (unwritable by uid 26), breaking Patroni's
     default `.pgpass` path. Fixed with an explicit `export
     HOME=/var/lib/postgresql`.
   - that then broke on data-dir **permissions** (not just ownership) — a
     fresh named volume is `0755`; `chown` fixes owner but not mode, and
     Postgres 16 refuses to start unless the dir is exactly `0700`/`0750`.
     initdb's own bootstrap path happens to set this correctly on the
     leader (which is why pg1 came up fine on the first working attempt),
     but a **replica's** basebackup-based bootstrap does not — pg2/pg3 both
     failed with "data directory has invalid permissions" until an explicit
     `chmod 0700` was added right after the `chown`.
6. Separately: an earlier version of the script built the image via a raw
   `docker build -t pg-ha-trial-patroni .` (for `bin_dir` detection) while
   `docker compose up` builds its own, differently-named tag the first time
   it's needed and does **not** rebuild it on later `up`s. Every fix above
   landed in the file, got rebuilt under the raw tag, but pg1 kept silently
   reusing its very first (pre-fix) compose-built image across every rerun —
   the actual live symptom repeated identically for several iterations
   before this was diagnosed. Fixed by building exclusively via `docker
   compose build patroni` everywhere, so there is only one image tag.

**Final bootstrap result** (after fixing #5's chmod issue and rebuilding just
pg2/pg3 — pg1 was already correctly bootstrapped and left untouched to avoid
invalidating its already-initialized superuser/replication passwords):

```
+ Cluster: pg-ha-trial (7671302568584658978) ----+----+-------------+-----+------------+-----+
| Member | Host            | Role    | State     | TL | Receive LSN | Lag | Replay LSN | Lag |
+--------+-----------------+---------+-----------+----+-------------+-----+------------+-----+
| pg1    | 192.168.101.120 | Leader  | running   |  1 |             |     |            |     |
| pg2    | 192.168.101.79  | Replica | streaming |  1 |   0/7000060 |   0 |  0/7000060 |   0 |
| pg3    | 192.168.101.76  | Replica | streaming |  1 |   0/7000060 |   0 |  0/7000060 |   0 |
+--------+-----------------+---------+-----------+----+-------------+-----+------------+-----+
```

Passwords generated this run (random, `openssl rand -hex 16`, not persisted
anywhere beyond this note): replicator `c97ac73f...`, postgres `15c078f6...`
(truncated here deliberately — full values only ever appeared in the
now-discarded terminal output, not committed anywhere).

## TODO as the trial runs

- [x] Confirm CNPG image's actual Postgres `bin_dir`.
- [x] `./run.sh up` — VM provisioning result.
- [x] `./run.sh setup` — cluster bootstrap result (1 Leader + 2 Replicas).
- [ ] `./run.sh failover-test --switchover` — measured time.
- [ ] `./run.sh failover-test --kill-leader` — measured time, rejoin outcome.
- [ ] `./run.sh backup-test` — dump/restore + pg_basebackup result.
- [ ] Post-run `free -h` on sc1 — confirm no new memory distress.
- [ ] Final recommendation, written into `README.md`.
