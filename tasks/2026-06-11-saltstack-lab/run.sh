#!/usr/bin/env bash
# Thin driver around boxman for the Salt lab. Meant to run on sc1.
#
#   ./run.sh up               provision: build template + clone the 2 VMs
#   ./run.sh setup [--accept] assign Salt roles + start services
#   ./run.sh sync             push salt/states -> master:/srv/salt, pillar -> /srv/pillar
#   ./run.sh apply [state]    salt '*' state.apply [state] on the master (default: demo)
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

ssh_config() {  # path to boxman's generated ssh_config
  local cfg
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  printf '%s\n' "$cfg"
}

host_for() {  # resolve the boxman Host alias matching a short name; args: cfg pattern
  local host
  host="$(awk -v p="$2" '$1=="Host" && $2 ~ p {print $2; exit}' "$1")"
  [ -n "$host" ] || { echo "no Host matching '$2' in $1" >&2; exit 1; }
  printf '%s\n' "$host"
}

ssh_to() {  # ssh into a VM by its short name (salt-master / salt-minion)
  local cfg host
  cfg="$(ssh_config)"
  host="$(host_for "$cfg" "$1")"
  shift
  exec ssh -F "$cfg" "$host" "$@"
}

sync_states() {  # push local states + pillar into the master's file/pillar roots
  local cfg master
  cfg="$(ssh_config)"; master="$(host_for "$cfg" salt-master)"
  [ -d salt/states ] && [ -d salt/pillar ] || { echo "salt/states + salt/pillar must exist" >&2; exit 1; }
  echo ">> syncing salt/states -> $master:/srv/salt"
  tar -C salt/states -cf - . | ssh -F "$cfg" "$master" 'sudo mkdir -p /srv/salt && sudo tar -C /srv/salt -xf -'
  echo ">> syncing salt/pillar -> $master:/srv/pillar"
  tar -C salt/pillar -cf - . | ssh -F "$cfg" "$master" 'sudo mkdir -p /srv/pillar && sudo tar -C /srv/pillar -xf -'
  echo ">> refreshing pillar on minions"
  ssh -F "$cfg" "$master" "sudo salt '*' saltutil.refresh_pillar"
}

apply_state() {  # run state.apply on the master; arg: state name (default: demo)
  local cfg master state="${1:-demo}"
  cfg="$(ssh_config)"; master="$(host_for "$cfg" salt-master)"
  exec ssh -F "$cfg" "$master" "sudo salt '*' state.apply $state"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)       boxman --conf "$CONF" up "$@" ;;
  setup)    ./setup-salt.sh "$@" ;;
  sync)     sync_states ;;
  apply)    apply_state "${1:-}" ;;
  ssh)      ssh_to "${1:-salt-master}" "${@:2}" ;;
  ping)     ssh_to salt-master "sudo salt '*' test.ping" ;;
  status|ps) boxman --conf "$CONF" ps "$@" ;;
  destroy)  boxman --conf "$CONF" destroy "$@" ;;
  *) echo "usage: ./run.sh {up|setup [--accept]|sync|apply [state]|ssh <vm>|ping|status|destroy}" >&2; exit 2 ;;
esac
