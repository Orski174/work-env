#!/usr/bin/env bash
# Export tracked tutorial sources only; never recursively copy the worktree.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
prefix=tasks/2026-09-01-packer-video-tutorial/viewer-files
destination=${1:?Pass an empty staging directory}
mkdir -p "$destination"
test -z "$(find "$destination" -mindepth 1 -print -quit)"
git -C "$root" ls-files -z -- "$prefix" |
  tar -C "$root" --null -T - -cf - |
  tar -C "$destination" --strip-components=3 -xf -
test -f "$destination/template.pkr.hcl"
test -z "$(find "$destination" \( -name __pycache__ -o -name '*.pyc' \) -print -quit)"
