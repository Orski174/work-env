#!/usr/bin/env bash
# Generate disposable credentials and fill NoCloud + boxman templates.
set -euo pipefail
cd "$(dirname "$0")"
source ./demo.env
[[ "$DEMO_NAME" =~ ^[a-z0-9_]+$ ]]
[[ "$DEMO_HOSTNAME" =~ ^[a-z][a-z0-9-]{0,62}$ ]]
[[ "$DEMO_SUBNET" =~ ^192\.168\.[0-9]{1,3}$ ]]
[[ "$PKR_VAR_output_dir" =~ ^[a-zA-Z0-9_-]+$ ]]
[[ "$PKR_VAR_vm_name" =~ ^[a-zA-Z0-9_.-]+$ ]]
test ! -e id_ed25519_packer
test ! -e .demo-password
umask 077
ssh-keygen -q -t ed25519 -N '' -C packer-demo -f id_ed25519_packer
openssl rand -hex 18 > .demo-password
python3 prepare.py
packer init template.pkr.hcl
packer fmt template.pkr.hcl
packer validate template.pkr.hcl
