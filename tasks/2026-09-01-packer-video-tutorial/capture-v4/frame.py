#!/usr/bin/env python3
"""Save a correctly ordered RGB review frame from fastgrab's BGRA buffer."""
import sys
from fastgrab import screenshot
from PIL import Image

frame = screenshot.Screenshot(backend='x11').capture()
Image.fromarray(frame[:, :, [2, 1, 0, 3]]).convert('RGB').save(sys.argv[1])
