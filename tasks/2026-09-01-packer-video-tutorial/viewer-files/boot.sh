#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ./demo.env
export PACKER_IMAGE_PATH="$PWD/$PKR_VAR_output_dir/$PKR_VAR_vm_name"
export BOXMAN_ADMIN_PASS
BOXMAN_ADMIN_PASS="$(< .demo-password)"
time boxman --conf boxman.yml up
