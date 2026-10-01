# Files used in the v4 Packer tutorial

This is the complete viewer bundle, independent of the capture automation.
In the video this directory is staged as `~/packer-tutorial`.

Prerequisites: a disposable Linux workstation with KVM access, Packer and its
QEMU plugin, QEMU utilities, `cloud-localds`/ISO tooling required by Packer,
OpenSSH, OpenSSL, Python 3, libvirt, virt-install/virt-clone, and boxman on PATH.
The recorded workstation is Ubuntu 24.04; the built guest is Rocky Linux 9.8.
Boxman's libvirt provider needs passwordless sudo in this isolated demo.
Choose a free `192.168.N.0/24` subnet and a unique `DEMO_NAME` before booting.

1. Open `packer-values.txt` in a text editor beside a terminal. Review the
   values for your environment. The pinned URL is a **cloud disk image**, not
   an installer ISO (`disk_image = true`). If a mirror rotates the release,
   replace the URL and trusted SHA-256 together.
2. Create a working directory and copy the supplied templates/scripts:

   ```bash
   mkdir packer-demo && cd packer-demo
   cp -R ~/packer-tutorial/. .
   ```

3. Inspect `template.pkr.hcl`; it does not need rewriting. In the editor,
   select/copy the complete values sheet (Ctrl+A, Ctrl+C). In the terminal run
   `cat > demo.env`, paste with Ctrl+Shift+V, then press Ctrl+D on the empty last
   line. This copies the six environment values without retyping long content.
   `cp packer-values.txt demo.env` is an equivalent non-GUI alternative.
4. Run the provided scripts:

   ```bash
   ./prepare.sh
   ./build.sh
   ./boot.sh
   ./verify.sh
   ```

`prepare.sh` creates a fresh SSH key and private `.demo-password`, fills the
NoCloud seed (`user-data.in`) and `boxman.yml.in`, then initializes/formats/
validates Packer. It refuses to overwrite existing credentials. `build.sh`
loads the four `PKR_VAR_` values and builds the qcow2. `boot.sh` points boxman at
that image. `verify.sh` performs one SSH-based proof from the actual clone.
The video cuts the build/boot waits and labels both time skips; do not expect
these operations to complete in the video's playback time.

The demo deliberately uses passwordless guest sudo and temporary credentials.
It is **not a production-hardening recipe**. Do not commit generated secrets,
the NoCloud seed, workspace, cache or image output. The included `.gitignore`
covers those artifacts (keep custom output paths out of version control too).

After trying it, source `demo.env`, export `PACKER_IMAGE_PATH` and
`BOXMAN_ADMIN_PASS` as shown in `boot.sh`, then use
`boxman --conf boxman.yml destroy --auto-accept`. Boxman may retain the reusable
template and storage pools; inspect `virsh list --all`, `virsh pool-list --all`
and `virsh net-list --all`, and remove only resources belonging to your unique
demo name. Remove the disposable work directory and generated credentials only
after all of its VMs are stopped and undefined.
