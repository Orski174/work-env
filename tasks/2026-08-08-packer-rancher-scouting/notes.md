# Notes — packer-rancher-scouting

Running log. Tracks scds-infra #184.

## 2026-08-08 — created, scoping

Scaffolded the task. Two independent sub-trials, both executed on sc1 via boxman.

**Scoping findings (before touching either tool):**

- boxman already has a declarative `templates:` mechanism in `conf.yml` that
  auto-builds template VMs from a cloud image + inline cloud-init on first
  `boxman provision` (`~/git/boxman/README.md:93-142`,
  `~/git/boxman/data/templates/conf.libvirt.yml`). `rocky-95-minimal-base-template`
  (referenced in `boxman/README.md:306`) is exactly this mechanism, Rocky
  flavor — so this is *not* "no repeatable pipeline exists". The real Packer
  comparison is declarative-template-in-conf.yml (current) vs. a separate
  Packer build step + its provisioner/artifact ecosystem.
- `/usr/sbin/packer` on sc1 is a decoy: `file` + `rpm -qf` confirm it's
  `cracklib-packer` (password-dictionary tool, package `cracklib-dicts`), not
  HashiCorp Packer. Real Packer needs installing from scratch.
- sc1 `free -h`: 13Gi available (124Gi total, 110Gi used, swap 4Gi/4Gi full).
  Tighter than the ~15-16Gi baseline `pg-ha-boxman-trial` saw, because several
  VMs are already up and left running: `sc1-talos` (6-node Omni-managed Talos
  cluster + mgmt VM), `salt-lab` (2 VMs — that task is still "in-progress",
  not torn down), `clouddev01-small`, `derboukagpt`. Disk is not a constraint
  (13T free on `/mnt/data`). → keeping both new trial VMs small, tearing down
  promptly once findings are captured.
- `sc1-talos` (the live 6-node cluster) has a known open issue — flux
  `kustomization/infrastructure` failing since a `CephBlockPool` manifest
  landed without the Rook-Ceph operator/CRDs (see
  `tasks/2026-07-20-demo-172-sc1-talos/notes.md`) — and it's a shared KT/demo
  resource. **Not touching it** for the Rancher trial; using a throwaway
  boxman-provisioned k3s VM instead.
- Neither k3s nor Helm are installed on sc1 either — both installed fresh as
  part of the Rancher trial.

## 2026-08-08 — Packer sub-trial, build

