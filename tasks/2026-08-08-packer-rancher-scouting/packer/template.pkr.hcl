# Packer scouting trial (scds-infra #184).
#
# Builds a Rocky Linux 9 base qcow2 from the SAME upstream GenericCloud image
# boxman's own `rocky-9.7-minimal-base-template-cloudinit` template uses
# (~/git/boxman/boxes/tiny-libvirt-rocky-9-cloudinit/conf.yml), so the two
# pipelines are directly comparable. Packages that boxman's template installs
# via cloud-init `packages:` on every first boot (vim, curl, qemu-guest-agent,
# openssh-server) are baked in here instead — the point of the trial is
# whether "bake once, boot fast" (Packer) beats "reinstall every clone via
# cloud-init" (boxman today) for a fleet's base image.
#
# The NoCloud seed under http/ is ONLY for Packer's own SSH communicator
# during the build (see run.sh, which renders http/user-data from
# http/user-data.tmpl with a per-run ephemeral keypair). It has nothing to do
# with the cloud-init boxman applies later when it clones this image — that
# still runs, unchanged, from packer/boxman-test/conf.yml.

packer {
  required_plugins {
    qemu = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable "ssh_private_key_file" {
  type    = string
  default = "id_ed25519_packer"
}

variable "output_directory" {
  type    = string
  default = "output-rocky9"
}

source "qemu" "rocky9" {
  # Same source (Rocky 9 GenericCloud) family as boxman's own rocky-9
  # template, re-pinned to the current release: the 9.7 build referenced by
  # boxman's own boxes/tiny-libvirt-rocky-9-cloudinit/conf.yml has already
  # been rotated out of download.rockylinux.org (404), which is itself a
  # data point for the write-up — Rocky only mirrors a few point releases,
  # so any pinned URL (Packer's or boxman's own template `image.uri`) needs
  # periodic re-pinning either way.
  iso_url      = "https://download.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2"
  iso_checksum = "sha256:92c206cc6f790c61583247eefe87890f8828420662c17cacf247cec78ab4eec8"
  disk_image   = true

  output_directory = var.output_directory
  vm_name           = "rocky9-packer-base.qcow2"
  format            = "qcow2"
  disk_size         = "20000M"
  disk_compression  = true

  accelerator    = "kvm"
  headless       = true
  net_device     = "virtio-net"
  disk_interface = "virtio"
  memory         = 2048
  cpus           = 2
  # Without this, QEMU falls back to a conservative default CPU model that
  # lacks the x86-64-v2 baseline (SSE4.2 etc.) RHEL/Rocky 9.4+'s glibc now
  # requires — the guest panics at PID 1 with "Fatal glibc error: CPU does
  # not support x86-64-v2" before anything (incl. cloud-init) ever runs, and
  # Packer just sees "Timeout waiting for SSH" with no indication why (only
  # visible by capturing the serial console, see qemuargs below). Hit this
  # on the first real attempt — 30 minutes burned waiting on a VM that was
  # never going to boot.
  cpu_model = "host"

  # NoCloud seed ISO, generated inline by the qemu builder from http/.
  cd_label = "cidata"
  cd_files = ["http/meta-data", "http/user-data"]

  # Cloud images' serial console is the only window into what cloud-init is
  # doing during the (first) 30min hang this trial hit — capture it to a file
  # instead of guessing blind next time.
  qemuargs = [
    ["-serial", "file:packer-serial.log"]
  ]

  communicator          = "ssh"
  ssh_username           = "packer"
  ssh_private_key_file   = var.ssh_private_key_file
  ssh_timeout            = "10m"

  shutdown_command = "sudo shutdown -h now"
}

build {
  sources = ["source.qemu.rocky9"]

  provisioner "shell" {
    # Matches the package list boxman's rocky-9 template installs via
    # cloud-init `packages:` — baked in at build time instead of every clone.
    inline = [
      "sudo dnf install -y vim curl qemu-guest-agent openssh-server",
      "sudo systemctl enable qemu-guest-agent",
      "sudo dnf clean all",
      # NOT run in the first successful build — found afterwards, by symptom.
      # Packer boots the image once to provision it, and that boot leaves
      # cloud-init instance/semaphore state (incl. the hostname it set for
      # ITS OWN NoCloud seed) baked into the final qcow2. On the resulting
      # clone's first real boot, cc_set_hostname's once-per-instance check
      # can short-circuit against that leftover state, so boxman's own
      # per-clone hostname never applies (observed: clone kept the
      # template's build-time hostname instead of the `hostname:` set in
      # boxman's own cloud-init). `cloud-init clean` resets that state so
      # the clone's first boot is treated as a genuinely fresh instance —
      # exactly what boxman's own template mechanism gets for free, since
      # its templates are built by a single from-scratch boot with no
      # separate "provisioning boot" to leave residue behind.
      "sudo cloud-init clean --logs --seed",
    ]
  }
}
