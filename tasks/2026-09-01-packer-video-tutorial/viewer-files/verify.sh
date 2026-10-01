#!/usr/bin/env bash
# One proof: boot the built disk and query the actual guest over SSH.
set -euo pipefail
cd "$(dirname "$0")"
source ./demo.env
ssh -F workspace/ssh_config "demo_$DEMO_HOSTNAME" '
  hostname
  cat /etc/rocky-release
  rpm -q vim-enhanced curl qemu-guest-agent openssh-server
  systemctl is-active qemu-guest-agent
  sudo grep -E "Cloud-init .* finished at" /var/log/cloud-init.log | tail -1
'
