#!/usr/bin/env python3
"""Extract one final-render frame from the middle of every typed command."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


RAW = "/admin/packer-tutorial-v3-raw.mp4"
FINAL = "/admin/packer-tutorial-v3-final.mp4"
ACTION_LOG = Path("/admin/packer-v3-action.log")
SCENE_LOG = Path("/admin/packer-v3-scenes.jsonl")
TRIM_SCRIPT = Path("/admin/screen-demo-recording/scripts/trim_recording.py")
OUTPUT_DIR = Path("/admin/packer-v3-command-checks")
HOLDS_AFTER = {20: 4.0, 33: 4.0}


def load_trim_module():
    spec = importlib.util.spec_from_file_location("screen_demo_trim", TRIM_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {TRIM_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def type_intervals(recording_start: float) -> list[tuple[float, float]]:
    intervals = []
    pending = None
    for line in ACTION_LOG.read_text(encoding="utf-8").splitlines():
        fields = line.split(" ", 2)
        if len(fields) < 2:
            continue
        timestamp, kind = float(fields[0]), fields[1]
        if kind == "type_start":
            pending = timestamp - recording_start
        elif kind == "type_end" and pending is not None:
            intervals.append((pending, timestamp - recording_start))
            pending = None
    return intervals


def typing_labels() -> list[str]:
    labels = []
    for line in SCENE_LOG.read_text(encoding="utf-8").splitlines():
        label = json.loads(line)["label"]
        if label.endswith("_typing"):
            labels.append(label.removesuffix("_typing"))
    return labels


def cut_time(raw_time: float, kept: list[tuple[float, float]]) -> float:
    elapsed = 0.0
    for index, (start, end) in enumerate(kept):
        if start <= raw_time <= end:
            return elapsed + raw_time - start
        elapsed += end - start + HOLDS_AFTER.get(index, 0.0)
    raise ValueError(f"raw time {raw_time:.3f} is outside all kept segments")


def make_sheets(paths: list[Path]) -> None:
    tile_width, tile_height = 480, 270
    for sheet_index in range((len(paths) + 11) // 12):
        sheet = Image.new("RGB", (tile_width * 4, tile_height * 3), "black")
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(paths[sheet_index * 12 : (sheet_index + 1) * 12]):
            image = Image.open(path).convert("RGB").resize((tile_width, tile_height))
            x = (offset % 4) * tile_width
            y = (offset // 4) * tile_height
            sheet.paste(image, (x, y))
            label_top = y + tile_height - 20
            draw.rectangle(
                (x, label_top, x + tile_width, y + tile_height), fill="black"
            )
            draw.text((x + 5, label_top + 4), path.stem, fill="white")
        sheet.save(OUTPUT_DIR / f"command-check-sheet-{sheet_index + 1}.png")


def main() -> None:
    trim = load_trim_module()
    recording_start, actions = trim.load_actions(ACTION_LOG)
    duration = trim.probe_duration(RAW)
    kept = trim.build_kept(
        actions,
        trim.active_segments(RAW, duration),
        duration,
        2.0,
        20.0,
        [],
        [],
    )
    intervals = type_intervals(recording_start)
    labels = typing_labels()
    if len(intervals) != len(labels):
        raise RuntimeError(
            f"typing interval/label mismatch: {len(intervals)} != {len(labels)}"
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    frames = []
    for index, ((start, end), label) in enumerate(zip(intervals, labels), start=1):
        timestamp = cut_time((start + end) / 2, kept)
        target = OUTPUT_DIR / f"{index:02d}-{label}.png"
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                FINAL,
                "-frames:v",
                "1",
                str(target),
            ],
            check=True,
        )
        print(f"{index:02d} {label} {timestamp:.3f} {target}")
        frames.append(target)
    make_sheets(frames)


if __name__ == "__main__":
    main()
