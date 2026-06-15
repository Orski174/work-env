#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# This task is shell/Terraform, not Python. Entry point just runs the demo.
exec ./demo/run.sh "$@"
