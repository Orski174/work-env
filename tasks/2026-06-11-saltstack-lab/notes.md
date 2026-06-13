# Notes — saltstack-lab

Running log. Tracks scds-infra #6.

## 2026-06-11 — created

Scaffolded the task. Decided to author in `work-env` (published privately to GitHub)
and execute on **sc1 (scds001)**, a RHEL 9.7 box with KVM/libvirt where boxman runs
from the `boxman` conda env (`~/.conda/envs/boxman/bin/boxman`).

## Step 1 — environment setup (boxman master/minion lab)

**Design:** one minimal Ubuntu 24.04 golden template → cloned into two VMs
(`salt-master`, `salt-minion`) on a NAT net (192.168.77.0/24). Salt is installed
**post-provision** by `setup-salt.sh` over SSH (official Broadcom repo, pinned 3008
LTS), which also assigns roles. Two phases because boxman applies cloud-init at the
*template* level (shared by both clones), so roles can't be set at boot.

### Gotchas hit (and fixes)

1. **Slow cloud-init install races a 120s marker poll.** First attempt baked the Salt
   `apt` install into the template. boxman's `_poll_done_marker` waits a *hardcoded*
   120s (the `cloudinit_timeout` config key is ignored on this path); on a miss it
   skips the template shutdown and then `virt-clone`s the still-running template,
   which fails — clones never created. **Fix:** keep the template minimal (marker
   lands in ~1s) and move the Salt install to `setup-salt.sh`.

2. **Clones collided on one DHCP IP.** Both clones inherited the template's
   `/etc/machine-id`; systemd-networkd derives the DHCP DUID from it, so both VMs
   presented the same identity and the DHCP server gave them the *same* IP
   (192.168.77.37) — one VM became unreachable. **Fix:** `truncate -s 0
   /etc/machine-id` (+ relink `/var/lib/dbus/machine-id`) at the end of the template
   cloud-init so each clone regenerates a unique machine-id at first boot. After the
   fix the two VMs got distinct IPs (.42 and .154).

3. **Minion registered with a stale identity / mismatched key.** The `salt-minion`
   apt postinst auto-starts the service with the default master (`salt`) and
   `id=hostname`, caching `/etc/salt/minion_id` + PKI before our config lands. That
   left the minion stuck on host `salt`, and later key resets caused a master-side
   "cached public key" mismatch (rejected). **Fix (in `setup-salt.sh`):** stop the
   auto-started minion, write `minion.d/master.conf` (master IP + `id: salt-minion`),
   then wipe `/etc/salt/minion_id` and `pki/minion/*` so it registers exactly once.
   Also bumped the key-wait to ~120s (fresh minion needs ~20-40s to key up).

### Working flow (on sc1, from the task dir)

```bash
BOXMAN=~/.conda/envs/boxman/bin/boxman ./run.sh up   # template + 2 clones
./run.sh setup                                        # install Salt, assign roles
./run.sh ssh salt-master                              # salt-key -L / -A -y / test.ping
```

**Step 1 verified (2026-06-13):** master `salt-master` (192.168.77.42) + minion
`salt-minion` (192.168.77.154), both Salt 3008.1. After accepting the key,
`salt '*' test.ping` → `salt-minion: True`; `grains.item id os osrelease` →
`salt-minion / Ubuntu / 24.04`. Acceptance criterion 1 met.

## Step 2 — core concepts (states, pillars, grains, targeting)

Notes taken while reading the Salt docs (saltproject.io / saltstack/salt). Salt is a
**master → minion** system: the `salt-master` daemon holds config + issues commands; each
`salt-minion` connects out to the master (ZeroMQ pub/sub, port 4505/4506), authenticated by
accepted keys. You drive it with **execution modules** (ad-hoc, imperative — e.g.
`salt '*' test.ping`, `pkg.install`) and with **states** (declarative, idempotent desired
state). This lab uses both: execution modules to poke the minion, states for the demo.

### States & SLS files
- A **state** is a declarative "this is how the system should be" block. Salt enforces it
  and reports what (if anything) it changed — so re-running is safe (**idempotent**).
- Written in **`.sls`** files (YAML, rendered through **Jinja** first by default). Live under
  the master's **`file_roots`** (default base env `/srv/salt`), addressed as `salt://...`.
- Each block has an **ID**, a **state function** (`pkg.installed`, `file.managed`,
  `service.running`, ...) and args. The ID is the default `name` if `- name:` is omitted.
- A directory state is `dir/init.sls` and is referenced as just `dir` (so
  `salt://demo/init.sls` ⇒ `state.apply demo`).
- **Requisites** order/relate states: `require` (run after X), `watch` (act if X changed),
  `onchanges`, `require_in`, etc. The demo uses `require` so the config file is written only
  after the package is installed.
- Apply: `state.apply <name>` runs one state tree; `state.apply` (no arg) runs the
  **highstate** = whatever `top.sls` assigns to that minion. `test=True` does a dry run.

### top.sls (the highstate map)
- `top.sls` in `file_roots` maps **targets → state lists** per environment:
  ```yaml
  base:
    'salt-minion':
      - demo
  ```
