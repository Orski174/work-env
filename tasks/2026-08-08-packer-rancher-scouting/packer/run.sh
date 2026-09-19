#!/usr/bin/env bash
# Driver for the Packer scouting sub-trial. Meant to run on sc1.
#
#   ./run.sh install-packer     add HashiCorp repo + dnf install packer (RHEL/dnf host)
#   ./run.sh build               render the SSH seed, packer build the Rocky 9 qcow2
#   ./run.sh up                   boxman up (clone+boot 1 VM from the built image)
#   ./run.sh status               boxman ps for the test cluster
#   ./run.sh ssh                  ssh into the test VM
#   ./run.sh destroy              boxman destroy the test cluster
#   ./run.sh clean                remove build output + generated keys/seed
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

OUTDIR="output-rocky9"
IMAGE="$HERE/$OUTDIR/rocky9-packer-base.qcow2"
KEY="id_ed25519_packer"
CONF="boxman-test/conf.yml"

boxman() {
  if [ -n "${BOXMAN:-}" ]; then "$BOXMAN" "$@";
  elif command -v boxman >/dev/null 2>&1; then command boxman "$@";
  elif [ -x "$HOME/.conda/envs/boxman/bin/boxman" ]; then "$HOME/.conda/envs/boxman/bin/boxman" "$@";
  else python -m boxman "$@"; fi
}

do_install_packer() {
  if command -v packer >/dev/null 2>&1 && packer version 2>/dev/null | grep -qi hashicorp; then
    echo "packer already installed: $(packer version)"
    return
  fi
  echo ">> installing HashiCorp Packer (dnf)"
  sudo dnf install -y dnf-plugins-core
  sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
  sudo dnf install -y packer
  packer version
}

do_build() {
  [ -f "$KEY" ] || { echo ">> generating ephemeral build keypair"; ssh-keygen -t ed25519 -N '' -f "$KEY" -C "packer-scouting-trial"; }
  local pubkey
  pubkey="$(cat "${KEY}.pub")"
  sed "s#__PACKER_SSH_PUBKEY__#${pubkey}#" http/user-data.tmpl > http/user-data

  packer init template.pkr.hcl
  packer validate template.pkr.hcl
  time packer build -var "ssh_private_key_file=$HERE/$KEY" -var "output_directory=$OUTDIR" template.pkr.hcl
  echo ">> built: $IMAGE"
  ls -lh "$IMAGE"
}

do_up() {
  [ -f "$IMAGE" ] || { echo "no built image at $IMAGE — run './run.sh build' first" >&2; exit 1; }
  export PACKER_IMAGE_PATH="$IMAGE"
  time boxman --conf "$CONF" up "$@"
}

do_ssh() {
  local cfg
  cfg="$(find "$HOME/workspaces/boxmandev/packer_scouting_test" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config found — run './run.sh up' first" >&2; exit 1; }
  local host
  host="$(awk '$1=="Host" && $2 !~ /\*/ {print $2; exit}' "$cfg")"
  exec ssh -F "$cfg" "$host"
}

do_clean() {
  rm -rf "$OUTDIR" "$KEY" "${KEY}.pub" http/user-data packer_cache*
}

cmd="${1:-}"; shift || true
case "$cmd" in
  install-packer) do_install_packer ;;
  build)          do_build ;;
  up)             do_up "$@" ;;
  status)         boxman --conf "$CONF" ps || true ;;
  ssh)            do_ssh ;;
  destroy)        boxman --conf "$CONF" destroy "$@" ;;
  clean)          do_clean ;;
  *) echo "usage: ./run.sh {install-packer|build|up|status|ssh|destroy|clean}" >&2; exit 2 ;;
esac
