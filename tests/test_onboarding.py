"""Onboarding helper tests."""

from pwdbox.ui.onboarding import should_show_setup


def test_should_show_setup_when_not_complete() -> None:
    """Setup shows when not complete and not demo."""
    assert should_show_setup(demo=False, setup_complete=False) is True


def test_should_not_show_setup_when_demo() -> None:
    """Setup hides in demo mode."""
    assert should_show_setup(demo=True, setup_complete=False) is False


def test_should_not_show_setup_when_complete() -> None:
    """Setup hides when completed."""
    assert should_show_setup(demo=False, setup_complete=True) is False
