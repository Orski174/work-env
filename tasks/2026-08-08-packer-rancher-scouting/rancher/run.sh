#!/usr/bin/env bash
# Driver for the Rancher scouting sub-trial. Meant to run on sc1.
#
#   ./run.sh up                 boxman up (provision the 1 throwaway VM)
#   ./run.sh setup                ./setup.sh (k3s + helm + cert-manager + Rancher)
#   ./run.sh status                node/pod status for k3s + cert-manager + Rancher
#   ./run.sh ssh                   ssh into rancher01
#   ./run.sh ui                    print the SSH tunnel command for the Rancher UI
#   ./run.sh destroy               boxman destroy
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

CONF="boxman/conf.yml"
WORKSPACE="${RANCHER_WORKSPACE:-$HOME/workspaces/boxmandev/rancher_scouting_trial}"

boxman() {
  if [ -n "${BOXMAN:-}" ]; then "$BOXMAN" "$@";
  elif command -v boxman >/dev/null 2>&1; then command boxman "$@";
  elif [ -x "$HOME/.conda/envs/boxman/bin/boxman" ]; then "$HOME/.conda/envs/boxman/bin/boxman" "$@";
  else python -m boxman "$@"; fi
}

ssh_config() {
  local cfg
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  printf '%s\n' "$cfg"
}

host_for() {
  local host
  host="$(awk -v p="$2" '$1=="Host" && $2 ~ p {print $2; exit}' "$1")"
  [ -n "$host" ] || { echo "no Host matching '$2' in $1" >&2; exit 1; }
  printf '%s\n' "$host"
}

ip_for() {
  awk -v h="$2" '
    $1=="Host" { inblock = ($2==h) }
    inblock && tolower($1)=="hostname" { print $2; exit }
  ' "$1"
}

ssh_to() {
  local cfg="$1" host="$2"; shift 2
  ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=10 "$host" "$@"
}

do_status() {
  echo "== boxman ps =="
  boxman --conf "$CONF" ps || true
  local cfg host
  cfg="$(ssh_config)"; host="$(host_for "$cfg" "rancher01\$")"
  echo
  echo "== k3s nodes =="
  ssh_to "$cfg" "$host" 'sudo k3s kubectl get nodes -o wide' || echo "(k3s not reachable — has 'setup' run?)"
  echo
  echo "== cert-manager pods =="
  ssh_to "$cfg" "$host" 'sudo k3s kubectl -n cert-manager get pods' || true
  echo
  echo "== rancher pods =="
  ssh_to "$cfg" "$host" 'sudo k3s kubectl -n cattle-system get pods' || true
}

do_ui() {
  local cfg host ip
  cfg="$(ssh_config)"; host="$(host_for "$cfg" "rancher01\$")"; ip="$(ip_for "$cfg" "$host")"
  echo "From the workstation:"
  echo "  ssh -L 8443:${ip}:443 sc1"
  echo "Then browse https://localhost:8443 (self-signed cert — trial only, click through the warning)."
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)       boxman --conf "$CONF" up "$@" ;;
  setup)    ./setup.sh "$@" ;;
  status)   do_status ;;
  ssh)      cfg="$(ssh_config)"; exec ssh -F "$cfg" "$(host_for "$cfg" "rancher01\$")" ;;
  ui)       do_ui ;;
  destroy)  boxman --conf "$CONF" destroy "$@" ;;
  *) echo "usage: ./run.sh {up|setup|status|ssh|ui|destroy}" >&2; exit 2 ;;
esac
