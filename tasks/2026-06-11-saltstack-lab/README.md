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

- **boxman** — `$REPOS_ROOT/boxman` on sc1 (`~/git/boxman`). The lab is defined in
  `boxman/conf.yml`. boxman drives libvirt/KVM to build a golden Ubuntu 24.04
  template (Salt baked in) and clone two VMs from it.

## Layout

```text
boxman/conf.yml   the lab: 1 template + cluster of 2 VMs (salt-master, salt-minion)
setup-salt.sh     post-provision: assign roles, start services, wait for minion key
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

./run.sh up        # build template (Salt baked in via cloud-init) + clone 2 VMs
./run.sh setup     # assign roles, start salt-master + salt-minion, show pending key
# accept the minion key by hand (the instructive step):
./run.sh ssh salt-master
#   sudo salt-key -L && sudo salt-key -A -y && sudo salt '*' test.ping
./run.sh destroy   # tear the lab down
```

`./run.sh setup --accept` auto-accepts the key and runs `test.ping` instead.

## Why two phases (boxman up, then setup-salt.sh)

boxman applies cloud-init at the **template** level, then clones that template to
create each VM — so cloud-init is *shared* and can't make one node a master and
the other a minion. The template therefore boots both VMs with `salt-master` +
`salt-minion` installed (official Broadcom repo, pinned 3008 LTS) but **disabled**
and identity-less; `setup-salt.sh` then enables the right service per node and
points the minion at the master.

## Inputs

None external. The Ubuntu cloud image is fetched + cached by boxman on first `up`.

## Outputs

VMs live in libvirt on sc1; boxman artifacts (ssh_config, keys, template qcow2) in
`~/workspaces/salt-lab` on sc1. Nothing large is committed.
