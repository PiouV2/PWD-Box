from pwdbox.ui.onboarding import should_show_setup


def test_should_show_setup_when_not_complete() -> None:
    assert should_show_setup(demo=False, setup_complete=False) is True


def test_should_not_show_setup_when_demo() -> None:
    assert should_show_setup(demo=True, setup_complete=False) is False


def test_should_not_show_setup_when_complete() -> None:
    assert should_show_setup(demo=False, setup_complete=True) is False
