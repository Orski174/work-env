# v4 desktop / copy-and-paste recording

Uses `~/tools/screen-demo-recording/SKILL.md`, `reference.md`, and its helper
scripts. The new take runs the actual Packer → KVM → boxman workflow; no terminal
output is fabricated or replayed. The accepted v3 files remain unchanged.

## Layout and viewer bundle

- Capture: 1920×900, 12 fps, clean XFCE desktop on Xvfb `:94`.
- Terminal: x=20, y=65, 102×36 cells, DejaVu Sans Mono 13; configured in the
  terminal rc file so its panel launcher opens the same readable geometry.
- Mousepad: roughly 798×803 at x=1070, y=65; font 13, word wrap enabled.
- Pointer parking: x=1890, y=460, clear of both windows.
- Final: untouched 1920×900 desktop above a separate 1920×180 dark caption
  strip. The renderer draws captions on the strip, then stacks it below the
  screen. Caption pixels cannot cover terminal/editor pixels.
- `../viewer-files/` is staged as `/admin/packer-tutorial`. It includes the
  values sheet, HCL, cloud-init and boxman templates, and scripts. Only this
  bundle is needed to follow the tutorial; see its README for prerequisites.

## Recording rig

Dedicated VM: `bprj__throwaway-playwright-capture`, reached via:

```bash
ssh -F ~/workspaces/throwaway-playwright-capture/workspace/ssh_config cluster_1_capture01
```

Install the lightweight XFCE components (`xfce4-panel`, `xfwm4`, `xfdesktop4`,
`xfce4-settings`, `xfce4-terminal`, `mousepad`, `dbus-x11`) plus `xclip`,
`xdotool`, ImageMagick, ffmpeg and Xvfb. Copy the skill's `scripts/` to
`/admin/screen-demo-recording/scripts`. This rig uses the explicit interpreter
`/admin/fastgrab-venv/bin/python` and `PYTHONPATH=/admin/fastgrab-gdp`.

Stage this directory at `/admin/recording-v4` and viewer-files at
`/admin/packer-tutorial` (preserve the scripts' executable bits). Configure a
fresh dedicated desktop with `python3 setup-desktop.py`, start Xvfb `:94` at
1920×900×24, and run `dbus-run-session bash start-desktop.sh`. Its background
processes must have closed stdin/stdout/stderr when launched through SSH.
Do not apply this setup to a user's existing desktop profile.

Confirm no leftover tutorial domains/pools, no `/admin/packer-demo`, and no
restored windows or dialogs. Inspect a screenshot **before** capture. Then run
`bash start-recording.sh` open-ended; record its PID. It refuses to overwrite
the raw master, log or demo directory.

Run `python3 actions.py LABEL` for the ordered labels `01-desktop` through
`19-finish` in `actions.py`. After **each** step, retrieve the printed review
PNG, actually inspect it, then run `python3 actions.py ack LABEL`. The next
step refuses to run without that acknowledgement. Do not batch past this gate.
Opening the editor uses the desktop launcher; its title bar is moved with the
skill's human_drag helper. Verify the actual window geometry before that drag.
Copy/paste uses the real clipboard and asserts that it matches both the sheet
and the saved `demo.env` byte-for-byte. All keyboard shortcuts are logged.

After reviewing/acknowledging the final shot, explicitly `kill -INT` the
recorder PID and wait for its MP4 to finalize. Compare the recorded duration
and frame count with the action log's last timestamp, and inspect the ending.

## Evidence-based edit and review

```bash
/admin/fastgrab-venv/bin/python /admin/recording-v4/render.py --dry-run
/admin/fastgrab-venv/bin/python /admin/recording-v4/render.py
/admin/fastgrab-venv/bin/python /admin/recording-v4/review.py
```

`render.py` imports the skill's action parser, freeze detector and kept-segment
builder. Every typing/mouse/clipboard action and explicit read hold stays at
1×, with **no action exclusions**. Only gaps are shortened. The first activity
and real successful results of build/boot remain, with a visible TIME SKIP
caption and actual elapsed runtime. Review pauses are removed as idle gaps.

The frame ranges round outward; each encoded clip is frame-count checked, and
the exact integer-frame map drives caption timing and evidence extraction.
Assertions reject truncated raw footage, missing reviews, clipped actions,
oversized captions, and a cut exceeding 240 seconds. The scripts refuse to
overwrite an existing render/evidence directory; preserve it under a new name
before deliberately rerendering.

For a caption-only correction, preserve/rename the old final MP4 and evidence
directory, then run `render.py --captions-only` followed by `review.py` again.
The previous manifest must match the recomputed edit frame-for-frame. Runtime
labels are approximate because the action submit marker follows the Enter key.

`review.py` performs an error-fatal full-frame decode and checks resolution,
duration and frame count. It extracts every scene outcome, three points from
every typed string, a contact sheet of the entire cut at 2-second intervals,
and the actual final frame. Read **every** contact-sheet tile, then inspect
full-resolution scene/command frames wherever needed. Extraction alone is not
visual verification.

Artifacts remain on the VM under `/admin/packer-tutorial-v4-{raw,trimmed,final}.mp4`
and `/admin/packer-v4-render/`. Action/scene logs are `/admin/packer-v4-action.log`
and `/admin/packer-v4-scenes.jsonl`. `manifest.json` is the exact edit/caption map;
`decode-report.json` and `command-review.json` are machine-readable evidence.

## Cleanup and handoff

After recording, run boxman destroy with the generated demo environment.
Inspect libvirt: boxman can leave its shut-off reusable template and directory
pools behind. This take's exact leftovers were `packer_v4-template` (domain and
pool) and `demo` (pool pointing at `/admin/packer-demo/workspace/demo`). Remove
only those resolved resources, their `/admin/boxman-templates/packer_v4-template`
directory, `/admin/packer-demo`, and the task's Xvfb/desktop processes. Preserve
all raw/final recordings and evidence. Never delete a pre-existing VM or pool.

Copy the reviewed final to work-env's gitignored output folder and
`~/Videos/scds/packer-tutorial-recording-v4.mp4`; compare SHA-256 after transfer.
Commit only the task's pipeline/templates/docs. Push to the existing remote
only if it is reachable/authenticated. Do not upload the video or post an issue
comment.
