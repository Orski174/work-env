# packer-video-tutorial

Created: 2026-09-01 · Tracks scds-infra #237 and command-center Vikunja Work #410.

## Goal

Provide a recording-ready tutorial script for the Packer proof of concept from
scds-infra #184. The tutorial builds a Rocky Linux 9 qcow2 with Packer's qemu
builder, bakes in the package set boxman's Rocky template normally installs at
boot, clones and boots it through boxman, and explains the three high-value
failure modes found during scouting.

## Deliverable

- [tutorial-script.md](tutorial-script.md) — narration, exact terminal commands,
  representative expected output, recording cues, verification, and teardown.

This task deliberately does not copy the Packer HCL, NoCloud seed, boxman config,
or driver. It uses the proven files in the
[2026-08-08 scouting task](../2026-08-08-packer-rancher-scouting/README.md):

- [template.pkr.hcl](../2026-08-08-packer-rancher-scouting/packer/template.pkr.hcl)
- [boxman-test/conf.yml](../2026-08-08-packer-rancher-scouting/packer/boxman-test/conf.yml)
- [run.sh](../2026-08-08-packer-rancher-scouting/packer/run.sh)
- [scouting notes](../2026-08-08-packer-rancher-scouting/notes.md)

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
