# Packer tutorial v3 capture pipeline

This rig records a real Packer → libvirt → boxman session on `capture01` and
uses the `screen-demo-recording` skill for human-paced input, cursor parking,
ground-truth action logging, and evidence-based trimming.

## VM preparation

Copy this directory to `/admin/recording-assets` on the capture VM. Copy the
five helpers from `~/tools/screen-demo-recording/scripts/` to
`/admin/screen-demo-recording/scripts/`:

- `fastgrab_record.py`
- `human_type.py`
- `human_move.py`
- `human_drag.py`
- `trim_recording.py`

The VM also needs the fillable templates at `/admin/tutorial-templates`, the
fastgrab checkout at `/admin/fastgrab-gdp`, and its Python environment at
`/admin/fastgrab-venv`.

## Capture and per-step review

Run `launch-capture.sh`. It starts a 1280×800 Xvfb display, frames an xterm with
a pointer parking strip on the right, and records open-ended at 12 fps. Before
recording and after every command it writes a PNG under
`/admin/packer-v3-review` and blocks on `/tmp/packer_v3_review_ack`. Inspect the
PNG before writing the exact pending label to that ack file.

The raw take is `/admin/packer-tutorial-v3-raw.mp4`. The action log is
`/admin/packer-v3-action.log`; `packer-v3-scenes.jsonl` maps command names and
review frames to raw timestamps.

## Trim, captions, and verification

1. Run `trim-v3.sh`. It keeps every logged action, compresses inactive gaps,
   retains a 20-second closing proof, and creates the uncaptioned retimed master
   at `/admin/packer-tutorial-v3-retimed.mp4`.
2. Run `burn-captions.py`. It scales the capture to 1440×900 at the top of a
   1920×1080 dark canvas and renders captions only in the lower 180-pixel band.
3. Run `extract-command-checks.py` and inspect all generated contact sheets.
   The script samples the midpoint of every `type_start`/`type_end` interval in
   the final render.
4. Decode the complete final with ffmpeg and compare checksums before and after
   transfer.

The final renderer writes `/admin/packer-tutorial-v3-final.mp4`. Keep the
uncaptioned retimed master for future caption-only revisions.
