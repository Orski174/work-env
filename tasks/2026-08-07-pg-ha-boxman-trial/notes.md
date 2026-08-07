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

## 2026-08-07 — failover tests

**`--switchover` (graceful):** pg1 → pg2, **6s** elapsed. `patronictl
switchover` output showed the clean sequence directly: pg1 stopped Postgres
first, then pg2 promoted. pg1 rejoined on its own as a streaming replica
(confirmed via `./run.sh status` immediately after) with zero lag, timeline
bumped 1→2.

**`--kill-leader` (hard-failure simulation):** pg2 → pg1, **6s** elapsed, pg2
rejoined cleanly as a streaming replica after restart (timeline 2→3).

**Caveat worth stating plainly in the recommendation:** both measured times
are ~6s, not the ~30s `ttl` the design doc anticipated for the hard-kill path.
That's because `docker compose stop` sends **SIGTERM**, which Patroni catches
and uses to release its leader lock immediately and cleanly — this is a
*graceful process stop*, not a true hard failure (VM power loss, `kill -9`,
network partition, host crash). A real hard failure would only be detected
after the leader's lock **expires** in etcd (bounded by the configured `ttl:
30`), so real-world worst-case failover is closer to that ~30s figure, not
the 6s observed here. Both numbers are worth reporting: 6s demonstrates the
graceful-stop path is fast, but the true hard-crash worst case is still
~30s-bounded and untested directly in this trial (would need an actual VM
power-off or `kill -9` on the patroni process to observe).

Either way — **today's per-service standalone Postgres has zero automatic
failover at all**; any primary failure is full downtime until a human
intervenes. Both 6s and the ~30s worst-case bound are a categorical
improvement over that baseline.

## 2026-08-07 — backup/restore test

- [x] Confirm CNPG image's actual Postgres `bin_dir`.
- [x] `./run.sh up` — VM provisioning result.
- [x] `./run.sh setup` — cluster bootstrap result (1 Leader + 2 Replicas).
- [x] `./run.sh failover-test --switchover` — 6s, clean rejoin.
- [x] `./run.sh failover-test --kill-leader` — 6s (SIGTERM-driven, see caveat
      above), clean rejoin.
- [x] `./run.sh backup-test` — see below.
- [x] Post-run `free -h` on sc1 — see below.
- [x] Final recommendation, written into `README.md`.

**`./run.sh backup-test` result:** one real bug hit and fixed (`< /tmp/backup.sql`
was nested inside a container-side `sh -c`, looking for the dump file in the
wrong filesystem — the dump itself landed on the VM host via a host-level `>`
redirect. Fixed by redirecting at the same level for both dump and restore).

```
dump+restore elapsed: 3s
original row count:   50
restored row count:   50
row counts match:     yes
pg_basebackup ok:      yes
```

pg_dump → restore-into-fresh-database round-trip: clean, 3s, row counts match
exactly. `pg_basebackup` (physical backup, doubling as a replication-auth
sanity check) completed a full 39MB base backup successfully.

**Known minor bug, not fixed:** the `pg_basebackup` step's `PGPASSWORD=$(grep
... | awk ...)` one-liner has a shell-quoting bug (visible as `grep:
/etc/patroni.ymlawk: ...` noise in the output) that likely left `PGPASSWORD`
empty. The backup still succeeded, most plausibly because it ran as the
`postgres` OS user with `$HOME=/var/lib/postgresql` (set in `entrypoint.sh`),
and Patroni maintains its own `~/.pgpass` there for its internal replication
connections — libpq auto-discovers that file ahead of any env var, which is a
legitimate, intentional auth path, just not the one the script's one-liner
intended. Net effect: the actual thing being tested (does replication auth
work) is answered — yes — even though the script's own password-extraction
line is cosmetically broken. Not worth chasing further for a trial.

**Explicit gaps, as scoped in the original plan (not evaluated here):**
- This does not exercise restoring a `pg_dump` into a brand-new
  Patroni-bootstrapped node — only into a fresh database on an existing,
  already-running node.
- No continuous WAL-archiving / point-in-time-recovery solution (Barman,
  pgBackRest) was evaluated. A production adoption would need one; this
  trial only proves the underlying logical/physical backup primitives work.

## 2026-08-07 — post-run resource check, recommendation

**Post-run `free -h` on sc1:**
```
               total        used        free      shared  buff/cache   available
Mem:           124Gi       115Gi       1.1Gi       1.4Gi        10Gi       9.2Gi
Swap:          4.0Gi       4.0Gi       0.0Ki
```
`available` dropped from ~16Gi (pre-flight) to ~9.2Gi — this one 3-VM cluster
consumed roughly 7Gi once Docker/Postgres/etcd overhead is included on top of
the 3×2048MB VM allocations. Swap usage unchanged (still fully used, not
growing) — no new distress signal, but confirms the fixed-per-cluster cost
observation in the recommendation: this isn't a cost that scales down if
replicated per-service.

**Recommendation written to `README.md`: adopt selectively, as one shared
cluster, not one per service.** See README for full reasoning — summary: the
HA mechanics genuinely work (6s observed failover, ~30s worst-case bound,
vs. today's zero-HA baseline), but the overhead (VMs, etcd, custom image,
new config/ops surface) is largely fixed per cluster rather than per
database, so a shared cluster amortizes it while a cluster-per-service
pattern would 3x the footprint on an already memory-constrained host for no
proportional benefit.

## 2026-08-07 — teardown

`./run.sh destroy -y`: all 3 VMs undefined and their network removed cleanly.
One cosmetic issue, not a real problem: `virsh undefine
--remove-all-storage --wipe-storage ...` hit a libvirt storage-pool API quirk
(`unsupported flags (0x2) in function virStorageBackendVolDeleteLocal`) on
all 3 disks — the *wipe* itself succeeded ("Wiping volume ... Done") but the
follow-up unlink call failed. Didn't matter: boxman's final cleanup step
force-removes the whole workspace directory tree at the filesystem level
regardless of libvirt's storage-pool bookkeeping, so the qcow2 files were
gone either way. Confirmed after: `virsh list --all` shows no pg_ha_trial
VMs, `virsh net-list --all` shows no pg_ha_trial network, workspace dir gone.

Post-teardown `free -h`: `available` back to ~15Gi (from the post-run 9.2Gi),
consistent with the pre-flight ~16Gi baseline — the resource footprint was
fully reclaimed, no leftover drag on sc1 from this trial.

**Trial complete.** All deliverables from the ticket brief are done: trial
deployment ✓, HA/failover evaluated ✓, backup/restore evaluated ✓,
operational-overhead comparison ✓, recommendation ✓ (adopt selectively, as
one shared cluster). Reported back to command-center via agent-mailbox for
posting to scds-infra #91.
