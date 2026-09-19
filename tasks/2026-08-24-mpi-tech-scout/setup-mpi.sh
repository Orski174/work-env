#!/usr/bin/env bash
# Install OpenMPI on both lab VMs, wire up passwordless SSH from mpi-node1 ->
# mpi-node2 (mpirun's default rsh launcher needs it), build the hello-world
# program, and copy the binary to matching paths on both nodes (no shared
# filesystem in this lab, so mpirun can't rely on one).
#
# Run from the task root on sc1 (where boxman provisioned):
#   ./setup-mpi.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WORKSPACE="${MPI_LAB_WORKSPACE:-$HOME/workspaces/mpi-lab}"
SSH_CONFIG="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1 || true)"
if [ -z "$SSH_CONFIG" ]; then
  echo "ERROR: ssh_config not found under $WORKSPACE — has './run.sh up' run?" >&2
  exit 1
fi
echo ">> using ssh_config: $SSH_CONFIG"

N1_HOST="$(awk '/^Host .*mpi-node1/{print $2; exit}' "$SSH_CONFIG")"
N2_HOST="$(awk '/^Host .*mpi-node2/{print $2; exit}' "$SSH_CONFIG")"
if [ -z "$N1_HOST" ] || [ -z "$N2_HOST" ]; then
  echo "ERROR: could not find mpi-node1/mpi-node2 Host entries in $SSH_CONFIG" >&2
  grep '^Host ' "$SSH_CONFIG" >&2 || true
  exit 1
fi
echo ">> node1 host alias: $N1_HOST"
echo ">> node2 host alias: $N2_HOST"

n1() { ssh -F "$SSH_CONFIG" -o LogLevel=ERROR "$N1_HOST" "$@"; }
n2() { ssh -F "$SSH_CONFIG" -o LogLevel=ERROR "$N2_HOST" "$@"; }

echo ">> [both] installing openmpi-bin + libopenmpi-dev ..."
n1 'sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y openmpi-bin libopenmpi-dev'
n2 'sudo DEBIAN_FRONTEND=noninteractive apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y openmpi-bin libopenmpi-dev'

echo ">> [node1] generating an ssh keypair for the admin user (if missing) ..."
n1 '[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519'
N1_PUBKEY="$(n1 'cat ~/.ssh/id_ed25519.pub')"

echo ">> [node2] trusting node1's key for the admin user ..."
n2 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$N1_PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sort -u -o ~/.ssh/authorized_keys ~/.ssh/authorized_keys"

echo ">> resolving each node's IP on the lab network (192.168.79.0/24) ..."
N1_IP="$(n1 "ip -4 -o addr show | awk '{print \$4}' | cut -d/ -f1 | grep '^192.168.79.' | head -1")"
N2_IP="$(n2 "ip -4 -o addr show | awk '{print \$4}' | cut -d/ -f1 | grep '^192.168.79.' | head -1")"
if [ -z "$N1_IP" ] || [ -z "$N2_IP" ]; then
  echo "ERROR: could not determine lab-network IPs (node1=$N1_IP node2=$N2_IP)" >&2
  exit 1
fi
echo ">> node1 IP: $N1_IP   node2 IP: $N2_IP"

echo ">> [node1] trusting node2's host key (needed for mpirun's rsh launcher) ..."
n1 "ssh-keyscan -H $N2_IP >> ~/.ssh/known_hosts 2>/dev/null"
n1 "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new $N2_IP true"

echo ">> [node1] compiling hello.c ..."
n1 'mkdir -p ~/mpi-hello'
scp -F "$SSH_CONFIG" -o LogLevel=ERROR "$HERE/src/hello.c" "$N1_HOST:~/mpi-hello/hello.c"
n1 'mpicc -O2 -o ~/mpi-hello/hello ~/mpi-hello/hello.c'

echo ">> [node1 -> node2] copying the compiled binary to the same path ..."
n1 "scp -o StrictHostKeyChecking=accept-new -r ~/mpi-hello $N2_IP:~/"

echo ">> [node1] writing the hostfile (2 slots per node) ..."
n1 "printf '%s slots=2\n%s slots=2\n' '$N1_IP' '$N2_IP' > ~/mpi-hello/hosts"

echo
echo "Setup complete. Run the hands-on test with:"
echo "  ./run.sh mpitest"
