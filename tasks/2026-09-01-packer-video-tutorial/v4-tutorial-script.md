# v4 desktop tutorial: caption and action map

Fresh real-session recording on 2026-10-01 using the screen-demo-recording skill.
Final duration: **3:11.92** (2,303 frames at 12 fps), 1920×1080.
The full 1920×900 desktop sits above a separate 180-pixel caption strip.

Viewer bundle: [viewer-files/](viewer-files/README.md). Capture/edit pipeline:
[capture-v4/](capture-v4/README.md). All long values are copied through the real
clipboard into `demo.env`; templates and scripts are copied unchanged. Short
commands and file paths are typed at natural speed. There is one guest proof.

## Final caption map

Times are generated from the integer-frame edit map, not guessed from sleeps.

| Start | End | Scene / caption |
| --- | --- | --- |
| 00:00.00 | 00:04.47 | Packer to boxman: build a reusable Rocky Linux image, then boot one clone. |
| 00:04.47 | 00:11.97 | Start on a clean desktop. Packer, KVM and boxman are already installed. |
| 00:11.97 | 00:19.55 | Open packer-values.txt beside the terminal: pinned image, checksum, names and subnet. |
| 00:19.55 | 00:24.69 | Keep the values sheet visible. Long values will be copied, not retyped. |
| 00:24.69 | 00:36.13 | Create an empty work directory for this build. |
| 00:36.13 | 00:46.99 | Copy the supplied viewer-files bundle (staged here as ~/packer-tutorial). |
| 00:46.99 | 00:59.24 | The HCL stays unchanged: demo.env supplies the image URL, SHA-256, name and output directory. |
| 00:59.24 | 01:03.88 | Use the host CPU; bake in the packages once. Cloud-init cleanup is the final provisioner step. |
| 01:03.88 | 01:09.64 | Return to the values sheet. Keep the pinned image URL and checksum together. |
| 01:09.64 | 01:12.81 | Select all and copy (Ctrl+A, Ctrl+C). The sheet contains only demo values and comments. |
| 01:12.81 | 01:23.04 | Paste into demo.env (Ctrl+Shift+V), then Ctrl+D to save. No long content is typed. |
| 01:23.04 | 01:36.92 | prepare.sh generates disposable credentials and NoCloud data, then initializes and validates Packer. |
| 01:36.92 | 01:47.98 | The supplied build.sh loads demo.env and runs packer build. Its complete source is visible. |
| 01:47.98 | 02:05.12 | TIME SKIP — build wait shortened (real run: about 2:59). The real build produces the qcow2. |
| 02:05.12 | 02:16.06 | boot.sh passes the built image path to boxman and loads the private, generated demo password. |
| 02:16.06 | 02:37.58 | TIME SKIP — boot wait shortened (real run: about 1:29). Boxman creates the template and clone. |
| 02:37.58 | 02:48.61 | One final proof: the supplied verify.sh connects to the clone with boxman’s SSH config. |
| 02:48.61 | 03:04.24 | The real guest reports Rocky 9.8, the baked packages, an active guest agent and completed cloud-init. |
| 03:04.24 | 03:11.92 | Done: one reusable image and a working boxman clone. Viewer templates and scripts accompany the video. |

## Evidence and result

- Raw master: `capture01:/admin/packer-tutorial-v4-raw.mp4`, 825.667 seconds.
- Uncaptioned edit: `capture01:/admin/packer-tutorial-v4-trimmed.mp4`.
- 78 logged keyboard/mouse/clipboard actions and 19 explicit read holds kept;
  no action exclusions and no sped-up typing.
- Real Packer build: 2m58.810s; real boxman boot: 1m29.175s. Both waits are cut
  with visible TIME SKIP captions; the captions use rounded approximate times.
- The SSH proof returned Rocky 9.8, the four baked packages, active
  qemu-guest-agent, and completed NoCloud initialization. Boxman's template
  identity `packerv4-template` is visible, not Packer's `packer-build` hostname.
- Full error-fatal decode: all 2,303 frames. Reviewed all 19 scene outcomes,
  start/middle/full frames for all 14 typed strings (10 shell commands and
  4 editor file paths), the whole cut at 2-second intervals, and the final frame.
- v4-only domains, networks, pools, generated credentials and build workspace
  were removed. The recording desktop stopped. All older videos are untouched.

Final artifact: `~/Videos/scds/packer-tutorial-recording-v4.mp4`, with a second
copy at `outputs/2026-09-01-packer-video-tutorial/packer-tutorial-recording-v4.mp4`.
SHA-256: `f66af818be59750d17899a4998a7737a5b669b6a20fe2ef414c9478a7c47dab8`.

Local evidence is in `outputs/2026-09-01-packer-video-tutorial/evidence-v4/`.
The VM retains action/scene logs, the exact edit manifest, decode report, and
command-review manifest. Media and generated evidence are gitignored.

Git remote `origin` is `git@github.com:Orski174/work-env.git`. Read-only access
checks using both normal Git configuration and noninteractive SSH failed with
`Permission denied (publickey)` (no SSH agent available), so no push was made.
No video was uploaded and no GitLab issue comment was posted.
