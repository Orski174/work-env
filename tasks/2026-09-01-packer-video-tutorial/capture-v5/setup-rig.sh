#!/usr/bin/env bash
# Dedicated capture VM; no accounts, sudoers, dependency or ACL changes.
set -euo pipefail
rig=/var/lib/scds-recording
test -d "$rig/v5/pipeline"
test "$(id -un)" = admin
sudo mkdir -p "$rig/archive"
sudo chown admin:admin "$rig" "$rig/archive" "$rig/v5"
# Only the resolved Packer-task artifacts are moved. Unrelated tools stay put.
find /admin -mindepth 1 -maxdepth 1 \
  \( -name 'packer-*' -o -name 'recording-v4' \) -printf '%f\n' > "$rig/v5/archived-home-inventory.txt"
while IFS= read -r name; do
  test ! -e "$rig/archive/$name"
  mv -- "/admin/$name" "$rig/archive/$name"
done < "$rig/v5/archived-home-inventory.txt"
python3 "$rig/v5/pipeline/setup-desktop.py"
# Open File is always rooted in the supplied tutorial directory, never /admin.
