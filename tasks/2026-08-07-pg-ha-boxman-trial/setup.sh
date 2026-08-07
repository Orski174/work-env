#!/usr/bin/env bash
# Post-provision: install Docker (fallback if cloud-init's docker.io didn't land
# within boxman's ~120s done-marker poll), push patroni/ assets, render
# patroni.yml + .env per node, build the derived CNPG+Patroni image, and bring
# up etcd (quorum first) then Patroni on pg1 -> pg2 -> pg3 in order.
#
# Two-phase pattern (cloud-init stays minimal, heavy lifting happens here over
# SSH) mirrors saltstack-lab/setup-salt.sh, for the same reason: boxman's
# hardcoded ~120s cloud-init done-marker poll can't tolerate a slow install
# baked into the template.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

WORKSPACE="${PG_HA_WORKSPACE:-$HOME/workspaces/boxmandev/pg-ha-boxman-trial}"
NODES=(pg1 pg2 pg3)

ssh_config() {
  local cfg
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  printf '%s\n' "$cfg"
}

host_for() {  # cfg pattern -> boxman Host alias
  local host
  host="$(awk -v p="$2" '$1=="Host" && $2 ~ p {print $2; exit}' "$1")"
  [ -n "$host" ] || { echo "no Host matching '$2' in $1" >&2; exit 1; }
  printf '%s\n' "$host"
}

ip_for() {  # cfg host_alias -> Hostname value
  awk -v h="$2" '
    $1=="Host" { inblock = ($2==h) }
    inblock && tolower($1)=="hostname" { print $2; exit }
  ' "$1"
}

ssh_to() {  # cfg host_alias cmd...
  local cfg="$1" host="$2"; shift 2
  ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=10 "$host" "$@"
}

CFG="$(ssh_config)"
declare -A ALIAS IP
for n in "${NODES[@]}"; do
  ALIAS[$n]="$(host_for "$CFG" "$n\$")"
  IP[$n]="$(ip_for "$CFG" "${ALIAS[$n]}")"
  [ -n "${IP[$n]}" ] || { echo "no HostName for ${ALIAS[$n]} in $CFG" >&2; exit 1; }
  echo ">> $n -> ${ALIAS[$n]} (${IP[$n]})"
done

echo "== ensuring docker is present on all nodes =="
for n in "${NODES[@]}"; do
  ssh_to "$CFG" "${ALIAS[$n]}" \
    'command -v docker >/dev/null 2>&1 || (sudo apt-get update && sudo apt-get install -y docker.io && sudo systemctl enable --now docker)'
  ssh_to "$CFG" "${ALIAS[$n]}" 'sudo usermod -aG docker $USER || true'
done

echo "== pushing patroni/ assets to all nodes =="
for n in "${NODES[@]}"; do
  ssh_to "$CFG" "${ALIAS[$n]}" 'mkdir -p ~/patroni'
  tar -C "$HERE/patroni" --exclude=rendered -cf - . | ssh -F "$CFG" "${ALIAS[$n]}" 'tar -C ~/patroni -xf -'
done

echo "== building the derived image on pg1 to detect Postgres bin_dir =="
ssh_to "$CFG" "${ALIAS[pg1]}" 'cd ~/patroni && sudo docker build -t pg-ha-trial-patroni .'
PG_BIN_DIR="$(ssh_to "$CFG" "${ALIAS[pg1]}" \
  'sudo docker run --rm pg-ha-trial-patroni sh -c "dirname \$(command -v postgres)"' | tr -d '\r')"
[ -n "$PG_BIN_DIR" ] || { echo "could not detect postgres bin_dir in the built image" >&2; exit 1; }
echo ">> detected PG_BIN_DIR=$PG_BIN_DIR"

echo "== generating cluster passwords =="
REPL_PASS="$(openssl rand -hex 16)"
SUPERUSER_PASS="$(openssl rand -hex 16)"
echo ">> generated via 'openssl rand -hex 16' (random per run, not a fixed default — see notes.md)"

mkdir -p "$HERE/patroni/rendered"
for n in "${NODES[@]}"; do
  sed \
    -e "s|__NODE_NAME__|$n|g" \
    -e "s|__NODE_IP__|${IP[$n]}|g" \
    -e "s|__PG1_IP__|${IP[pg1]}|g" \
    -e "s|__PG2_IP__|${IP[pg2]}|g" \
    -e "s|__PG3_IP__|${IP[pg3]}|g" \
    -e "s|__PG_BIN_DIR__|$PG_BIN_DIR|g" \
    -e "s|__REPL_PASS__|$REPL_PASS|g" \
    -e "s|__SUPERUSER_PASS__|$SUPERUSER_PASS|g" \
    "$HERE/patroni/patroni.yml.tmpl" > "$HERE/patroni/rendered/patroni.$n.yml"

  cat > "$HERE/patroni/rendered/$n.env" <<EOF
NODE_NAME=$n
NODE_IP=${IP[$n]}
PG1_IP=${IP[pg1]}
PG2_IP=${IP[pg2]}
PG3_IP=${IP[pg3]}
EOF
done

echo "== pushing rendered patroni.yml + .env to each node =="
for n in "${NODES[@]}"; do
  scp -F "$CFG" "$HERE/patroni/rendered/patroni.$n.yml" "${ALIAS[$n]}:~/patroni/patroni.yml"
  scp -F "$CFG" "$HERE/patroni/rendered/$n.env" "${ALIAS[$n]}:~/patroni/.env"
done

echo "== building patroni image on pg2/pg3 (pg1 already built) =="
for n in pg2 pg3; do
  ssh_to "$CFG" "${ALIAS[$n]}" 'cd ~/patroni && sudo docker build -t pg-ha-trial-patroni . && sudo -E docker compose build patroni' 2>&1 || \
    ssh_to "$CFG" "${ALIAS[$n]}" 'cd ~/patroni && sudo docker compose build patroni'
done

echo "== starting etcd on all 3 nodes (quorum needs 2-of-3) =="
for n in "${NODES[@]}"; do
  ssh_to "$CFG" "${ALIAS[$n]}" 'cd ~/patroni && sudo docker compose up -d etcd'
done
sleep 10

echo "== starting patroni on pg1, waiting for it to become Leader =="
ssh_to "$CFG" "${ALIAS[pg1]}" 'cd ~/patroni && sudo docker compose up -d patroni'
for i in $(seq 1 30); do
  out="$(ssh_to "$CFG" "${ALIAS[pg1]}" 'sudo docker compose exec -T patroni patronictl -c /etc/patroni.yml list' 2>/dev/null || true)"
  if echo "$out" | grep -q "Leader"; then
    echo ">> pg1 is Leader after ~$((i*5))s"
    break
  fi
  sleep 5
done

echo "== starting patroni on pg2 and pg3 (join as replicas) =="
for n in pg2 pg3; do
  ssh_to "$CFG" "${ALIAS[$n]}" 'cd ~/patroni && sudo docker compose up -d patroni'
done

echo "== waiting for replicas to catch up =="
sleep 20

echo "== final cluster state =="
ssh_to "$CFG" "${ALIAS[pg1]}" 'sudo docker compose exec -T patroni patronictl -c /etc/patroni.yml list' 2>&1

echo
echo "Passwords for this run (not stored anywhere else — copy into notes.md if needed):"
echo "  replicator: $REPL_PASS"
echo "  postgres:   $SUPERUSER_PASS"
