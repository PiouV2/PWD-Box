"""Run the UI in demo mode for a quick smoke test."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui.app import run_ui


if __name__ == "__main__":
    raise SystemExit(run_ui(demo=True))
