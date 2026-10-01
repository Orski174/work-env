#!/usr/bin/env bash
# Exact v5 recording resources only; leaves recordings and work files intact.
set -euo pipefail
cd /admin/packer-demo
source ./demo.env
test "$DEMO_NAME" = packer_v5
export PACKER_IMAGE_PATH="$PWD/$PKR_VAR_output_dir/$PKR_VAR_vm_name"
export BOXMAN_ADMIN_PASS
BOXMAN_ADMIN_PASS="$(< .demo-password)"
umask 077
/admin/boxman-venv/bin/boxman --conf boxman.yml destroy --auto-accept \
  > /var/lib/scds-recording/v5/destroy-private.log 2>&1
test "$(sudo virsh domstate packer_v5-template)" = 'shut off'
sudo virsh undefine packer_v5-template
for pool in packer_v5-template demo; do
  expected=/admin/packer-demo/workspace/demo
  if test "$pool" = packer_v5-template; then
    expected=/admin/packer-demo/.boxman-templates/packer_v5-template
  fi
  actual=$(sudo virsh pool-dumpxml "$pool" | sed -n 's:.*<path>\(.*\)</path>.*:\1:p')
  test "$actual" = "$expected"
  sudo virsh pool-destroy "$pool"
  sudo virsh pool-undefine "$pool"
done
sudo virsh list --all
sudo virsh pool-list --all
sudo virsh net-list --all
