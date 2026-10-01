# packer-video-tutorial

Created: 2026-09-01 · Tracks scds-infra #237 and command-center Vikunja Work #410.

## Goal

Provide a recording-ready tutorial script for the Packer proof of concept from
scds-infra #184. The tutorial builds a Rocky Linux 9 qcow2 with Packer's qemu
builder, bakes in the package set boxman's Rocky template normally installs at
boot, clones and boots it through boxman, and explains the three high-value
failure modes found during scouting.

## Deliverable

- [v4-tutorial-script.md](v4-tutorial-script.md) — 3:11.92 desktop redo,
  frame-derived caption map, verification record and handoff paths.
- [viewer-files/](viewer-files/) — self-contained v4 templates, values sheet,
  and short prepare/build/boot/verify scripts a viewer can use directly.
- [capture-v4/](capture-v4/) — desktop capture, review-gated copy/paste actions,
  frame-accurate action-log trim, separate caption band, and evidence checks.
- [tutorial-script.md](tutorial-script.md) — narration, exact terminal commands,
  representative expected output, recording cues, verification, and teardown.
- [polished-tutorial-script.md](polished-tutorial-script.md) — condensed 4:55
  final-cut script with natural narration and long-running waits removed.
- [from-scratch-tutorial-script.md](from-scratch-tutorial-script.md) — final
  6:57 v3 scene/caption map for the generic, from-scratch recording.
- [capture-v2/](capture-v2/) — fillable templates, keystroke automation,
  screen-demo action-log capture/trim pipeline, and dedicated-band caption
  renderer used for the final take.

The original September 1 script used the proven files in the
[2026-08-08 scouting task](../2026-08-08-packer-rancher-scouting/README.md):

- [template.pkr.hcl](../2026-08-08-packer-rancher-scouting/packer/template.pkr.hcl)
- [boxman-test/conf.yml](../2026-08-08-packer-rancher-scouting/packer/boxman-test/conf.yml)
- [run.sh](../2026-08-08-packer-rancher-scouting/packer/run.sh)
- [scouting notes](../2026-08-08-packer-rancher-scouting/notes.md)

The later v3/v4 bundles are self-contained; v4 viewers do not need the scouting
directory or the capture VM's private files.

## Validation on 2026-09-01

Re-ran the existing trial on `scds001` with HashiCorp Packer 1.16.0:

- `./run.sh build` produced the Rocky 9.8 qcow2 in 57.7 seconds (751 MiB).
- A retained boxman template was deliberately rebuilt from that new artifact.
- The configured `192.168.30.0/24` test subnet was occupied by another live
  project, so the verification run temporarily used unused
  `192.168.31.0/24`; the source config was restored afterwards.
- Clean boxman template rebuild, clone, boot, IP assignment, and SSH setup took
  45.9 seconds. Cloud-init itself reported completion at 10.43 seconds.
- SSH verification confirmed Rocky 9.8, all four baked packages,
  `qemu-guest-agent` active, and a boxman-controlled hostname rather than
  Packer's build-time hostname.
- `./run.sh destroy --auto-accept` removed the test clone, network, SSH material,
  and workspace. The reusable shut-off boxman template remains, as intended.

No Packer or boxman source was changed by this documentation task.

## Superseded cut on 2026-09-03

- Re-recorded from the same native Packer/libvirt/boxman environment on
  `capture01`; the real build and template rebuild were staged immediately
  before capture, then their waits were replaced by actual log checkpoints.
- Runtime is 4:55 at 1280×800 and 24 fps. This rejected review artifact is
  preserved as
  `outputs/2026-09-01-packer-video-tutorial/packer-tutorial-recording-2026-09-03-rejected.mp4`
  and is gitignored.
- SHA-256:
  `0555396308b2f7ea9db5b9d76874531c5b53ea1bbbc1a7bbc1713a0a87042f69`.
- Full decode, all 7,080 frames, representative scene transitions, subtitle
  synchronization, live guest proof, and the filtered teardown result were
  verified before transfer.

## From-scratch final cut on 2026-09-04

- Recorded in the native Packer/libvirt/boxman environment. The terminal uses
  a generic prompt and work directory, assumes the tools are installed, and
  fills the Packer, NoCloud, and boxman template values live.
- Every build and `boxman up` frame remains in order. Their long-running
  sections play at 12× and 10× with visible speed badges; the surrounding
  typing and verification stay at natural speed.
- Final runtime is 2:43.42 at 1280×800, 24 fps, H.264/yuv420p. The generated
  MP4 is
  `outputs/2026-09-01-packer-video-tutorial/packer-tutorial-recording.mp4`
  and is gitignored.
- SHA-256:
  `bbd32df702addb06297f604a484c2ce1228585696466a2abefd304c2e554c717`.
- Verified by a complete decode of all 3,922 frames, transition-by-transition
  subtitle review, a transcript leak scan, and matching checksums before and
  after transfer.
- The unedited 8:29 raw take remains on `capture01` at
  `/admin/packer-tutorial-v2-raw.mp4`. All transient tutorial domains,
  networks, storage pools, build images, and intermediate encodes were removed.

## Caption-band v3 on 2026-09-30

- Re-recorded the real Packer → KVM → boxman workflow with the
  `screen-demo-recording` skill. Human-paced typing and pointer actions were
  logged as trim ground truth, and every completed command was gated on a
  visually inspected screenshot before the next step ran.
- The action-log trim keeps all 34 typed commands, compresses the real 4:17
  Packer build and 1:13 boxman run, and holds their proven result frames long
  enough to read. The final runtime is 6:57.25 at 1920×1080 and 12 fps.
- The 1280×800 capture is scaled to 1440×900 and centered in the top of the
  final canvas. Captions render only in a separate 180-pixel dark band below
  it, so they cannot cover terminal commands or output.
- Final artifact:
  `outputs/2026-09-01-packer-video-tutorial/packer-tutorial-recording-v3.mp4`
  (gitignored), SHA-256
  `bd14c1b75720c1a5e6db01a0e5b6fbd29bfe5c86478da6e0ad5e4ccef2699a7e`.
- Verified by full decoding of all 5,007 frames, an end-to-end contact-sheet
  review, a targeted midpoint frame for every typed command, and matching
  checksums before and after transfer.
- The new uncaptioned master remains on `capture01` at
  `/admin/packer-tutorial-v3-retimed.mp4`. All v3 tutorial domains, networks,
  storage pools, build images, and work directories were removed after the
  recording.
