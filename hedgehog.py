#!/usr/bin/env python3
"""Hedgehog Master command-line entry point."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent / "skills" / "hedgehog-master" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from research_harness import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
