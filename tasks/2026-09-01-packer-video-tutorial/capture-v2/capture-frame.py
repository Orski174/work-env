#!/usr/bin/env python3
"""Save one screenshot from the active X display for human review."""

from pathlib import Path
import sys

from fastgrab import screenshot
from PIL import Image


target = Path(sys.argv[1])
frame = screenshot.Screenshot(backend="x11").capture()
Image.fromarray(frame).convert("RGB").save(target)