- Pillar has its own `top.sls` in `pillar_roots` (default `/srv/pillar`) with the same shape,
  mapping targets → pillar `.sls` to expose.

### Grains — minion-side facts
- **Grains** are static facts *about* the minion, collected on the minion at start
  (`os`, `osrelease`, `kernelrelease`, `num_cpus`, `id`, `fqdn`, custom grains, ...).
- Read with `salt '*' grains.items` / `grains.get os`; inside templates as
  `{{ grains['os'] }}`. Good for **targeting** (`-G 'os:Ubuntu'`) and for branching config.
- The demo template reads `grains['id'|'os'|'osrelease'|'kernelrelease'|'num_cpus']`.

### Pillar — master-side, per-minion data
- **Pillar** is secure, targeted data defined *on the master* and handed only to the minions
  it's assigned to (via pillar `top.sls`). The place for config values / secrets, kept out of
  the state logic.
- Read with `salt '*' pillar.items`; in templates as `{{ pillar['demo']['owner'] }}` (or the
  safer `salt['pillar.get']('demo:owner', 'default')`).
- Changes need `salt '*' saltutil.refresh_pillar` to reach minions (cached otherwise).
- Grains vs pillar: **grains = facts the minion reports about itself; pillar = data the master
  assigns to the minion.** The demo template uses both — grains for host facts, pillar for the
  owner/environment/message.

### Targeting
- Pick which minions a command/state hits. Globs by default (`salt '*' ...`,
  `salt 'salt-*' ...`); also `-E` pcre, `-L` list, `-G` grains (`-G 'os:Ubuntu'`),
  `-I` pillar, `-C` compound. In `top.sls`, `- match: grain|pcre|list|pillar` selects the
  matcher. This lab has one minion, so `'*'` and `'salt-minion'` are equivalent here.

## Step 3 — minimal demo state + idempotency proof (2026-06-13)

Wrote a minimal demo state that **installs a package and manages a templated config file**,
applied it master→minion, then re-applied to prove idempotency.

### What's in the state (`salt/states/` + `salt/pillar/`, synced to master `/srv`)
- `states/demo/init.sls` — two states:
  - `demo-package` → `pkg.installed: htop`
  - `/etc/salt-demo.conf` → `file.managed` from `salt://demo/files/banner.j2`
    (`template: jinja`, mode `0644`), with `require` on `demo-package`.
- `states/demo/files/banner.j2` — Jinja template reading **grains** (id/os/kernel/cpus) and
  **pillar** (owner/environment/message).
- `pillar/demo.sls` — the pillar values; `pillar/top.sls` + `states/top.sls` assign `demo`
  to `salt-minion`.

Deploy helpers added to `run.sh`: `sync` tars `salt/states`→`/srv/salt` and
`salt/pillar`→`/srv/pillar` on the master and runs `saltutil.refresh_pillar`; `apply [state]`
runs `salt '*' state.apply [state]`.

### Exact commands (on sc1, from the task dir; `BOXMAN=~/.conda/envs/boxman/bin/boxman`)
```bash
./run.sh sync                 # push states+pillar to master /srv, refresh pillar
./run.sh apply demo           # first apply  -> changes
./run.sh apply demo           # second apply -> NO changes (idempotent)
# (clean-slate reset used for the proof: on the minion, apt-get purge -y htop && rm -f /etc/salt-demo.conf)
```

### First run — changes (changed=2)
```
          ID: demo-package      Function: pkg.installed   Name: htop
     Comment: The following packages were installed/updated: htop
     Changes:  htop: new: 3.3.0-4build1 / old:
          ID: /etc/salt-demo.conf   Function: file.managed
     Comment: File /etc/salt-demo.conf updated
     Changes:  diff: New file   mode: 0644
Summary for salt-minion:  Succeeded: 2 (changed=2)  Failed: 0
```

### Second run — idempotent (changed=0)
```
          ID: demo-package      Function: pkg.installed   Name: htop
     Comment: All specified packages are already installed
     Changes:           (empty)
          ID: /etc/salt-demo.conf   Function: file.managed
     Comment: File /etc/salt-demo.conf is in the correct state
     Changes:           (empty)
Summary for salt-minion:  Succeeded: 2  Failed: 0     <- no "changed=" => zero changes
```

### Rendered config on the minion (`/etc/salt-demo.conf`) — grains + pillar merged
```
# Rendered on ubuntu-24.04-salt-base from salt://demo/files/banner.j2
[host]
id = salt-minion / os = Ubuntu 24.04 / kernel = 6.8.0-31-generic / cpus = 2
[demo]
owner = orski / environment = lab / message = Provisioned by SaltStack 3008 LTS - saltstack-lab demo.
```
(`fqdn` grain shows the template hostname `ubuntu-24.04-salt-base` — clones inherit it; the
Salt `id` is set correctly to `salt-minion` via minion config. Cosmetic only.)

**Steps 2 & 3 done.** Acceptance criteria: demo state installs a package + manages a config
file (✓), applied master→minion (✓), re-apply reports zero changes (✓).

## Step 4 — SaltStack vs Ansible write-up

*TODO — step 4.*
