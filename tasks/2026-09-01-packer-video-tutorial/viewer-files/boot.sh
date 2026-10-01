#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ./demo.env
umask 077
# Keep secret-bearing files private, without blocking QEMU's disk directories.
touch .boxman-up.log boxman.rendered.yml
chmod 600 .boxman-up.log boxman.rendered.yml
umask 022
export PACKER_IMAGE_PATH="$PWD/$PKR_VAR_output_dir/$PKR_VAR_vm_name"
export BOXMAN_ADMIN_PASS
BOXMAN_ADMIN_PASS="$(< .demo-password)"
# Boxman's log can contain rendered passwords; never print it on screen.
echo "Starting boxman; private log: .boxman-up.log"
time boxman --conf boxman.yml up > .boxman-up.log 2>&1
# Clones retain the template hostname; apply this node's configured value.
[[ "$DEMO_HOSTNAME" =~ ^[a-z][a-z0-9-]{0,62}$ ]]
ssh -F workspace/ssh_config "demo_$DEMO_HOSTNAME" \
  sudo hostnamectl set-hostname "$DEMO_HOSTNAME"
echo "Clone ready: $DEMO_HOSTNAME"
