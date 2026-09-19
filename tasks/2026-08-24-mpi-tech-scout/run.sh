#!/usr/bin/env bash
# Thin driver around boxman for the MPI lab. Meant to run on sc1.
#
#   ./run.sh up          provision: build template + clone the 2 VMs
#   ./run.sh setup       install OpenMPI, wire SSH trust, compile hello.c
#   ./run.sh mpitest     mpirun the hello-world program across both nodes
#   ./run.sh ssh <vm>    ssh into mpi-node1 | mpi-node2
#   ./run.sh status      boxman ps for this project
#   ./run.sh destroy     tear the lab down
#
# boxman is located via $BOXMAN, then PATH, then a `python -m boxman` fallback.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

CONF="boxman/conf.yml"
WORKSPACE="${MPI_LAB_WORKSPACE:-$HOME/workspaces/mpi-lab}"

boxman() {
  if [ -n "${BOXMAN:-}" ]; then "$BOXMAN" "$@";
  elif command -v boxman >/dev/null 2>&1; then command boxman "$@";
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

ssh_to() {
  local cfg host
  cfg="$(ssh_config)"
  host="$(host_for "$cfg" "$1")"
  shift
  exec ssh -F "$cfg" "$host" "$@"
}

mpitest() {
  local cfg n1
  cfg="$(ssh_config)"; n1="$(host_for "$cfg" mpi-node1)"
  exec ssh -F "$cfg" "$n1" 'mpirun --hostfile ~/mpi-hello/hosts -np 4 ~/mpi-hello/hello'
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)        boxman --conf "$CONF" up "$@" ;;
  setup)     ./setup-mpi.sh "$@" ;;
  mpitest)   mpitest ;;
  ssh)       ssh_to "${1:-mpi-node1}" "${@:2}" ;;
  status|ps) boxman --conf "$CONF" ps "$@" ;;
  destroy)   boxman --conf "$CONF" destroy "$@" ;;
  *) echo "usage: ./run.sh {up|setup|mpitest|ssh <vm>|status|destroy}" >&2; exit 2 ;;
esac
