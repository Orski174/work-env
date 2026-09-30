#!/usr/bin/env python3
"""Run the screen-demo-recording skill's open-ended fastgrab recorder."""

from pathlib import Path
import runpy


SKILL_RECORDER = Path("/admin/screen-demo-recording/scripts/fastgrab_record.py")
if not SKILL_RECORDER.is_file():
    raise SystemExit(f"missing screen-demo-recording helper: {SKILL_RECORDER}")
runpy.run_path(str(SKILL_RECORDER), run_name="__main__")
