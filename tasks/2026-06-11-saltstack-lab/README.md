# saltstack-lab

Created: 2026-06-11 · Tracks scds-infra issue #6.

## Goal

Hands-on SaltStack: stand up a Salt **master + one minion** via boxman VMs, apply
a minimal state end-to-end (install a package + manage a config file), confirm
idempotency, and write up core concepts (states, pillars, grains) and a
SaltStack-vs-Ansible comparison.

## Where this runs

Authored on the workstation, **executed on `sc1` (scds001)** — a RHEL 9.7 box with
KVM + libvirt where boxman provisions the VMs. Workflow: edit here → `git push` →
`git pull` on sc1 → run boxman + the scripts on sc1.

## External repos / dependencies

- **boxman** — `$REPOS_ROOT/boxman` on sc1 (`~/git/boxman`), run from the `boxman`
  conda env (`~/.conda/envs/boxman/bin/boxman`). The lab is defined in
  `boxman/conf.yml`. boxman drives libvirt/KVM to build a minimal golden Ubuntu
  24.04 template and clone two VMs from it; Salt is installed afterwards by
  `setup-salt.sh`.

## Layout

```text
boxman/conf.yml   the lab: 1 template + cluster of 2 VMs (salt-master, salt-minion)
setup-salt.sh     post-provision: install Salt, assign roles, start services, wait for key
run.sh            thin driver around boxman (up / setup / ping / ssh / destroy)
salt/states/      Salt states (.sls) — the demo state (step 3)
salt/pillar/      Salt pillar data (step 3)
notes.md          running log + the write-up (states/pillars/grains, vs Ansible)
```

## How to run (on sc1)

```bash
# one-time: make boxman runnable (editable install into a venv/pyenv)
pip install -e ~/git/boxman          # or however boxman is set up on sc1

cd ~/git/work-env/tasks/2026-06-11-saltstack-lab

./run.sh up        # build minimal template + clone the 2 VMs
./run.sh setup     # install Salt, assign roles, start services, show pending key
# accept the minion key by hand (the instructive step):
./run.sh ssh salt-master
#   sudo salt-key -L && sudo salt-key -A -y && sudo salt '*' test.ping
./run.sh destroy   # tear the lab down
```

`./run.sh setup --accept` auto-accepts the key and runs `test.ping` instead.

Apply the demo state (install a package + manage a templated config file) and
prove idempotency:

```bash
./run.sh sync          # push salt/states -> master:/srv/salt, salt/pillar -> /srv/pillar
./run.sh apply demo    # first apply  -> changes (htop installed, config written)
./run.sh apply demo    # second apply -> NO changes (idempotent)
```

## Why two phases (boxman up, then setup-salt.sh)

Two reasons Salt is installed *post-provision* rather than baked into the template:

1. **cloud-init is template-level.** boxman applies cloud-init once to the golden
   image, then clones it — so it can't differentiate a master from a minion at boot.
2. **The template build polls the cloud-init "done marker" for only 120s (hardcoded
   in this boxman version), and on a miss it skips the template shutdown and then
   fails to clone the still-running template.** A full Salt `apt` install can't finish
   in 120s, so baking it in races-and-loses that poll and corrupts the provision.

So the template stays minimal (marker lands in seconds) and `setup-salt.sh` installs
Salt over SSH on each running VM (official Broadcom repo, pinned 3008 LTS): it starts
`salt-master` on one node and points `salt-minion` at the master on the other.

## Inputs

None external. The Ubuntu cloud image is fetched + cached by boxman on first `up`.

## Outputs

VMs live in libvirt on sc1; boxman artifacts (ssh_config, keys, template qcow2) in
`~/workspaces/salt-lab` on sc1. Nothing large is committed.
