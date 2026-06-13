#!/usr/bin/env bash
# Install Salt and assign roles to the two provisioned VMs, then start services.
#
# The boxman template is intentionally Salt-free (see boxman/conf.yml for why),
# so this script does the Salt install over SSH on each running VM, from the
# official Broadcom repo pinned to the 3008 LTS series:
#   - salt-master VM: install + start salt-master
#   - salt-minion VM: install salt-minion, point it at the master, start it
# then wait for the minion's key to show up as pending on the master.
#
# Key acceptance is left as a manual step (the instructive bit) unless --accept
# is passed. Safe to re-run (idempotent).
#
# Run from the task root on the host where boxman provisioned (sc1):
#   ./setup-salt.sh [--accept]
set -euo pipefail

WORKSPACE="${SALT_LAB_WORKSPACE:-$HOME/workspaces/salt-lab}"
ACCEPT=0
[ "${1:-}" = "--accept" ] && ACCEPT=1

# --- locate boxman's generated ssh_config ---
SSH_CONFIG="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1 || true)"
if [ -z "$SSH_CONFIG" ]; then
  echo "ERROR: ssh_config not found under $WORKSPACE — has 'boxman up' run?" >&2
  exit 1
fi
echo ">> using ssh_config: $SSH_CONFIG"

# --- resolve the host aliases boxman wrote for each VM ---
MASTER_HOST="$(awk '/^Host .*salt-master/{print $2; exit}' "$SSH_CONFIG")"
MINION_HOST="$(awk '/^Host .*salt-minion/{print $2; exit}' "$SSH_CONFIG")"
if [ -z "$MASTER_HOST" ] || [ -z "$MINION_HOST" ]; then
  echo "ERROR: could not find salt-master/salt-minion Host entries in $SSH_CONFIG" >&2
  grep '^Host ' "$SSH_CONFIG" >&2 || true
  exit 1
fi
echo ">> master host alias: $MASTER_HOST"
echo ">> minion host alias: $MINION_HOST"

m() { ssh -F "$SSH_CONFIG" -o LogLevel=ERROR "$MASTER_HOST" "$@"; }   # run on master
n() { ssh -F "$SSH_CONFIG" -o LogLevel=ERROR "$MINION_HOST" "$@"; }   # run on minion

# Snippet: configure the official Salt repo (Broadcom), pinned to 3008 LTS.
read -r -d '' SALT_REPO <<'EOS' || true
set -e
sudo mkdir -m 755 -p /etc/apt/keyrings
curl -fsSL https://packages.broadcom.com/artifactory/api/security/keypair/SaltProjectKey/public \
  | sudo gpg --dearmor -o /etc/apt/keyrings/salt-archive-keyring.pgp
curl -fsSL https://github.com/saltstack/salt-install-guide/releases/latest/download/salt.sources \
  | sudo tee /etc/apt/sources.list.d/salt.sources >/dev/null
printf 'Package: salt-*\nPin: version 3008.*\nPin-Priority: 1001\n' \
  | sudo tee /etc/apt/preferences.d/salt-pin-1001 >/dev/null
sudo apt-get update -q
EOS

# --- install + start the master ---
echo ">> [master] installing salt-master (official repo, 3008 LTS) ..."
m "$SALT_REPO"$'\n'"sudo DEBIAN_FRONTEND=noninteractive apt-get install -y salt-master"
echo ">> [master] starting salt-master ..."
m 'sudo systemctl enable --now salt-master'

# --- master's IP on the nat1 lab network (192.168.77.x) ---
MASTER_IP="$(m "ip -4 -o addr show | awk '{print \$4}' | cut -d/ -f1 | grep '^192.168.77.' | head -1")"
if [ -z "$MASTER_IP" ]; then
  echo "ERROR: could not determine master IP on 192.168.77.0/24" >&2
  exit 1
fi
echo ">> master IP (lab net): $MASTER_IP"

# --- install the minion, point it at the master, start it ---
echo ">> [minion] installing salt-minion (official repo, 3008 LTS) ..."
n "$SALT_REPO"$'\n'"sudo DEBIAN_FRONTEND=noninteractive apt-get install -y salt-minion"
echo ">> [minion] configuring + starting salt-minion ..."
# The apt postinst auto-starts salt-minion with the default master ('salt') and
# id=hostname, caching a stale /etc/salt/minion_id and PKI. Stop it, write our
# config, then wipe that stale identity so the minion registers exactly once as
# 'salt-minion' against the real master — otherwise the master caches a key that
# mismatches and rejects the minion.
n 'sudo systemctl stop salt-minion 2>/dev/null || true'
n "printf 'master: %s\nid: salt-minion\n' '$MASTER_IP' | sudo tee /etc/salt/minion.d/master.conf >/dev/null"
n 'sudo rm -f /etc/salt/minion_id; sudo rm -rf /etc/salt/pki/minion/*'
n 'sudo systemctl enable --now salt-minion'

# --- wait for the minion key to register as pending on the master ---
# A fresh minion takes ~20-40s to generate keys and reach the master.
echo ">> waiting for minion key to reach the master (up to ~120s) ..."
for _ in $(seq 1 60); do
  if m 'sudo salt-key -L' 2>/dev/null | grep -q 'salt-minion'; then break; fi
  sleep 2
done

echo
echo "================ salt-key -L (on master) ================"
m 'sudo salt-key -L' || true
echo "========================================================="

if [ "$ACCEPT" -eq 1 ]; then
  echo ">> accepting all pending keys (--accept) ..."
  m 'sudo salt-key -A -y'
  echo ">> verifying with test.ping (minion needs a few seconds after accept) ..."
  for _ in $(seq 1 10); do
    if m "sudo salt '*' test.ping" 2>/dev/null | grep -q 'True'; then break; fi
    sleep 3
  done
  m "sudo salt '*' test.ping"
else
  cat <<EOF

Master + minion are running. The minion key is pending acceptance.
Accept it by hand (the instructive step):

  ssh -F "$SSH_CONFIG" $MASTER_HOST
  sudo salt-key -L            # list keys (Unaccepted Keys: salt-minion)
  sudo salt-key -A -y         # accept all pending
  sudo salt '*' test.ping     # should return: salt-minion: True

Or re-run this script with --accept to do it automatically.
EOF
fi
