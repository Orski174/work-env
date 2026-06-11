#!/usr/bin/env bash
# Thin driver around boxman for the Salt lab. Meant to run on sc1.
#
#   ./run.sh up               provision: build template + clone the 2 VMs
#   ./run.sh setup [--accept] assign Salt roles + start services
#   ./run.sh ssh <vm>         ssh into salt-master | salt-minion
#   ./run.sh ping             salt master -> minion test.ping (run on master)
#   ./run.sh status           boxman ps for this project
#   ./run.sh destroy          tear the lab down
#
# boxman is located via $BOXMAN, then PATH, then a `python -m boxman` fallback
# against ~/git/boxman.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

CONF="boxman/conf.yml"
WORKSPACE="${SALT_LAB_WORKSPACE:-$HOME/workspaces/salt-lab}"

boxman() {
  if [ -n "${BOXMAN:-}" ]; then "$BOXMAN" "$@";
  elif command -v boxman >/dev/null 2>&1; then command boxman "$@";
  else python -m boxman "$@"; fi
}

ssh_to() {  # ssh into a VM by its short name (salt-master / salt-minion)
  local cfg host
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  host="$(awk -v p="$1" '$1=="Host" && $2 ~ p {print $2; exit}' "$cfg")"
  [ -n "$host" ] || { echo "no Host matching '$1' in $cfg" >&2; exit 1; }
  shift
  exec ssh -F "$cfg" "$host" "$@"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)       boxman --conf "$CONF" up "$@" ;;
  setup)    ./setup-salt.sh "$@" ;;
  ssh)      ssh_to "${1:-salt-master}" "${@:2}" ;;
  ping)     ssh_to salt-master "sudo salt '*' test.ping" ;;
  status|ps) boxman --conf "$CONF" ps "$@" ;;
  destroy)  boxman --conf "$CONF" destroy "$@" ;;
  *) echo "usage: ./run.sh {up|setup [--accept]|ssh <vm>|ping|status|destroy}" >&2; exit 2 ;;
esac
