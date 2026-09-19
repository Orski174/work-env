# packer-rancher-scouting

Created: 2026-08-08 · Tracks scds-infra #184 ("learn about packer and rancher"), sprint-011.

## Goal

Tech-scouting pass on two tools with plausible fit in the current stack:

- **Packer** — could it replace boxman's manually-authored cloud-init base VM
  templates (e.g. `rocky-95-minimal-base-template`) with a repeatable,
  code-defined image pipeline?
- **Rancher** — Kubernetes cluster management platform; evaluate as a
  potential complement/alternative to the current Omni+Talos management path
  for the sc1 `sc1-talos` cluster.

Deliverable: a short write-up with a recommendation for each (adopt / adopt
later / pass) — see [Recommendations](#recommendations) below.

## Where this runs

Authored on the workstation, **executed on `sc1` (scds001)** — a RHEL 9.7 box
with KVM + libvirt where boxman provisions VMs. Workflow: edit here → `git
push` → `git pull` on sc1 → run there.

## External repos / dependencies

- **boxman** — `~/git/boxman` on sc1, conda env `boxman`
  (`~/.conda/envs/boxman/bin/boxman`). Both sub-trials provision VMs through it.
- Neither HashiCorp Packer, k3s, nor Helm are installed on sc1 — all three are
  installed fresh as part of these trials. Note: `/usr/sbin/packer` already
  exists on sc1 but is `cracklib-packer` (password-dictionary tool), unrelated
  to HashiCorp Packer — don't rely on it.

## Layout

```text
packer/
  template.pkr.hcl           qemu builder, Rocky 9.x qcow2 comparable to boxman's own template
  http/                       NoCloud seed for Packer's own SSH communicator (build-time only)
  boxman-test/conf.yml        boxman template pointed at the built qcow2 — proves it clones/boots
  run.sh                      install-packer / build / up / status / ssh / destroy / clean driver
rancher/
  boxman/conf.yml             1 throwaway k3s VM (own project/network — does not touch sc1-talos)
  setup.sh                    post-provision: k3s + helm + cert-manager + Rancher
  run.sh                      up / setup / status / ssh / ui / destroy driver
notes.md                    running log across both sub-investigations (bugs hit, fixes, an incident)
```

## How to run (on sc1)

```bash
cd ~/git/work-env/tasks/2026-08-08-packer-rancher-scouting

# Packer
cd packer && ./run.sh install-packer && ./run.sh build && ./run.sh up && ./run.sh destroy

# Rancher
cd ../rancher && ./run.sh up && ./run.sh setup && ./run.sh status
./run.sh ui        # prints the SSH tunnel command for the web UI
./run.sh destroy
```

## Inputs

None external. Cloud images / install media are fetched by boxman or Packer
on first run.

## Outputs

VMs live in libvirt on sc1 while a trial is running; both sub-trials were
torn down (`./run.sh destroy`) after findings were captured — nothing is
left running. boxman/Packer artifacts lived under
`~/workspaces/boxmandev/{packer_scouting_test,rancher_scouting_trial}` on
sc1, also removed by destroy. Nothing large is committed here.

## Recommendations

### Packer — adopt later, not now

**What was actually run:** built a Rocky 9.8 qcow2 via the Packer `qemu`
builder from the same upstream GenericCloud image boxman's own
`rocky-9.7-minimal-base-template-cloudinit` template uses, with the
package set boxman installs via cloud-init (`vim`, `curl`,
`qemu-guest-agent`, `openssh-server`) baked in at build time instead.
Pointed a boxman template's `image:` at the resulting qcow2
(`file://…`) and cloned/booted one VM from it — confirmed via SSH:
packages present (`rpm -q` clean), `qemu-guest-agent` active, and a
**~12s boot-to-ready** (cloud-init's own log: "Up 12.46 seconds") since
nothing needed installing at boot. That's the real win Packer offers:
a fleet's base image becomes a versioned, rebuild-on-demand artifact
instead of "whatever `dnf`/`apt` resolved to on the day this particular
VM happened to be cloned."

**But boxman is not starting from zero.** It already has its own
declarative image pipeline — the `templates:` block in `conf.yml`
(`boxman create-templates` / auto-creation on `up`) — which is simpler
(one YAML block, no separate build tool, no extra state to manage) and
already does 90% of what this trial demonstrated, just via
reinstall-every-template-build rather than bake-once. Packer's actual
edge is the parts boxman's mechanism doesn't have: a real provisioner
ecosystem (Ansible, multiple shell stages, not just a single inline
cloud-init blob), multi-builder support (the same template could target
non-libvirt backends later), and a genuinely versioned/rebuildable
artifact story.

**Real friction hit, not just theoretical:** three distinct, non-obvious
bugs on the very first attempt (full detail + fixes in `notes.md`):
- A stale pinned Rocky point-release URL (404) — a rot problem shared
  with boxman's own checked-in example conf, not Packer-specific.
- **~30 minutes silently burned** on a VM that could never boot
  (`Fatal glibc error: CPU does not support x86-64-v2`, from not setting
  `cpu_model` on the qemu builder) — invisible without capturing the
  serial console by hand. boxman/virt-install never hits this because it
  passes through the host CPU implicitly.
- A second, subtler bug (cloud-init state from Packer's own build-time
  boot leaking into the final image, causing boxman's per-clone hostname
  to not apply) — fixed with `cloud-init clean --logs --seed` as the
  last provisioner step, but easy to miss and not obviously connected to
  the symptom.

None of these are dealbreakers, but they're real evidence that adopting
Packer here trades boxman's "one simple mechanism, already working" for
"a more capable but sharper-edged second tool," for a benefit (faster
clone-to-ready) that mostly matters at a fleet size or CI cadence this
stack isn't at yet.

**Recommendation: adopt later, not now.** Worth revisiting if either (a)
template rebuild time/reliability becomes an actual pain point as the
fleet of boxman-provisioned lab/trial VMs grows, or (b) there's a need to
target a non-libvirt backend from the same image definition. Until then,
boxman's own `templates:` mechanism is simpler and already good enough.
If revisited, start from this task's `template.pkr.hcl` +
`boxman-test/conf.yml` (working, with all three bugs above already fixed)
rather than from scratch.

### Rancher — pass for sc1-talos, no compelling gap to fill

**What was actually run:** a throwaway single-node k3s VM (never touched
the live `sc1-talos` cluster), Rancher installed via its documented Helm
path (cert-manager → `rancher-latest/rancher`), verified via SSH/kubectl:
k3s node Ready, cert-manager and Rancher pods Running, deployment rollout
succeeded. Confirmed hands-on (via `kubectl`, not a full UI click-through
— see boundary below) that Rancher self-registers its host cluster as
`local`, auto-creates default Projects (`p-8f7wv`, `p-g967b`), and ships a
working set of default `GlobalRoles` (admin, authn-manage,
clusters-create, roles-manage, ...) — real Project-scoped
multi-tenancy/RBAC machinery, functional out of the box.

**Explicit scope boundary:** did not import/register the live `sc1-talos`
cluster into Rancher, and did not stand up a second cluster to exercise
multi-cluster management live — a same-day scouting ticket didn't justify
touching a shared KT/demo resource (with its own already-open flux issue)
or doubling the VM footprint on an already memory-tight sc1 (9-13Gi
available across this session; Rancher's management pods alone want a
non-trivial slice of that). Multi-cluster import mechanics were assessed
from Rancher's own docs/CRD surface (`clusterregistrationtokens`,
`clusters.management.cattle.io`) rather than proven live: importing an
existing cluster deploys a `cattle-cluster-agent` into the target and
requires that cluster be network-reachable from wherever Rancher's
management server runs — for `sc1-talos` specifically, meaning either
Rancher's management cluster needs a network path to the Talos nodes, or
vice versa, neither of which exists today without deliberately wiring it.

**Recommendation: pass, for now.** The gap Rancher fills — a UI/RBAC
layer over multiple clusters — isn't a gap that exists today: there's one
k8s cluster (`sc1-talos`), managed through Omni (which already owns
cluster lifecycle/node management) plus `kubectl`/`flux`. Rancher's value
proposition is real but aimed at *multiple* clusters and *multiple*
users/teams needing scoped access — neither is the current situation.
Adding Rancher now would mean running and maintaining a second
management plane (its own Helm release, cert-manager dependency, upgrade
cadence) for capabilities (Project RBAC, multi-cluster fleet view) that
aren't being used yet. Revisit if either changes: a second real cluster
appears, or multiple people/teams need scoped (non-admin) access to
`sc1-talos` — at that point, this task's `rancher/boxman/conf.yml` +
`setup.sh` are a working starting point, and the actual open question
becomes reachability between Rancher's management cluster and Talos'
node network, not whether the install itself works (it does).
