# v5 reviewed desktop recording

Uses the complete `~/tools/screen-demo-recording/SKILL.md` and `reference.md`,
with the actual skill helpers installed in `/admin/screen-demo-recording` on
the dedicated `bprj__throwaway-playwright-capture` VM. No synthetic output,
command replay, credentials in typed commands, or action exclusions.

## Rig and staging

1920×900 XFCE desktop, Xvfb :94, 12 fps; terminal and Mousepad side by side.
The final adds a separate 1920×180 caption band below the untouched desktop.
Only that separate band receives drawtext filters.

Stage this pipeline at `/var/lib/scds-recording/v5/pipeline`. Run setup-rig.sh
as the existing admin account. It archives only inspected `packer-*` and
`recording-v4` task artifacts under `/var/lib/scds-recording/archive`, including
previous media and evidence. It does not change users, sudoers, dependencies,
ACLs or unrelated directories. All new capture/evidence/log files are outside
the home directory under `/var/lib/scds-recording/v5`.

Run `stage-viewer.sh EMPTY_DIRECTORY` locally and transfer its contents to
`/admin/packer-tutorial`. It copies only Git-tracked viewer source paths, not
ignored Python bytecode or generated credentials. Do not use recursive scp on
the original worktree. The staged `.gitignore` travels with the bundle.

Configure XFCE using setup-desktop.py. Start Xvfb and start-desktop.sh under a
fresh dbus-run-session, redirecting logs into the rig directory with closed
SSH standard streams. GTK starts in the tutorial directory, not Recent; the
editor launcher has an explicit working directory. Open File uses Ctrl+L and
only source basenames, never autocompleting /admin or visiting the rig folders.
All displayed templates are the identical source copies in packer-tutorial;
commands execute their copies in packer-demo.

Before capture inspect a clean desktop screenshot, check no leftover demo
domains/pools or packer-demo directory, and run `packer fmt -check -diff` on
the staged HCL (must print nothing). Start start-recording.sh open-ended and
retain its PID. It refuses existing raw/log/workdir paths and requires at least
13 GiB free: virt-clone checks the virtual disk's 10 GiB capacity even when
the source image is sparse.

## Review-gated recording

Use `python3 actions.py LABEL` for 01-desktop through 19-finish, inserting
12b-private-files after 12-prepare (20 scenes). After EACH action, transfer the
printed screenshot, actually look at it, then acknowledge with
`python3 actions.py ack LABEL`. Never batch past the gate. The values are
copied with real clipboard shortcuts; source, clipboard and demo.env bytes
must match. The real build and boot run to completion; only waiting is cut.

Stop the recorder with SIGINT after the final reviewed hold. Confirm duration
extends past the final action and inspect the last frame. A partial initial
take with a GTK Recent-search navigation error was preserved separately under
`partial-take/`. A second rejected take exposed an overly restrictive directory
umask at boot; its recording is under `failed-boot-take/`. The corrected boot,
actual demo-node hostname, and secret-file audit passed a complete off-camera
trial before restarting from the desktop. A third take, `failed-storage-take/`,
hit virt-clone's capacity check because trial disks still occupied space.
Only the exact trial guests, pools and generated workdirs were removed before
the final fresh take; all rejected recordings and evidence were preserved.
None of the rejected takes contributes frames or actions to the final take.

## Trim, captions and evidence

Run with `/admin/fastgrab-venv/bin/python`:

```text
render.py --dry-run
render.py
review.py
audit-viewer.py
```

The renderer imports the skill's action parser, freeze detector and trim
builder. All typing, mouse/clipboard actions and explicit read holds survive
at 1×; excludes is empty. It uses outward-rounded integer frame intervals,
checks each clip's frame count, and enforces 240 seconds maximum.

Captions are deliberately short. Every caption is frame-aligned and must
pass `len(text)/(end-start) <= 15`; the exact rate is in manifest.json.
Build and boot receive ordinary captions while commands are typed. TIME SKIP
starts exactly on the first output frame after the largest omitted wait in
that operation, never at the start of the scene. The skip record includes
submission time, cut timestamp and removed duration.

review.py fully decodes with ffmpeg -xerror, checks resolution and frame count,
and extracts every scene, beginning/middle/end of each typed string, whole-cut
samples every two seconds and the actual last frame. It also samples the
entire Open File intervals every quarter-second, including initial listings
before typing. Inspect EVERY contact
sheet tile and full-resolution problem areas; generating images is not review.
audit-viewer.py checks unchanged HCL, exact copied values, absence of bytecode,
private generated-file modes, and real Git ignore coverage for files that
contain the generated password/private keys (reports paths, never values).

## Viewer fixes

The HCL is committed fmt-clean; prepare.sh keeps fmt and validate. boot.sh
redirects Boxman's potentially password-bearing output into a private ignored
log. Rendered YAML, template workdir/NoCloud seeds, workspace/keys and bytecode
are ignored. The template workdir stays inside the disposable project.
After boxman starts the clone, boot.sh uses SSH/hostnamectl to set the actual
hostname from DEMO_HOSTNAME. verify.sh queries that real guest once.

## Cleanup and handoff

After evidence is complete, destroy only this demo's clone/network and resolve
its exact template/domain/pool paths before removing leftovers. Remove the
generated credentials and task workdir only after all tutorial guests stop.
Stop this task's desktop/recorder processes; keep the existing outer VM, old
media, new raw master, pipeline logs and review evidence.

Copy final MP4 into the gitignored work-env outputs directory and
`~/Videos/scds/packer-tutorial-recording-v5.mp4`, comparing SHA-256. Commit only
this task on main. Fetch remote history, but DO NOT rebase or push. Command-center
handles integration. No GitLab upload or comment.
