#!/usr/bin/env bash
set -euo pipefail

exec xvfb-run -a --server-args='-screen 0 1280x800x24 -nolisten tcp' \
  /admin/recording-assets/run-capture.sh
