#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source ./demo.env
export PACKER_CACHE_DIR="$PWD/.packer-cache"
time packer build template.pkr.hcl
