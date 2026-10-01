#!/usr/bin/env bash
set -euo pipefail
export DISPLAY=:94
export ACTION_LOG=/admin/packer-v4-action.log
export PYTHONPATH=/admin/fastgrab-gdp
test ! -e /admin/packer-tutorial-v4-raw.mp4
test ! -e "$ACTION_LOG"
test ! -e /admin/packer-demo
mkdir /admin/packer-v4-review
exec /admin/fastgrab-venv/bin/python /admin/screen-demo-recording/scripts/fastgrab_record.py /admin/packer-tutorial-v4-raw.mp4 --fps 12
