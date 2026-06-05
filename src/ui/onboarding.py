"""Simple onboarding helpers for first run."""

from __future__ import annotations


def should_show_setup(demo: bool, setup_complete: bool) -> bool:
    """Return True when the setup screen should be shown."""
    if demo:
        return False
    return not setup_complete
