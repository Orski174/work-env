# Video script: Packer to boxman, with the gotchas that matter

**Target length:** 12–15 minutes

**Audience:** operators onboarding to the sc1 libvirt/boxman workflow

**Recorded on:** `scds001` (`sc1`)

**Source:** the proven [2026-08-08 Packer scouting
trial](../2026-08-08-packer-rancher-scouting/README.md), not a new example

Output below is from the 2026-09-01 re-run. Treat timestamps, ports, IP
addresses, package patch versions, image size, and elapsed times as variable.
The structural success lines are what viewers should compare.

## Recording preparation — do before capture

This section is for the presenter, not narration.

Run on `scds001`, where KVM/libvirt and boxman are available. The boxman CLI is
normally found on `PATH` or at `~/.conda/envs/boxman/bin/boxman`. The driver
selects either automatically.

Start in the proven Packer sub-trial:

```bash
cd ~/git/work-env/tasks/2026-08-08-packer-rancher-scouting/packer
pwd
```

Expected:

```text
/home/orski/git/work-env/tasks/2026-08-08-packer-rancher-scouting/packer
```

Packer refuses to overwrite an existing output directory. If this is a repeat
recording, remove only the generated Packer output and ephemeral build key:

```bash
test ! -e output-rocky9 || ./run.sh clean
```

Expected: no output. Do not run this if the current qcow2 must be retained.

Preflight the test subnet before recording:

```bash
ip -4 route show | rg '^192\.168\.30\.0/24' || true
```

Expected on an unused host: no output. On 2026-09-01, another project owned the
subnet:

```text
192.168.30.0/24 dev virbr9 proto kernel scope link src 192.168.30.1 linkdown
```

If there is output, temporarily change all three `192.168.30.*` addresses in
`boxman-test/conf.yml` to an unused private `/24`. The verification run used
`192.168.31.0/24`. Back up the file first and restore it after teardown. This
is host housekeeping, not a Packer lesson, so omit it from the recording.

If `rocky9-packer-built-template` already exists from an earlier run, use
`./run.sh up --rebuild-templates` in scene 4. On a genuinely clean host,
`./run.sh up` is enough. Never use `boxman destroy --templates` on sc1: that
flag removes the shared `~/boxman-templates` directory across projects.

## Scene 1 — what we are proving (about 45 seconds)

**On screen:** title, then the scouting task README's Packer recommendation.

**Narration**

> This tutorial takes a Rocky Linux cloud image through Packer and hands the
> resulting qcow2 to boxman. We are using the exact proof of concept from
> scds-infra issue 184, so this is knowledge capture, not a new implementation.
>
> Packer's qemu builder boots the same Rocky GenericCloud image family used by
> boxman's Rocky 9 template. Packer installs the base package set once, cleans
> the image, and emits a reusable qcow2. Boxman then consumes that local file as
> a normal base image, builds its template, and clones a test VM.
>
> The adoption verdict is still “adopt later.” Boxman's own YAML template path
> is simpler and already works. The value today is knowing the repeatable path
> and, especially, the three failures that cost time in the first scouting pass.

**Terminal**

```bash
./run.sh install-packer
```

**Expected output, abridged**

```text
>> installing HashiCorp Packer (dnf)
Package dnf-plugins-core-... is already installed.
Package packer-1.16.0-1.x86_64 is already installed.
Complete!
Packer v1.16.0
```

**Narration**

> One local trap: sc1 historically also had `/usr/sbin/packer` from
> `cracklib-dicts`; that is a password-dictionary utility, not HashiCorp
> Packer. The driver installs and then prints the HashiCorp version we need.

## Scene 2 — inspect the qemu image definition (about 2 minutes)

**Terminal**

```bash
rg -n 'iso_url|iso_checksum|disk_image|cpu_model|qemuargs|dnf install|cloud-init clean' template.pkr.hcl
```

**Expected output**

```text
45:  iso_url      = "https://download.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2"
46:  iso_checksum = "sha256:92c206cc6f790c61583247eefe87890f8828420662c17cacf247cec78ab4eec8"
47:  disk_image   = true
69:  cpu_model = "host"
78:  qemuargs = [
97:      "sudo dnf install -y vim curl qemu-guest-agent openssh-server",
113:      "sudo cloud-init clean --logs --seed",
```

**Narration**

