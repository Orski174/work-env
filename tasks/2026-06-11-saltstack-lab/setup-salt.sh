#!/usr/bin/env bash
# Assign Salt roles to the two provisioned VMs and start services.
#
# boxman applies cloud-init at the template level, so both clones boot with
# salt-master + salt-minion installed but DISABLED and identity-less. This
# script differentiates them:
#   - salt-master VM: start the salt-master service
#   - salt-minion VM: point /etc/salt/minion at the master, start salt-minion
# then wait for the minion's key to show up as pending on the master.
#
# Key acceptance is left as a manual step (the instructive bit) unless --accept
# is passed. Safe to re-run (idempotent).
#
# Run from the task root on the host where boxman provisioned (sc1):
#   ./setup-salt.sh [--accept]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

# --- sanity: salt actually baked into the image? ---
if ! m 'command -v salt-master' >/dev/null 2>&1; then
  echo "ERROR: salt-master not installed on the master VM — template build/cloud-init likely failed." >&2
  echo "       Check /var/log/cloud-init-output.log inside the VM." >&2
  exit 1
fi

# --- master's IP on the nat1 lab network (192.168.77.x) ---
MASTER_IP="$(m "ip -4 -o addr show | awk '{print \$4}' | cut -d/ -f1 | grep '^192.168.77.' | head -1")"
if [ -z "$MASTER_IP" ]; then
  echo "ERROR: could not determine master IP on 192.168.77.0/24" >&2
  exit 1
fi
echo ">> master IP (lab net): $MASTER_IP"

# --- configure + start the master ---
echo ">> starting salt-master ..."
m 'sudo systemctl enable --now salt-master'

# --- point the minion at the master, give it a stable id, start it ---
echo ">> configuring + starting salt-minion ..."
n "printf 'master: %s\nid: salt-minion\n' '$MASTER_IP' | sudo tee /etc/salt/minion.d/master.conf >/dev/null"
n 'sudo systemctl enable --now salt-minion'
n 'sudo systemctl restart salt-minion'   # pick up config if it was already running

# --- wait for the minion key to register as pending on the master ---
echo ">> waiting for minion key to reach the master ..."
for _ in $(seq 1 30); do
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
  echo ">> verifying with test.ping ..."
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
