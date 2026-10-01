#!/usr/bin/env bash
set -euo pipefail
export DISPLAY=:94
export ACTION_LOG=/var/lib/scds-recording/v5/packer-v5-action.log
export PYTHONPATH=/admin/fastgrab-gdp
test ! -e /var/lib/scds-recording/v5/packer-tutorial-v5-raw.mp4
test ! -e "$ACTION_LOG"
test ! -e /admin/packer-demo
# virt-clone checks the disk's full 10 GiB capacity, even for sparse qcow2.
# Leave room for the download, built image and template before cloning.
available=$(df -B1 --output=avail /admin | tail -1)
test "$available" -ge 13958643712
mkdir /var/lib/scds-recording/v5/packer-v5-review
exec /admin/fastgrab-venv/bin/python /admin/screen-demo-recording/scripts/fastgrab_record.py /var/lib/scds-recording/v5/packer-tutorial-v5-raw.mp4 --fps 12
