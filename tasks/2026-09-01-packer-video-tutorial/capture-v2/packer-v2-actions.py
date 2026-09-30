#!/usr/bin/env python3
"""Drive the v3 Packer tutorial and gate every step on visual review.

The typing and pointer movement helpers come from the screen-demo-recording
skill. Each completed command gets a pointer-motion action in the parking
strip, which gives the evidence-based trimmer a ground-truth anchor for both
the typed command and its resulting output.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path


GO = Path("/tmp/packer_v3_recording_go")
PROMPT = Path("/tmp/packer_v3_prompt_ready")
LAST_RC = Path("/tmp/packer_v3_last_rc")
PENDING = Path("/tmp/packer_v3_review_pending")
ACK = Path("/tmp/packer_v3_review_ack")
ACTION_LOG = Path("/admin/packer-v3-action.log")
SCENE_LOG = Path("/admin/packer-v3-scenes.jsonl")
REVIEW_DIR = Path("/admin/packer-v3-review")
ASSETS = Path("/admin/recording-assets")
SKILL_SCRIPTS = Path("/admin/screen-demo-recording/scripts")
PYTHON = "/admin/fastgrab-venv/bin/python"
HUMAN_TYPE = SKILL_SCRIPTS / "human_type.py"
HUMAN_MOVE = SKILL_SCRIPTS / "human_move.py"
CAPTURE_FRAME = ASSETS / "capture-frame.py"


def wait_for(path: Path, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.1)
    raise TimeoutError(f"timed out waiting for {path}")


wait_for(GO, 300)


def recording_start() -> float:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if ACTION_LOG.exists():
            for line in ACTION_LOG.read_text(encoding="utf-8").splitlines():
                fields = line.split(" ", 2)
                if len(fields) >= 2 and fields[1] == "recording_start":
                    return float(fields[0])
        time.sleep(0.1)
    raise TimeoutError("recording_start was not written to the action log")


START = recording_start()
WINDOW = subprocess.check_output(
    ["xdotool", "search", "--name", "Packer to boxman"], text=True
).splitlines()[-1]
STEP = 0
PARK_Y = 400


def elapsed() -> float:
    return time.time() - START


def mark(label: str, command: str | None = None) -> None:
    record: dict[str, object] = {"time": round(elapsed(), 6), "label": label}
    if command is not None:
        record["command"] = command
    with SCENE_LOG.open("a", encoding="utf-8") as marker_file:
        marker_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def focus() -> None:
    subprocess.run(["xdotool", "windowfocus", "--sync", WINDOW], check=True)


def skill_script(script: Path, *args: str) -> None:
    env = os.environ.copy()
    env["ACTION_LOG"] = str(ACTION_LOG)
    subprocess.run([PYTHON, str(script), *args], env=env, check=True)


def review_frame(label: str) -> None:
    """Capture the current display and wait for a matching reviewer ack."""
    global STEP
    STEP += 1
    path = REVIEW_DIR / f"{STEP:03d}-{label}.png"
    env = os.environ.copy()
    env["PYTHONPATH"] = "/admin/fastgrab-gdp"
    subprocess.run([PYTHON, str(CAPTURE_FRAME), str(path)], env=env, check=True)
    mark(f"{label}_review", str(path))
    ACK.unlink(missing_ok=True)
    PENDING.write_text(f"{label}\t{path}\n", encoding="utf-8")
    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        if ACK.exists() and ACK.read_text(encoding="utf-8").strip() == label:
            ACK.unlink(missing_ok=True)
            PENDING.unlink(missing_ok=True)
            return
        time.sleep(0.2)
    raise TimeoutError(f"visual review was not acknowledged for {label}")


def type_command(command: str) -> None:
    focus()
    skill_script(HUMAN_TYPE, command)
    subprocess.run(["xdotool", "key", "--window", WINDOW, "Return"], check=True)


def anchor_result() -> None:
    """Move only within the parking strip so the result survives trimming."""
    global PARK_Y
    PARK_Y = 430 if PARK_Y == 400 else 400
    skill_script(HUMAN_MOVE, "1220", str(PARK_Y))


def run(label: str, command: str, timeout: float = 60) -> None:
    mark(f"{label}_typing", command)
    PROMPT.unlink(missing_ok=True)
    LAST_RC.unlink(missing_ok=True)
    type_command(command)
    mark(f"{label}_run_start", command)
    wait_for(PROMPT, timeout)
    rc = int(LAST_RC.read_text(encoding="ascii").strip())
    mark(f"{label}_run_end", command)
    anchor_result()
    review_frame(label)
    if rc != 0:
        raise RuntimeError(f"command failed with {rc}: {command}")


mark("session_start")
skill_script(HUMAN_MOVE, "400", "300", "click")
skill_script(HUMAN_MOVE, "1220", "400")
review_frame("focused_and_parked")

run("workspace", "mkdir packer-boxman-demo-v3 && cd packer-boxman-demo-v3")
run("copy_packer_skeleton", "cp -R ~/tutorial-templates/packer/. .")
run("list_packer_files", "find . -maxdepth 2 -type f | sort")
run("show_packer_placeholders", "rg -n '__[A-Z_]+' template.pkr.hcl http")

run(
    "generate_key",
    "ssh-keygen -q -t ed25519 -N '' -C packer-demo -f id_ed25519_packer",
)
run(
    "set_image_url",
    "ROCKY_IMAGE=https://download.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base-9.8-20260525.0.x86_64.qcow2",
)
run(
    "set_image_sha",
    "ROCKY_SHA=92c206cc6f790c61583247eefe87890f8828420662c17cacf247cec78ab4eec8",
)
run(
    "fill_packer_image",
    "sed -i \"s|__ROCKY_IMAGE_URL__|$ROCKY_IMAGE|; s|__ROCKY_IMAGE_SHA256__|$ROCKY_SHA|; s|__CPU_MODEL__|host|\" template.pkr.hcl",
)
run("show_image_pin", "rg -n 'iso_url|iso_checksum|disk_image' template.pkr.hcl")
run("show_cpu_serial", "rg -n 'cpu_model|serial' template.pkr.hcl")
run(
    "show_provisioning",
    "rg -n 'dnf install|cloud-init clean' template.pkr.hcl",
)

run(
    "fill_seed_identity",
    "sed -i 's|__BUILD_HOSTNAME__|packer-build|g; s|__INSTANCE_ID__|packer-build-001|g' http/meta-data http/user-data",
)
run(
    "fill_seed_key",
    "sed -i \"s|__SSH_PUBLIC_KEY__|$(cat id_ed25519_packer.pub)|\" http/user-data",
)
run("show_seed", "sed -n '1,13p' http/user-data")

run("packer_init", "packer init template.pkr.hcl", timeout=180)
run("packer_fmt", "packer fmt template.pkr.hcl")
run("packer_validate", "packer validate template.pkr.hcl")

run("before_build_clear", "clear")
run("packer_build", "time packer build template.pkr.hcl", timeout=900)
run(
    "inspect_image",
    "qemu-img info output-rocky9/rocky9-packer-base.qcow2 | sed -n '1,5p;/corrupt:/p'",
)
run(
    "set_boxman_input",
    "export PACKER_IMAGE_PATH=\"$PWD/output-rocky9/rocky9-packer-base.qcow2\"",
)
run(
    "show_boxman_input",
    "printf 'boxman input: %s\\n' \"${PACKER_IMAGE_PATH#$PWD/}\"",
)

run("before_boxman_config_clear", "clear")
run("copy_boxman_skeleton", "cp ~/tutorial-templates/boxman.yml .")
run("show_boxman_placeholders", "rg -n '__[A-Z_]+' boxman.yml")
run(
    "fill_boxman_core",
    "sed -i 's|__PROJECT__|packer_boxman_demo_v3|g; s|__IMAGE_ENV__|PACKER_IMAGE_PATH|g; s|__TEMPLATE_NAME__|rocky9-packer-template-v3|g' boxman.yml",
)
run(
    "fill_boxman_workspace",
    "sed -i 's|__WORKSPACE_PATH__|~/packer-boxman-demo-v3/workspace|g; s|__NETWORK_PREFIX__|192.168.77|g' boxman.yml",
)
run(
    "fill_boxman_hosts",
    "sed -i 's|__TEMPLATE_HOSTNAME__|packer-template|g; s|__VM_HOSTNAME__|demo-node|g' boxman.yml",
)
run(
    "show_boxman_values",
    "rg -n 'project:|name: rocky|image: file|hostname:|base_image:|address:' boxman.yml",
)

run("before_boxman_up_clear", "clear")
run("boxman_up", "time boxman --conf boxman.yml up", timeout=600)

run("before_verification_clear", "clear")
run("boxman_ps", "boxman --conf boxman.yml ps")
run(
    "guest_verify",
    "ssh -F ~/packer-boxman-demo-v3/workspace/ssh_config demo_demo-node 'hostname; cat /etc/rocky-release; rpm -q vim-enhanced curl qemu-guest-agent openssh-server; systemctl is-active qemu-guest-agent; sudo grep -E \"Cloud-init .* finished at\" /var/log/cloud-init.log | tail -1'",
    timeout=180,
)

mark("session_complete")
review_frame("session_complete")