> `disk_image = true` is important: the input is already a bootable
> GenericCloud qcow2, not an installer ISO. The URL is pinned to the Rocky 9.8
> build proven on August 8 and re-verified today, with a SHA-256 checksum.
> That is the same upstream image family as boxman's Rocky 9 template.
>
> The build VM runs headless under KVM with two CPUs and two gigabytes of RAM.
> `cpu_model = "host"` is deliberate, and the serial console is captured in
> `packer-serial.log`. We will return to both choices in the gotchas section.
>
> Packer needs SSH access only while it is building. The driver generates an
> ephemeral Ed25519 key and renders `http/user-data` from the checked-in
> template. Packer turns `http/meta-data` and that rendered user-data into a
> NoCloud seed CD. Those build credentials are not the credentials boxman uses
> later.

**On screen:** briefly open
`template.pkr.hcl`, `http/user-data.tmpl`, and `run.sh`; do not paste or rewrite
them. Point out `cd_files`, `ssh_private_key_file`, `packer init`, `packer
validate`, and `packer build`.

## Scene 3 — build the qcow2 and bake the packages (about 3 minutes)

**Terminal**

```bash
./run.sh build
```

**Expected output, first phase**

```text
>> generating ephemeral build keypair
The configuration is valid.
qemu.rocky9: output will be in this color.

==> qemu.rocky9: Retrieving ISO
==> qemu.rocky9: Trying https://download.rockylinux.org/.../Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2
==> qemu.rocky9: Creating CD disk...
==> qemu.rocky9: Copying hard drive...
==> qemu.rocky9: Resizing hard drive...
==> qemu.rocky9: Starting VM, booting disk image
==> qemu.rocky9: Waiting for SSH to become available...
==> qemu.rocky9: Connected to SSH!
```

If the key already exists, the `generating ephemeral build keypair` line is
absent. A warm Packer cache also makes the image retrieval nearly immediate.

**Narration while the build runs**

> The qemu builder copies the upstream disk, expands its virtual size to twenty
> gigabytes, boots it, and connects over the temporary SSH key.
>
> “Baking in the cloud-init packages” means we take the package list that
> boxman's Rocky template normally asks cloud-init to install on first boot—
> vim, curl, qemu-guest-agent, and openssh-server—and install it now in Packer's
> shell provisioner. The clone does not need a package transaction on its first
> boot. Some packages already exist in the upstream image; `dnf install` also
> brings them to the current repository patch level.

**Expected output, provisioning phase, abridged**

```text
==> qemu.rocky9: Provisioning with shell script: /tmp/packer-shell...
==> qemu.rocky9: Package curl-... is already installed.
==> qemu.rocky9: Package qemu-guest-agent-... is already installed.
==> qemu.rocky9: Package openssh-server-... is already installed.
==> qemu.rocky9: Installing:
==> qemu.rocky9:  vim-enhanced ...
==> qemu.rocky9: Complete!
==> qemu.rocky9: Gracefully halting virtual machine...
==> qemu.rocky9: Converting hard drive...
```

**Narration**

> The last provisioner command is not optional cleanup. `cloud-init clean
> --logs --seed` removes Packer's build-time instance state so the next consumer
> sees a fresh image. It must remain after every other provisioning command.

**Expected output, completion**

```text
Build 'qemu.rocky9' finished after 57 seconds 265 milliseconds.

==> Builds finished. The artifacts of successful builds are:
--> qemu.rocky9: VM files in directory: output-rocky9

real    0m57.676s
>> built: .../packer/output-rocky9/rocky9-packer-base.qcow2
-rw-r--r-- 1 orski orski 751M ... rocky9-packer-base.qcow2
```

**Terminal**

```bash
qemu-img info output-rocky9/rocky9-packer-base.qcow2
```

**Expected output, abridged**

```text
image: output-rocky9/rocky9-packer-base.qcow2
file format: qcow2
virtual size: 19.5 GiB (20971520000 bytes)
disk size: ...
...
corrupt: false
```

## Scene 4 — hand the artifact to boxman (about 3 minutes)

**Terminal**

```bash
rg -n 'image: file|No `packages:`|base_image:|hostname:' boxman-test/conf.yml
```

**Expected output**

```text
19:    image: file://{{ env("PACKER_IMAGE_PATH") }}
26:    # No `packages:` here — vim/curl/qemu-guest-agent/openssh-server are
31:      hostname: packer-test-node
78:    base_image: rocky9-packer-built-template
104:        hostname: node01
```

**Narration**

> The driver exports the absolute qcow2 path as `PACKER_IMAGE_PATH`. Boxman
> resolves the `file://` URI, copies the Packer artifact into its normal
> template directory, applies its own NoCloud data, and creates the reusable
> `rocky9-packer-built-template`. Notice that there is no cloud-init `packages`
> list here. The packages are already in the disk.
>
> The test cluster then clones one VM named `node01` from that boxman template.
> The VM label and the guest OS hostname are separate concepts in this test:
> after boxman creates the reusable template it disables cloud-init, so the
> clone retains the template's boxman-controlled guest hostname.

