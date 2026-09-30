# Packer to boxman — polished five-minute cut

**Target length:** 4:55 (hard cap: 5:00)

**Audience:** operators onboarding to the libvirt/boxman workflow

**Source:** the verified Packer scouting recipe from scds-infra #184

The Packer build and boxman template rebuild are run for real immediately before
capture. Their logs and artifacts stay in place. The recording shows the useful
checkpoints and live guest proof, but cuts the image-copy, package-install, and
boot waits.

## 0:00–0:19 — what this proves

**On screen:** title card, then `./run.sh install-packer`.

**Narration**

> Let's take Rocky 9 through Packer, then hand the finished image to boxman.
> This is the working trial from scds-infra #184, condensed to the parts worth
> keeping. I've cut the waiting out; we'll stay on what explains the workflow.
>
> First, make sure this is HashiCorp Packer, not sc1's old dictionary utility.
> Version 1.16 is already installed, so we're ready.

## 0:19–0:59 — the Packer recipe

**On screen:**

```bash
rg -n '^  (iso_url|iso_checksum|disk_image|cpu_model)|\["-serial"|sudo dnf install|sudo cloud-init clean' template.pkr.hcl
sed -n '91,116p' template.pkr.hcl
```

**Narration**

> Here's the whole Packer recipe in seven lines. `disk_image = true` tells
> Packer the Rocky download is already bootable; it isn't an installer ISO.
> `cpu_model = "host"` keeps Rocky's x86-64-v2 baseline happy, and serial output
> gives us early-boot errors.
>
> The shell step bakes in the four packages boxman would otherwise install on
> first boot. Cloud-init cleanup stays last, so boxman gets a fresh image
> instead of Packer's instance state.

## 0:59–1:38 — the real build, without the wait

**On screen:** selected checkpoints from the just-completed build log, followed
by the artifact metadata.

```bash
rg -ni 'configuration is valid|connected to ssh|provisioning with shell|complete!|finished after|>> built:' /admin/recording-assets/packer-polished-build.log
tail -n 12 /admin/recording-assets/packer-polished-build.log
qemu-img info output-rocky9/rocky9-packer-base.qcow2 | sed -n '1,4p;/corrupt:/p'
```

**Narration**

> I ran the real build just before recording. Here are the checkpoints, with
> the wait removed. Packer validated the HCL, booted with KVM, and connected
> over its temporary SSH key. It installed the packages, cleaned the guest,
> and wrote the qcow2. No package spinner needed.
>
> The result is a qcow2 with a 19.5-gigabyte virtual disk and under a gigabyte
> allocated. That's the handoff artifact.

## 1:38–2:22 — boxman handoff

**On screen:**

```bash
rg -n 'image: file|No `packages:`|base_image:|hostname:' boxman-test/conf.yml
sed -n '14,32p' boxman-test/conf.yml
rg -ni "creating template 'packer_rocky9'|copying image .*rocky9-packer-base|QEMU guest agent is responding|successfully started the vm|all VMs are running$|All vms have ip addresses|ssh connection verified:|^real" /admin/recording-assets/packer-polished-up.log
```

**Narration**

> Boxman takes that local qcow2 through `PACKER_IMAGE_PATH`. There's no package
> list here; that work already happened in Packer. It builds a reusable
> template and clones `node01` from it.
>
> Here's the real `up --rebuild-templates` result from this run, with the boot
> waits cut. The template is healthy, the clone is running, it has an IP, and
> SSH is verified.

## 2:22–2:56 — live proof

**On screen:**

```bash
./run.sh status
ssh -F ~/workspaces/boxmandev/packer_scouting_test/ssh_config cluster_1_node01 'hostname; cat /etc/rocky-release; rpm -q vim-enhanced curl qemu-guest-agent openssh-server; systemctl is-active qemu-guest-agent; sudo grep -E "Cloud-init .* finished at" /var/log/cloud-init.log | tail -1'
```

**Narration**

> Now let's prove the clone instead of trusting the orchestration log. One SSH
> command checks everything together. It's Rocky 9.8, the four packages are
> already present, the guest agent is active, and cloud-init ran from boxman's
> NoCloud seed.
>
> The hostname is boxman's template name, not Packer's build hostname. That's
> the cloud-init regression check.

## 2:56–4:16 — the three gotchas

### Stale Rocky image pin

**On screen:** labelled historical 404 excerpt, then the current URL/checksum.

**Narration**

> Three gotchas are the real reason to keep this example. First, Rocky rotates
> point-release downloads. An old pinned 9.7 URL started returning 404. Refresh
> the `latest` link, then pin the resolved filename and its real checksum.

### CPU model and serial output

**On screen:** labelled historical serial excerpt, then the current fix.

**Narration**

> Second, without `cpu_model = "host"`, Rocky can die before SSH ever starts.
> Packer only says it's waiting for SSH; the serial log shows the x86-64-v2
> failure. Pass through the host CPU and keep serial capture on. That turns a
> timeout into a diagnosis.

### Cloud-init state

**On screen:** labelled historical hostname symptom, final cleanup line, then
the live clone's hostname.

**Narration**

> Third, Packer's cloud-init state can leak into every clone. Skip cleanup and
> the VM still boots, but it keeps `packer-rocky9-build` as its hostname. Keep
> `cloud-init clean --logs --seed` last. The live clone reports
> `rocky9-packer-built-template`, so the state didn't leak.

## 4:16–4:55 — teardown and close

**On screen:**

```bash
set -o pipefail
./run.sh destroy --auto-accept 2>&1 | rg -i 'shut down successfully|network .*undefined successfully|removed .*packer_scouting_test$|destroy complete'
```

Then show the end card.

**Narration**

> That's the proof. A normal destroy removes the clone, network, SSH files, and
> workspace. Don't use boxman's broad `--templates` cleanup on a shared host.
>
> The pattern works, but the recommendation is still adopt later; boxman's YAML
> path is simpler. Keep this reference for three guardrails: refresh the image
> pin, use the host CPU with serial capture, and clean cloud-init state last.
> That's the whole path.

**End card:** `scds-infra #237 · source trial #184 · Vikunja Work #410`
