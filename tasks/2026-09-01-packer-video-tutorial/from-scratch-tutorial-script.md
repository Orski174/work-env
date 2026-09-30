# Packer to boxman — from-scratch tutorial v3

Target: 6:57 · 1920×1080 · 12 fps · terminal in the upper 900 px · captions in
an independent 180 px dark band below the terminal

This revision starts in a generic work directory, assumes Packer and boxman are
installed, and fills generic skeleton files on camera. The real Packer build
and `boxman up` run in the recorded session; the action-log trim keeps every
typed command and compresses their waits. Times below refer to the v3 final.

| Time | What happens on screen | Caption |
| --- | --- | --- |
| 00:04.2–00:14.3 | Create and enter `~/packer-boxman-demo-v3`. | Let's build a reusable Rocky Linux image with Packer, then boot it with boxman. |
| 00:14.7–00:30.1 | Copy and list the Packer and NoCloud skeletons. | Copy the Packer and NoCloud skeletons into a clean work directory. |
| 00:30.4–00:38.4 | Show the open placeholders. | The fillable templates leave every environment-specific value visible. |
| 00:38.7–00:49.0 | Generate a temporary SSH key. | First, make a temporary SSH key for the Packer build. |
| 00:49.3–01:08.7 | Set the Rocky 9.8 cloud-image URL. | Pin the exact Rocky 9.8 cloud-image URL instead of relying on a moving latest release. |
| 01:09.0–01:21.9 | Set the SHA-256 digest. | Rocky rotates point-release files, so update the filename and SHA-256 checksum as a pair. |
| 01:22.2–01:42.4 | Fill the Packer image values and CPU model. | Fill the pinned image values and select the host CPU model in the Packer template. |
| 01:42.7–01:51.7 | Show the resolved image pin. | These resolved values make the image source and checksum auditable before the build. |
| 01:52.0–01:59.8 | Show `cpu_model = "host"` and the serial log setting. | Use the host CPU. An emulated model can fail Rocky's x86-64-v2 check and look like an SSH timeout. |
| 02:00.1–02:09.9 | Show package installation and final cloud-init cleanup. | Packages go into the image once. Cloud-init cleanup stays last so clones do not inherit build state. |
| 02:10.2–02:48.4 | Fill and show the NoCloud metadata and user data. | This NoCloud seed gives Packer temporary SSH access while the guest is being built. |
| 02:48.7–03:09.3 | Run `packer init`, `packer fmt`, and `packer validate`. | Initialize the plugin, format the HCL, and validate it before starting the build. |
| 03:13.0–03:21.4 | Start the real Packer build and show its initial download/check. | Packer starts from the pinned Rocky image and verifies its SHA-256 checksum. |
| 03:21.7–03:27.2 | Show the held successful build result after the compressed wait. | After KVM provisioning and cleanup, Packer converts the qcow2 and finishes successfully. |
| 03:27.6–03:40.6 | Run `qemu-img info`. | The artifact is a healthy 10 GiB virtual disk with about 792 MiB allocated. |
| 03:40.9–04:02.7 | Export and print `PACKER_IMAGE_PATH`. | That qcow2 is the handoff. Its path becomes an environment value for boxman. |
| 04:06.4–04:19.8 | Copy the boxman skeleton and show its placeholders. | Now copy the boxman skeleton and inspect the values that still need filling. |
| 04:20.2–04:41.5 | Fill the project, image environment variable, and template. | Set the project, image environment variable, and reusable template identity. |
| 04:41.9–04:59.1 | Fill the workspace and subnet. | Set the workspace and a private subnet for the demo environment. |
| 04:59.5–05:15.0 | Fill the template and VM hostnames. | Give the template and cloned VM distinct hostnames so their roles stay clear. |
| 05:15.4–05:29.1 | Show the completed boxman values. | No packages are installed here; that work is already baked into the image. |
| 05:32.8–05:42.7 | Start the real `boxman up`. | With the values visible, bring the environment up. |
| 05:43.0–05:48.7 | Show the held successful Boxman result after the compressed wait. | Boxman creates the template and clone, then verifies networking and SSH. |
| 05:52.4–05:58.1 | Run `boxman ps`. | boxman ps confirms that the cloned node is running. |
| 05:58.5–06:16.0 | Type the SSH verification command. | One SSH command now checks the guest itself, using boxman's generated SSH config. |
| 06:16.2–06:35.0 | Finish typing the complete guest check. | The check covers the hostname, Rocky release, baked packages, guest agent, and cloud-init result. |
| 06:35.3–06:42.0 | Show the Rocky release, package versions, and agent status. | Rocky 9.8 is up with the baked packages and qemu guest agent active. |
| 06:42.2–06:49.0 | Show cloud-init's finished line and NoCloud datasource. | Cloud-init finished cleanly from NoCloud, so the clone did not inherit stale build state. |
| 06:49.2–06:56.8 | Hold the complete verification output. | The clone kept boxman's template identity, not Packer's build-time hostname. |

## Commands shown

The capture automation in
[`capture-v2/packer-v2-actions.py`](capture-v2/packer-v2-actions.py) contains
the exact keystrokes and commands used for the take. The fillable source files
live under [`capture-v2/templates`](capture-v2/templates).

The final verification checks:

```bash
boxman --conf boxman.yml ps
ssh -F ~/packer-boxman-demo-v3/workspace/ssh_config demo_demo-node \
  'hostname; cat /etc/rocky-release; rpm -q vim-enhanced curl qemu-guest-agent openssh-server; systemctl is-active qemu-guest-agent; sudo grep -E "Cloud-init .* finished at" /var/log/cloud-init.log | tail -1'
```
