#!/usr/bin/env python3
"""Render v3 captions in a dedicated band below the terminal image."""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path


INPUT = "/admin/packer-tutorial-v3-retimed.mp4"
OUTPUT = "/admin/packer-tutorial-v3-final.mp4"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
SCREEN_X = 240
CAPTION_TOP = 900
CAPTION_HEIGHT = 180


@dataclass(frozen=True)
class Caption:
    text: str
    start: float
    end: float


CAPTIONS = [
    Caption(
        "Let's build a reusable Rocky Linux image with Packer, then boot it with boxman.",
        4.2,
        14.3,
    ),
    Caption(
        "Copy the Packer and NoCloud skeletons into a clean work directory.",
        14.7,
        30.1,
    ),
    Caption(
        "The fillable templates leave every environment-specific value visible.",
        30.4,
        38.4,
    ),
    Caption("First, make a temporary SSH key for the Packer build.", 38.7, 49.0),
    Caption(
        "Pin the exact Rocky 9.8 cloud-image URL instead of relying on a moving latest release.",
        49.3,
        68.7,
    ),
    Caption(
        "Rocky rotates point-release files, so update the filename and SHA-256 checksum as a pair.",
        69.0,
        81.9,
    ),
    Caption(
        "Fill the pinned image values and select the host CPU model in the Packer template.",
        82.2,
        102.4,
    ),
    Caption(
        "These resolved values make the image source and checksum auditable before the build.",
        102.7,
        111.7,
    ),
    Caption(
        "Use the host CPU. An emulated model can fail Rocky's x86-64-v2 check and look like an SSH timeout.",
        112.0,
        119.8,
    ),
    Caption(
        "Packages go into the image once. Cloud-init cleanup stays last so clones do not inherit build state.",
        120.1,
        129.9,
    ),
    Caption(
        "This NoCloud seed gives Packer temporary SSH access while the guest is being built.",
        130.2,
        168.4,
    ),
    Caption(
        "Initialize the plugin, format the HCL, and validate it before starting the build.",
        168.7,
        189.3,
    ),
    Caption(
        "Packer starts from the pinned Rocky image and verifies its SHA-256 checksum.",
        193.0,
        201.4,
    ),
    Caption(
        "After KVM provisioning and cleanup, Packer converts the qcow2 and finishes successfully.",
        201.7,
        207.2,
    ),
    Caption(
        "The artifact is a healthy 10 GiB virtual disk with about 792 MiB allocated.",
        207.6,
        220.6,
    ),
    Caption(
        "That qcow2 is the handoff. Its path becomes an environment value for boxman.",
        220.9,
        242.7,
    ),
    Caption(
        "Now copy the boxman skeleton and inspect the values that still need filling.",
        246.4,
        259.8,
    ),
    Caption(
        "Set the project, image environment variable, and reusable template identity.",
        260.2,
        281.5,
    ),
    Caption(
        "Set the workspace and a private subnet for the demo environment.",
        281.9,
        299.1,
    ),
    Caption(
        "Give the template and cloned VM distinct hostnames so their roles stay clear.",
        299.5,
        315.0,
    ),
    Caption(
        "No packages are installed here; that work is already baked into the image.",
        315.4,
        329.1,
    ),
    Caption("With the values visible, bring the environment up.", 332.8, 342.7),
    Caption(
        "Boxman creates the template and clone, then verifies networking and SSH.",
        343.0,
        348.7,
    ),
    Caption(
        "boxman ps confirms that the cloned node is running.", 352.4, 358.1
    ),
    Caption(
        "One SSH command now checks the guest itself, using boxman's generated SSH config.",
        358.5,
        376.0,
    ),
    Caption(
        "The check covers the hostname, Rocky release, baked packages, guest agent, and cloud-init result.",
        376.2,
        395.0,
    ),
    Caption(
        "Rocky 9.8 is up with the baked packages and qemu guest agent active.",
        395.3,
        402.0,
    ),
    Caption(
        "Cloud-init finished cleanly from NoCloud, so the clone did not inherit stale build state.",
        402.2,
        409.0,
    ),
    Caption(
        "The clone kept boxman's template identity, not Packer's build-time hostname.",
        409.2,
        416.8,
    ),
]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="packer-v3-captions-") as temp_dir:
        drawtext = []
        for index, caption in enumerate(CAPTIONS):
            text_path = Path(temp_dir) / f"{index:02d}.txt"
            wrapped = "\n".join(textwrap.wrap(caption.text, width=92))
            text_path.write_text(wrapped, encoding="utf-8")
            drawtext.append(
                "drawtext="
                f"fontfile={FONT}:textfile={text_path}:"
                "fontcolor=white:fontsize=30:line_spacing=8:"
                "shadowcolor=black@0.85:shadowx=2:shadowy=2:"
                "x=(w-text_w)/2:"
                f"y={CAPTION_TOP}+({CAPTION_HEIGHT}-text_h)/2:"
                f"enable='between(t,{caption.start},{caption.end})'"
            )

        filters = (
            f"color=c=0x101318:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:r=12[canvas];"
            f"[0:v]scale={SCREEN_WIDTH}:{SCREEN_HEIGHT}:flags=lanczos[screen];"
            f"[canvas][screen]overlay={SCREEN_X}:0:shortest=1[base];"
            "[base]" + ",".join(drawtext) + "[outv]"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "warning",
                "-i",
                INPUT,
                "-filter_complex",
                filters,
                "-map",
                "[outv]",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-threads",
                "2",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "12",
                "-movflags",
                "+faststart",
                OUTPUT,
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
