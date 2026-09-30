packer {
  required_plugins {
    qemu = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

source "qemu" "rocky9" {
  iso_url      = "__ROCKY_IMAGE_URL__"
  iso_checksum = "sha256:__ROCKY_IMAGE_SHA256__"
  disk_image   = true

  output_directory = "output-rocky9"
  vm_name           = "rocky9-packer-base.qcow2"
  format            = "qcow2"
  disk_size         = "10240M"
  disk_compression  = true

  accelerator    = "kvm"
  headless       = true
  net_device     = "virtio-net"
  disk_interface = "virtio"
  memory         = 2048
  cpus           = 2
  cpu_model      = "__CPU_MODEL__"

  cd_label = "cidata"
  cd_files = ["http/meta-data", "http/user-data"]
  qemuargs = [
    ["-serial", "file:packer-serial.log"]
  ]

  communicator        = "ssh"
  ssh_username         = "packer"
  ssh_private_key_file = "id_ed25519_packer"
  ssh_timeout          = "10m"
  shutdown_command     = "sudo shutdown -h now"
}

build {
  sources = ["source.qemu.rocky9"]

  provisioner "shell" {
    inline = [
      "sudo dnf install -y vim curl qemu-guest-agent openssh-server",
      "sudo systemctl enable qemu-guest-agent",
      "sudo dnf clean all",
      "sudo cloud-init clean --logs --seed",
    ]
  }
}
