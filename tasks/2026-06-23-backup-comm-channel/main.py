#!/usr/bin/env python3
"""Entry point for this task."""
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
INPUT = TASK_DIR / "input"
OUTPUT = TASK_DIR / "output"


def main() -> None:
    print(f"task dir: {TASK_DIR}")


if __name__ == "__main__":
    main()