Use the first command on a clean host. Use the second for a repeat recording so
boxman cannot silently reuse an older retained template:

```bash
./run.sh up
```

```bash
./run.sh up --rebuild-templates
```

**Expected output, abridged from the repeat-recording command**

```text
no existing VMs found, running full provision...
rebuilding all templates (--rebuild-templates implies --force for create-templates)...
creating template 'packer_rocky9' -> VM name 'rocky9-packer-built-template'
copying image .../output-rocky9/rocky9-packer-base.qcow2 -> .../rocky9-packer-built-template.qcow2
QEMU guest agent is responding. OS is healthy.
guest-exec is available
done marker found: /var/log/hello-cloudinit.log
...
successfully started the vm bprj__packer_scouting_test__bprj_cluster_1_node01
all VMs are running
All vms have ip addresses (waited 15s)
ssh connection verified: rocky9-packer-built-template
ssh access setup complete
via config: ssh -F /home/orski/workspaces/boxmandev/packer_scouting_test/ssh_config cluster_1_node01

real    0m45.927s
```

On this RHEL host boxman may first print `sudo: cloud-localds: command not
found`, then successfully create the seed ISO with `genisoimage`. That is a
handled fallback; continue when `seed ISO created with genisoimage` follows.

**Narration**

> A normal `up` is shorter when the reusable boxman template already exists.
> Today's 45.9-second figure deliberately includes rebuilding that template
> from today's Packer artifact, then cloning, booting, assigning an IP, and
> installing boxman's SSH key. Cloud-init reported its own completion at 10.43
> seconds. Exact timings depend on host load.

## Scene 5 — verify the running clone (about 90 seconds)

**Terminal**

```bash
./run.sh status
```

**Expected output**

```text
Id  Cluster    Name    Provider  State
--  ---------  ------  --------  -------
0   cluster_1  node01  libvirt   running
```

Run all guest checks non-interactively so the proof is visible together:

```bash
ssh -F ~/workspaces/boxmandev/packer_scouting_test/ssh_config cluster_1_node01 '
hostname
cat /etc/rocky-release
rpm -q vim-enhanced curl qemu-guest-agent openssh-server
systemctl is-active qemu-guest-agent
sudo grep -E "Cloud-init .* finished at" /var/log/cloud-init.log | tail -1
'
```

**Expected output from 2026-09-01**

```text
rocky9-packer-built-template
Rocky Linux release 9.8 (Blue Onyx)
vim-enhanced-8.2.2637-26.el9_8.13.x86_64
curl-7.76.1-40.el9_8.5.x86_64
qemu-guest-agent-10.1.0-17.el9_8.5.x86_64
openssh-server-9.9p1-9.el9_8.rocky.0.1.x86_64
active
... Cloud-init v. 24.4-8.el9.rocky.0.1 finished ... Up 10.43 seconds
```

**Narration**

> This proves four things. We booted Rocky 9.8. The four packages are present
> without a clone-time package install. The guest agent is active. And the
> hostname is controlled by boxman's NoCloud/template pass rather than stuck at
> Packer's build seed name, `packer-rocky9-build`. That last difference is the
> proof that Packer's cloud-init state did not leak into the final image.

## Scene 6 — the three gotchas: the real value of this tutorial (about 4 minutes)

### Gotcha 1: a stale Rocky point-release pin fails with 404

**Narration**

> The first scouting build copied boxman's then-current Rocky 9.7 URL. Rocky's
> main download tree rotates older point-release artifacts, so that exact URL
> soon returned 404. Packer failed immediately. This is not unique to Packer:
> any checked-in boxman or Packer URL pointing at a rotated point build has the
> same maintenance burden.

**Failure command**

```bash
packer build template.pkr.hcl
```

**Historical failure output**

```text
==> qemu.rocky9: Retrieving ISO
==> qemu.rocky9: Trying .../Rocky-9-GenericCloud-Base-9.7-20251123.2.x86_64.qcow2
==> qemu.rocky9: error downloading ISO: bad response code: 404
Build 'qemu.rocky9' errored after ...
```

**Fix shown on screen**

```bash
rg -n 'iso_url|iso_checksum' template.pkr.hcl
```

Expected:

```text
45:  iso_url      = "...Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2"
46:  iso_checksum = "sha256:92c206cc6f790c61583247eefe87890f8828420662c17cacf247cec78ab4eec8"
```

