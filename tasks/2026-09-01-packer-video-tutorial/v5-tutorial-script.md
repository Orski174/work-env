# v5 Packer tutorial: review fixes and evidence

Recorded on 2026-10-01 after reading the complete independent v4 review at
`/tmp/scds237-review-report.md`, plus the screen-demo-recording skill and its
reference. Fresh real commands, real clipboard, real Packer build and real
Boxman clone; no simulated output or footage from rejected takes.

Final: **3:13.000**, **1920×1080**, 12 fps, H.264/yuv420p, no audio,
2,316 frames, 3,916,486 bytes. The 1920×900 desktop is stacked above a separate
180-pixel dark caption band. Caption filters cannot touch desktop pixels.

- Handoff: `~/Videos/scds/packer-tutorial-recording-v5.mp4`
- Matching local copy: `outputs/2026-09-01-packer-video-tutorial/packer-tutorial-recording-v5.mp4`
- SHA-256: `66044aa8b1375922e6010ff2fbfccf44df7dd042d475f5f91ffcde68a1fd006b`
- Master used: `capture01:/var/lib/scds-recording/v5/packer-tutorial-v5-raw.mp4`
  (956.500 seconds), not the old v3/v4 master.
- Uncaptioned edit: `capture01:/var/lib/scds-recording/v5/packer-tutorial-v5-trimmed.mp4`
- Pipeline: [capture-v5/](capture-v5/README.md).
- Viewer material: [viewer-files/](viewer-files/README.md), starting with
  [packer-values.txt](viewer-files/packer-values.txt) and
  [template.pkr.hcl](viewer-files/template.pkr.hcl); supplied prepare/build/boot/verify
  scripts and cloud-init/Boxman templates are copied into the working directory.

## Seven fixes

Times below refer to v5, not the rejected v4 cut.

| Review item | Fix and timestamp evidence |
| --- | --- |
| 1. Rig clutter | Old Packer recording/evidence/log paths moved from /admin to /var/lib/scds-recording/archive; new rig artifacts live outside /admin. GTK opens in packer-tutorial and receives only source basenames. All five dialogs checked: 00:50.20–00:53.55, 01:37.07–01:39.79, 01:47.87–01:50.29, 02:13.26–02:15.52, 02:43.36–02:46.35. Only tutorial files appear. |
| 2. Caption pace | Every caption passes the renderer's ≤15 chars/s assertion; maximum 8.45. “Use host CPU; clean cloud-init last.” at 00:57.08–01:01.75 is 7.71 chars/s. “Copy all: Ctrl+A, Ctrl+C.” at 01:07.50–01:10.67 is 7.89 chars/s. |
| 3. fmt-clean HCL | The supplied template is preformatted. prepare.sh still runs fmt and validate. At 01:32.54 validation succeeds without a rewritten filename. The post-run source and working-copy hashes match, and packer fmt -check -diff is silent. |
| 4. Generated secrets | .gitignore is shown at 01:41.41: boxman.rendered.yml, *.rendered.yml, .boxman-up.log, .boxman-templates/, seeds and workspace keys are ignored. The audit found seven password/private-key-bearing files, all ignored. Secret YAML/log files are mode 0600; Boxman's private output never reaches the terminal. |
| 5. Hostname | DEMO_HOSTNAME is configured in the sheet. boot.sh uses SSH/hostnamectl after cloning; its source is visible at 02:17.13. “Clone ready: demo-node” appears at 02:36.76. The actual guest's hostname output is demo-node in the single proof at 03:01.14. |
| 6. Python caches | The bundle is exported from tracked source paths, not a recursive worktree copy. Bytecode was removed; __pycache__/ and *.py[cod] are ignored (01:41.41). Every dialog, including 00:52.00, is cache-free. Post-run audit confirms no bytecode in either bundle or viewer workdir. |
| 7. Early boot skip | ./boot.sh is submitted at 02:29.17. The ordinary boot caption remains through frame 1850 (02:34.17). TIME SKIP starts at frame 1851, exactly 02:34.25, the first frame after the 77.25-second omitted wait. Adjacent boundary frames were extracted and inspected. |

## Caption map

Frame-aligned boundaries from the edit manifest. Rates include spaces and punctuation.

