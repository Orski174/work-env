#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec pytest -m integration test_wireguard_demo.py -v "$@"