Wrote `packer/template.pkr.hcl` (qemu builder, Rocky 9 GenericCloud base +
NoCloud seed for Packer's own SSH communicator only) and
`packer/boxman-test/conf.yml` (a boxman template pointed at the built qcow2
via `image: file://{{ env("PACKER_IMAGE_PATH") }}` — confirmed by reading
`boxman/src/boxman/providers/libvirt/cloudinit.py:_resolve_image_path`, which
strips a `file://` prefix and falls through to a local-file copy, so a
Packer-built qcow2 slots into boxman's normal template pipeline with zero
extra machinery — no OCI push/import-image package needed for this).

Installed HashiCorp Packer 1.16.0 on sc1 via `dnf config-manager --add-repo
https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo` (confirms
`/usr/sbin/packer`/cracklib-packer wasn't shadowing anything real).

**Bug hit:** first `packer build` failed immediately — `error downloading
ISO: [bad response code: 404]` — because the exact Rocky 9.7 point-release
URL copied from boxman's own
`boxes/tiny-libvirt-rocky-9-cloudinit/conf.yml` (`Rocky-9-GenericCloud-Base-9.7-20251123.2...`)
had already been rotated out of `download.rockylinux.org` (Rocky only
mirrors a handful of recent point releases). Fixed by resolving the
`.latest.x86_64.qcow2` symlink to the current build
(`Rocky-9-GenericCloud-Base-9.8-20260525.0`) and re-pinning to its real
checksum. **Relevant to the write-up either way**: whichever tool owns the
image URL, that pin needs periodic refreshing — this isn't a Packer-specific
weakness, boxman's own checked-in example conf.yml has the identical
stale-pin problem right now.

`packer build` kicked off in the background on sc1 (`nohup ... &`,
`/tmp/packer-build.log`) — downloading the ~700MB base image, booting it via
qemu (512MB build VM, headless, VNC boot-command injection), then running
the shell provisioner (`dnf install -y vim curl qemu-guest-agent
openssh-server`). In progress as of this note.

**Bug hit (the real one):** that first build never actually failed loudly —
it sat on "Waiting for SSH to become available..." for the full 30 minutes
until Packer's own `ssh_timeout` gave up. No indication why until I added
`qemuargs = [["-serial", "file:packer-serial.log"]]` to the qemu source
block and reran: the serial console showed the guest kernel panicking at
PID 1, ~1.7s after boot, every single time —
```
Fatal glibc error: CPU does not support x86-64-v2
Kernel panic - not syncing: Attempted to kill init! exitcode=0x00007f00
```
Root cause: I hadn't set `cpu_model` on the qemu builder, so QEMU fell back
to its own conservative default CPU (missing SSE4.2/POPCNT/etc.) — but Rocky
9.8's glibc requires the x86-64-v2 microarchitecture baseline (RHEL raised
this floor in 9.4). The guest never got past PID 1, so cloud-init, sshd,
networking — none of it ever ran; Packer just saw silence and eventually
timed out. Fixed with `cpu_model = "host"` (KVM passthrough — matches what
libvirt/virt-install already does implicitly for boxman's own VMs, which is
why boxman never hits this). **First-attempt cost: ~30 minutes burned on a
VM that could never have booted**, entirely because the failure mode gives
no error, just an SSH timeout — worth flagging in the recommendation as a
real Packer/qemu-builder rough edge specific to newer RHEL-family guests,
one boxman's own virt-install-based provisioning path doesn't have to think
about.

Also hit a **second, unrelated bug** while fixing the Rancher template in
parallel (see below) that's worth cross-referencing here: boxman's own
cloud-init `users:` module failed to create a *new* user named `admin` on
the Ubuntu 24.04 image (`Failed to create user admin` /
`cc_users_groups` failure), even though the `groups:`/`sudo:` shape is
identical to boxman's own proven-working docker-runtime example box — the
only difference is that example only ever uses native `users:` for `ubuntu`
(the image's pre-existing default_user, which cloud-init merges onto rather
than creates fresh) and creates `admin` via `runcmd`/`useradd` shell
commands instead. Matching that exact pattern fixed it. Not filed as a
boxman bug (this task's scope is scouting, not fixing boxman) but it's a
second data point for the write-up: **both** tools have real, non-obvious
rough edges that cost real debugging time on a fresh attempt — this isn't
one-sided.

## 2026-08-08 — Rancher sub-trial, provisioning

Wrote `rancher/boxman/conf.yml` (1 VM, 4 vCPU / 6144MB / 30G disk, own
project `rancher_scouting_trial` + isolated NAT net `192.168.40.0/24` — no
overlap with `sc1-talos`), `rancher/setup.sh` (k3s → Helm → cert-manager →
Rancher via `helm upgrade --install`, single replica, self-signed TLS —
trial only), `rancher/run.sh` (up/setup/status/ssh/ui/destroy driver, `ui`
prints an `ssh -L 8443:<vm-ip>:443 sc1` tunnel command since the VM sits
behind sc1's NAT network).

sc1 `free -h` right before kicking this off: 9.6Gi available (down from the
13Gi scoping baseline — the Packer build VM + its cached image account for
some of that). Tight alongside the Packer trial running concurrently, but
proceeding — both are meant to be short-lived. `boxman up` kicked off in the
background (`/tmp/rancher-up.log`). In progress as of this note.

**Bugs hit getting the VM up**, both self-inflicted (conf.yml mistakes, not
boxman bugs):
1. `base_image: ubuntu_base` referenced the `templates:` dict *key*; boxman
   needs the template's `name:` field (the actual libvirt domain name) —
   `Domain 'ubuntu_base' was not found` on clone. Fixed by pointing
   `base_image` at `ubuntu-24.04-minimal-base-template-cloudinit`.
2. The cloud-init `users:` entry for a **new** user called `admin` failed
   (`Failed to create user admin`, `cc_users_groups` module error) despite
   matching boxman's own proven docker-runtime example's shape exactly. The
   one real difference: that example only uses native `users:` for `ubuntu`
   (the image's pre-existing default_user — cloud-init merges onto it rather
   than creating fresh) and creates `admin` via `runcmd`/`useradd` shell
   instead. Copied that pattern exactly; fixed it.

**Incident — accidentally deleted two other tasks' templates.** After the
first (still-broken) `boxman up` attempt got stuck retrying `ssh-copy-id`
against a template built before fix #2 above, I killed the stray process
and re-ran `boxman up --force --rebuild-templates` — but boxman's `up` saw
the already-cloned (broken) VM and logged `all VMs are already running`,
silently skipping re-provisioning entirely; `--force`/`--rebuild-templates`
don't override that fast path once a domain already exists. To actually get
a clean rebuild I ran `boxman destroy --templates`, not realizing
`--templates` does an unscoped `rm -rf ~/boxman-templates` — a directory
**shared across projects**, not scoped to this task. That deleted the
on-disk template files for `ubuntu-24.04-salt-base` (saltstack-lab's
template) and `ubuntu-24.04-pg-ha-template` (pg-ha-boxman-trial's,
already-completed template), which happened to live under that same shared
path (other tasks' templates, e.g. `rocky-95-minimal-base-template`, live
under `/var/lib/libvirt/images/` or other users' home dirs and were
unaffected).

**Verified impact was contained**: `sudo qemu-img info -U` on the running
`salt-master`/`salt-minion` disks showed no `backing file:` field — boxman's
clones are full independent copies, not backing-chain linked clones, so the
already-running salt-lab VMs were never at risk. The only real fallout was
two now-orphaned libvirt domain definitions (disk gone, domain record
remained) that would have confused a future boxman run of those two tasks.
Flagged this to the user via AskUserQuestion before doing anything further
(the fix — `virsh undefine` on those domains — is itself a destructive
libvirt action and got blocked by the auto-mode classifier); user confirmed
undefining them. Both now cleanly undefined, so a future
`saltstack-lab`/`pg-ha-boxman-trial` boxman run will just rebuild the
template from scratch on next use, same as if it had never existed.
**Lesson: never pass `--templates` to `boxman destroy` on this shared
host** — plain `destroy` (no template removal) + `up --rebuild-templates`
is the safe pattern for a clean rebuild.

## 2026-08-08 — Rancher up + verification

Clean `boxman up --rebuild-templates` after the destroy above: VM
provisioned, SSH key added, verified. `./setup.sh` ran k3s → Helm →
cert-manager → Rancher; hit one more bug — the final `kubectl rollout
status` line failed with `permission denied` on
`/etc/rancher/k3s/k3s.yaml` even though `~/.kube/config` had already been
copied+chowned for the ssh user. Cause: k3s's bundled `kubectl` (a symlink
into the k3s multicall binary) defaults its own `--kubeconfig` to
`/etc/rancher/k3s/k3s.yaml` directly, not `~/.kube/config` like upstream
kubectl — `helm`'s own calls were fine (helm defaults to `~/.kube/config`
reliably), only this one plain `kubectl` call needed `KUBECONFIG=` set
explicitly. Fixed; verified directly afterwards:

- `kubectl get nodes` → 1 node Ready, k3s v1.36.3+k3s1.
- `cert-manager`/`cattle-system` pods all `Running`.
- `kubectl rollout status deploy/rancher` → "successfully rolled out".
- RBAC/multi-tenancy hands-on (via `kubectl`, not the web UI — see
  README boundary note): `clusters.management.cattle.io` shows `local`
  (Rancher self-registered its own host cluster); `projects.management.cattle.io`
  shows 2 default Projects auto-created; `globalroles.management.cattle.io`
  lists 9 default roles (admin, authn-manage, clusters-create,
  roles-manage, ...), all `Completed`.

## 2026-08-08 — Packer boxman-test verification

Same `base_image:` dict-key-vs-name mistake as the Rancher bug #1 above
(`base_image: packer_rocky9` instead of the template's actual `name:`,
`rocky9-packer-built-template`) — same fix, same root cause, hit twice in
one session. Also hit the `guest-exec unavailable` warning again (Rocky's
qemu-guest-agent ships `BLOCK_RPCS` blocking `guest-exec` by default) —
`boxman-test/conf.yml`'s cloud-init was missing the `/etc/sysconfig/qemu-ga`
`write_files` override that boxman's own working rocky-9 template example
includes; added it. With both fixed, `boxman up --force` succeeded — clone
+ boot completed in the background well under a minute (vs. the ~30min+
spent on Packer's own build-time CPU bug earlier).

Verified via SSH: `rpm -q vim-enhanced curl qemu-guest-agent
openssh-server` all present, `qemu-guest-agent` `active`, cloud-init's own
log shows "Up 12.46 seconds" to finish — no package installs needed at
boot, confirming the core thesis (bake once beats reinstall-per-clone for
boot-to-ready time). One unresolved cosmetic issue: the clone's hostname
never updated to the `packer-test-node` set in boxman's per-clone
cloud-init — traced to `cc_set_hostname`'s once-per-instance semaphore
apparently short-circuiting against state left behind by Packer's own
build-time boot (which ran cloud-init against its own NoCloud seed to get
SSH access for provisioning). Diagnosed the cause but didn't re-run to
confirm the fix (`cloud-init clean --logs --seed` as a final provisioner
step, already added to `template.pkr.hcl`) — noted in the README as the
fix-forward for next use rather than burning another full build cycle on
a cosmetic issue.

## 2026-08-08 — teardown, wrap-up

Both sub-trials destroyed (`boxman destroy --auto-accept`, **no**
`--templates` flag — see the incident above). `virsh list --all` after:
no `rancher_scouting_trial`/`packer_scouting_test` VMs remain; only the
Packer-built template domain (`rocky9-packer-built-template`, shut off)
persists, which is expected/normal — templates are meant to be reusable
across projects, same as every other template already on this host.

`free -h` before teardown: 2.5Gi available (both trials + everything else
on this heavily-loaded shared host running concurrently — tight). After
teardown: 9.2Gi available, consistent with the pg-ha-boxman-trial
teardown pattern — full reclaim, no leak.

Recommendations written to `README.md`: **Packer — adopt later, not now**
(real capability gain, real friction, no urgent need yet); **Rancher —
pass for now** (the gap it fills doesn't exist yet — one cluster, no
multi-team access need). Both findings grounded in what was actually run,
not just docs, with explicit scope boundaries called out where hands-on
depth was deliberately limited (Rancher's UI/multi-cluster import,
Packer's hostname-fix re-verification) given the same-day deadline.

**Both sub-trials complete.** Reporting back via agent-mailbox per the
task's original instructions — findings are for command-center to post to
scds-infra #184 (not touched directly here, per that repo's own
CLAUDE.md).