| Start | End | Chars/s | Caption |
| --- | --- | ---: | --- |
| 00:00.00 | 00:04.50 | 8.44 | Build a Rocky Linux image with Packer. |
| 00:04.50 | 00:12.17 | 7.04 | Open a terminal. Packer, KVM and boxman are installed. |
| 00:12.17 | 00:19.92 | 5.42 | Open the values sheet beside the terminal. |
| 00:19.92 | 00:24.92 | 7.80 | Keep values visible; copy long content. |
| 00:24.92 | 00:36.42 | 2.78 | Create an empty build directory. |
| 00:36.42 | 00:47.58 | 3.58 | Copy the supplied templates and scripts. |
| 00:47.58 | 00:57.08 | 5.68 | The HCL stays unchanged; demo.env supplies its values. |
| 00:57.08 | 01:01.75 | 7.71 | Use host CPU; clean cloud-init last. |
| 01:01.75 | 01:07.50 | 4.70 | Return to the values sheet. |
| 01:07.50 | 01:10.67 | 7.89 | Copy all: Ctrl+A, Ctrl+C. |
| 01:10.67 | 01:20.58 | 3.43 | Paste: Ctrl+Shift+V. Save: Ctrl+D. |
| 01:20.58 | 01:34.42 | 4.84 | Generate credentials, then fmt and validate. Formatting is a no-op. |
| 01:34.42 | 01:45.25 | 5.35 | Ignore rendered passwords, private logs, seeds and caches. |
| 01:45.25 | 01:53.75 | 4.94 | build.sh loads the values and runs Packer. |
| 01:53.75 | 02:04.25 | 2.48 | Run the real Packer build. |
| 02:04.25 | 02:10.67 | 4.05 | TIME SKIP: build wait cut. |
| 02:10.67 | 02:19.00 | 6.84 | boot.sh starts boxman, then sets the configured hostname. |
| 02:19.00 | 02:34.25 | 3.74 | Boot the built image. Password-bearing logs stay private. |
| 02:34.25 | 02:40.67 | 3.90 | TIME SKIP: boot wait cut. |
| 02:40.67 | 02:50.25 | 3.76 | One SSH proof from the actual clone. |
| 02:50.25 | 03:05.42 | 4.29 | demo-node: Rocky 9.8, baked packages, guest agent and cloud-init. |
| 03:05.42 | 03:13.00 | 7.78 | Done: reusable image and working clone. Templates included. |

## Verification

The screen-demo-recording skill determined the review-gated capture and
action-log trim. All **89 actions** and **20 explicit reading holds** survive
at normal speed; **no action exclusions**. The 24 retained segments use
outward-rounded integer frame ranges. Raw duration extends beyond the last
reviewed action, and the final decoded frame retains the completed guest proof.

Real build time shown: **3m38.378s**; Boxman boot: **1m24.421s**, followed by the
hostname SSH command. Build TIME SKIP starts at **02:04.25**, omitting
211.083 seconds; boot TIME SKIP starts at **02:34.25**, omitting 77.250 seconds.
Other removed gaps are idle pauses between reviewed actions. No typing is sped up.

Checks completed:

- Error-fatal ffmpeg full decode: all 2,316 frames; metadata and frame count agree.
- Inspected all 98 whole-cut samples (every two seconds plus the final frame).
- Inspected all 20 scene outcomes.
- Inspected start/middle/full samples for all 15 typed strings:
  10 short shell commands and five editor basenames (45 samples).
- Inspected all 57 quarter-second dialog samples, including initial listings,
  plus full-resolution problem frames and both adjacent skip-boundary pairs.
- Captions remain in their own band throughout; no command or output is covered.
- The guest reports demo-node, Rocky Linux 9.8, vim/curl/guest-agent/OpenSSH,
  active qemu-guest-agent, and completed NoCloud initialization.
- Post-run audit: unchanged HCL SHA-256
  `c42dd164044d561bb640d2fd4e8628a09b29d251207162d8ba7e0887e40b1663`;
  copied values equal demo.env; all 11 distributed files are source files.
- Local Python AST checks, shell syntax checks and git diff --check pass.

The small generated files containing the actual password/private keys were:
`.demo-password`, `boxman.rendered.yml`, `.boxman-up.log`,
`id_ed25519_packer`, `workspace/id_ed25519_boxman`,
`.boxman-templates/packer_v5-template/nocloud/user-data`, and its `seed.iso`.
The audit reports paths only, never secret contents. Image/cache/workspace
directories are ignored as well.

## Evidence and cleanup

Local evidence directory:
`outputs/2026-09-01-packer-video-tutorial/evidence-v5/`.
It contains manifest.json, decode-report.json, viewer-audit.json,
command-review.json, dialog-review.json, action/scene logs and reviewed PNGs.

Three full-resolution stills showing the clear caption band:

1. `evidence-v5/whole-052.png` — clean tutorial-only dialog, 00:52.00.
2. `evidence-v5/scene-12b-private-files.png` — ignore rules, 01:41.41.
3. `evidence-v5/scene-18-proof.png` — actual guest proof, 03:01.14.

The v5 clone, template, network and both task storage pools were removed.
Generated workdirs/disks/credentials and private destruction logs were deleted
after guest shutdown; these are disposable/rebuildable, not recoverable files.
Recording desktop processes were stopped. The outer capture VM, default network,
all older videos, new raw master and rejected-take recordings/evidence remain.
Rejected takes contributed no final frames.

## Git handoff

Work is committed on main, without rebase or push. Unrelated TASKS.md,
2026-08-24-mpi-tech-scout and 2026-08-08-packer-rancher-scouting work is untouched.

SSH fetch failed because the agent socket is stale. A real HTTPS git fetch
succeeded and refreshed origin/main. The two remote-only commits are:

- `28a2e29e2591ba44cd08efc7771ea34c1fc23aac` — Redo Packer tutorial capture pipeline.
- `d168e4bd63ec51ad18122e0cf86e4791d2b27dd8` — tasks: oil-wells dataset updates + new scouting/demo task dirs.

The pre-v5 branch was ahead 2 / behind 2. Command-center will handle integration.
No GitLab upload, issue comment, rebase or push was performed.