**Narration**

> Resolve Rocky's current `latest` link when refreshing the template, then pin
> the resolved immutable filename and its real checksum. Do not replace this
> with an unchecksummed moving URL. Expect to re-pin when Rocky rotates the
> point release.

### Gotcha 2: qemu's default CPU can burn the full SSH timeout

**Narration**

> The expensive failure was leaving `cpu_model` unset. QEMU selected a
> conservative virtual CPU that did not meet Rocky 9.4-and-newer's x86-64-v2
> baseline. The guest crashed at PID 1 before networking, cloud-init, or SSH
> could start. Packer only displayed “Waiting for SSH to become available.” In
> the original pass the SSH timeout was about thirty minutes, so the first
> attempt silently burned that whole window.
>
> The cause was invisible until the qemu serial console was captured. If you
> ever see an unexplained SSH wait, inspect the serial log immediately instead
> of waiting for the timeout.

**Diagnostic command**

```bash
tail -f packer-serial.log
```

**Historical failure output**

```text
Fatal glibc error: CPU does not support x86-64-v2
Kernel panic - not syncing: Attempted to kill init! exitcode=0x00007f00
```

Press `Ctrl-C` after showing the error.

**Fix shown on screen**

```bash
rg -n 'cpu_model|serial' template.pkr.hcl
```

Expected, abridged:

```text
69:  cpu_model = "host"
79:    ["-serial", "file:packer-serial.log"]
```

**Narration**

> `cpu_model = "host"` passes through the KVM host CPU and satisfies Rocky's
> baseline, matching the host-passthrough behavior boxman's libvirt VMs already
> use. Keeping serial capture enabled turns the next early-boot failure into an
> immediate diagnosis instead of an SSH-timeout mystery.

### Gotcha 3: Packer's cloud-init state can leak into every clone

**Narration**

> Packer boots the source image once using its own NoCloud seed. That boot
> writes instance IDs, semaphores, logs, seed data, and the hostname
> `packer-rocky9-build` into the disk. Without cleanup, cloud-init in the final
> image can decide its once-per-instance hostname module already ran. Boxman's
> later NoCloud data is then skipped, and clones inherit Packer's build-time
> hostname.
>
> This is subtle because the VM still boots and SSH still works. Only checking
> the requested hostname reveals the image was not generalized correctly.

**Historical symptom**

```bash
hostname
```

```text
packer-rocky9-build
```

**Fix shown on screen**

```bash
tail -n 22 template.pkr.hcl
```

Expected final provisioner line:

```text
"sudo cloud-init clean --logs --seed",
```

**Narration**

> Keep `sudo cloud-init clean --logs --seed` as the last provisioner command.
> It deletes Packer's instance state, logs, and cached seed before shutdown.
> Today's verified clone reported `rocky9-packer-built-template`, which is
> boxman's hostname, not `packer-rocky9-build`; that is the regression check.

## Scene 7 — teardown and close (about 45 seconds)

**Terminal**

```bash
./run.sh destroy --auto-accept
```

**Expected output, abridged**

```text
The following actions will be performed:
  1. destroy every VM and network defined in 'boxman-test/conf.yml'
  2. remove generated provisioning files (... SSH keys)
  3. remove workspace workdir tree '.../packer_scouting_test'
...
vm ...node01 shut down successfully
network ...packer_scouting_test...nat1 undefined successfully
removed .../workspaces/boxmandev/packer_scouting_test
destroy complete
```

The current boxman/libvirt cleanup path can also print red errors saying an
extra `vdb` volume is not managed by libvirt or that a volume-delete flag is
unsupported. In the verified run, the domain was already undefined, boxman
removed the workspace tree, and the command still ended with `destroy
complete`. Confirm that final line rather than treating the intermediate
libvirt message as a Packer failure.

**Narration**

> Plain destroy removes the test clone, project network, generated SSH material,
> and workspace. It intentionally leaves the reusable shut-off boxman template.
> Do not add `--templates` on this shared host; that cleanup is not scoped to
> this project and can delete other tasks' template files.
>
> The result is a repeatable Packer-to-boxman path and a fast, pre-baked Rocky
> base. The current recommendation remains adopt later: revisit when template
> rebuild time or reliability becomes a real pain point, or when one image must
> target more than libvirt. Until then, the durable value is this working
> reference and the three guardrails: refresh stale image pins, set the qemu CPU
> model and capture serial output, and always clean cloud-init state last.

**End card:** `scds-infra #237 · source trial: #184 · Vikunja Work #410`
