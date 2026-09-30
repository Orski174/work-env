#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${REHEARSAL_WORKDIR:-/admin/packer-boxman-rehearsal-v3}"
TEMPLATES=/admin/tutorial-templates
WORKSPACE_PATH="~/${WORKDIR#/admin/}/workspace"

if [[ -e "$WORKDIR" ]]; then
  echo "Refusing to reuse rehearsal directory: $WORKDIR" >&2
  exit 2
fi

mkdir -p "$WORKDIR"
cd "$WORKDIR"
cp -R "$TEMPLATES/packer/." .

ssh-keygen -q -t ed25519 -N '' -C packer-demo -f id_ed25519_packer

ROCKY_IMAGE='https://download.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2'
ROCKY_SHA='92c206cc6f790c61583247eefe87890f8828420662c17cacf247cec78ab4eec8'

sed -i \
  -e "s|__ROCKY_IMAGE_URL__|$ROCKY_IMAGE|" \
  -e "s|__ROCKY_IMAGE_SHA256__|$ROCKY_SHA|" \
  -e 's|__CPU_MODEL__|host|' \
  template.pkr.hcl
sed -i \
  -e 's|__BUILD_HOSTNAME__|packer-build|g' \
  -e 's|__INSTANCE_ID__|packer-build-001|g' \
  http/meta-data http/user-data
sed -i "s|__SSH_PUBLIC_KEY__|$(cat id_ed25519_packer.pub)|" http/user-data

if rg -n '__[A-Z_]+__' template.pkr.hcl http; then
  echo 'Unfilled Packer placeholder found' >&2
  exit 3
fi

export PACKER_CACHE_DIR="${PACKER_CACHE_DIR:-$WORKDIR/.packer-cache}"
packer init template.pkr.hcl
packer fmt template.pkr.hcl
packer validate template.pkr.hcl
packer build template.pkr.hcl

export PACKER_IMAGE_PATH="$WORKDIR/output-rocky9/rocky9-packer-base.qcow2"
qemu-img info "$PACKER_IMAGE_PATH"

cp "$TEMPLATES/boxman.yml" boxman.yml
sed -i \
  -e 's|__PROJECT__|packer_boxman_demo_v3_rehearsal|g' \
  -e 's|__IMAGE_ENV__|PACKER_IMAGE_PATH|g' \
  -e 's|__TEMPLATE_NAME__|rocky9-packer-template-v3-rehearsal|g' \
  -e "s|__WORKSPACE_PATH__|$WORKSPACE_PATH|g" \
  -e 's|__NETWORK_PREFIX__|192.168.78|g' \
  -e 's|__TEMPLATE_HOSTNAME__|packer-template|g' \
  -e 's|__VM_HOSTNAME__|demo-node|g' \
  boxman.yml

if rg -n '__[A-Z_]+__' boxman.yml; then
  echo 'Unfilled boxman placeholder found' >&2
  exit 4
fi

export BOXMAN_ADMIN_PASS=boxman
export PATH=/admin/boxman-venv/bin:/usr/local/bin:/usr/bin:/bin
boxman --conf boxman.yml up
boxman --conf boxman.yml ps

SSH_CONFIG="$WORKDIR/workspace/ssh_config"
SSH_HOST="$(awk '$1 == "Host" && $2 !~ /\*/ { print $2; exit }' "$SSH_CONFIG")"
ssh -F "$SSH_CONFIG" "$SSH_HOST" \
  'hostname; cat /etc/rocky-release; rpm -q vim-enhanced curl qemu-guest-agent openssh-server; systemctl is-active qemu-guest-agent; sudo grep -E "Cloud-init .* finished at" /var/log/cloud-init.log | tail -1'
