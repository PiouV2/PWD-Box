"""Deauth detector tests."""

from pwdbox.detection.deauth_detector import DeauthDetector
from pwdbox.models import DeauthEvent


def _event(ts: float) -> DeauthEvent:
    """Create a deauth event with a fixed key."""
    return DeauthEvent(
        timestamp=ts,
        monotonic_ts=ts,
        frame_type=0,
        frame_subtype=12,
        src="11:22:33:44:55:66",
        dst="ff:ff:ff:ff:ff:ff",
        bssid="11:22:33:44:55:66",
        ssid=None,
        rssi=None,
        raw_len=None,
        reason_code=7,
    )


def test_threshold_triggers_alert() -> None:
    """Alert triggers once threshold is reached."""
    detector = DeauthDetector(threshold=3, window_seconds=5, cooldown_seconds=10)
    assert detector.process(_event(1)) is None
    assert detector.process(_event(2)) is None
    alert = detector.process(_event(3))
    assert alert is not None
    assert alert.count == 3


def test_cooldown_blocks_repeats() -> None:
    """Cooldown prevents alerts from firing too frequently."""
    detector = DeauthDetector(threshold=3, window_seconds=5, cooldown_seconds=10)
    detector.process(_event(1))
    detector.process(_event(2))
    detector.process(_event(3))
    assert detector.process(_event(4)) is None

    detector.process(_event(14))
    detector.process(_event(15))
    alert = detector.process(_event(16))
    assert alert is not None
