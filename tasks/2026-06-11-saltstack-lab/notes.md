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

## Concepts write-up (states, pillars, grains, vs Ansible)

*TODO — steps 2 & 4.*
