from __future__ import annotations


def should_show_setup(demo: bool, setup_complete: bool) -> bool:
    if demo:
        return False
    return not setup_complete
