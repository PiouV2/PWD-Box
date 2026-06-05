"""Battery unit tests."""

from pwdbox.battery import (
    BatteryMonitor,
    BatterySnapshot,
    estimate_battery_percentage,
    format_battery_status,
    format_current_ma,
)


class _FakeDriver:
    """Simple driver stub with fixed readings."""
    def __init__(self, voltage_v: float, current_ma: float) -> None:
        self._voltage_v = voltage_v
        self._current_ma = current_ma

    def getBusVoltage_V(self) -> float:
        return self._voltage_v

    def getCurrent_mA(self) -> float:
        return self._current_ma


class _BrokenDriver:
    """Driver stub that always fails."""
    def getBusVoltage_V(self) -> float:
        raise RuntimeError("sensor failed")

    def getCurrent_mA(self) -> float:
        raise RuntimeError("sensor failed")


def test_estimate_battery_percentage_clamps_and_scales() -> None:
    """Battery percentage clamps to expected range."""
    assert estimate_battery_percentage(8.5) == 0
    assert estimate_battery_percentage(9.0) == 0
    assert estimate_battery_percentage(10.8) == 50
    assert estimate_battery_percentage(12.6) == 100
    assert estimate_battery_percentage(13.0) == 100


def test_format_current_and_status() -> None:
    """Formatting helpers return expected strings."""
    snapshot = BatterySnapshot(
        available=True,
        percentage=75,
        current_ma=125.4,
        charging=True,
        voltage_v=11.7,
    )
    assert format_current_ma(125.4) == "+125.4 mA"
    assert format_battery_status(snapshot) == "Battery 75% | +125.4 mA | Charging"


def test_monitor_snapshot_uses_driver_readings() -> None:
    """Monitor uses driver values when available."""
    monitor = BatteryMonitor(driver=_FakeDriver(voltage_v=11.7, current_ma=-86.2))
    snapshot = monitor.read_snapshot()

    assert snapshot.available is True
    assert snapshot.percentage == 75
    assert snapshot.current_ma == -86.2
    assert snapshot.charging is False
    assert snapshot.tone == "warn"
    assert format_battery_status(snapshot) == "Battery 75% | -86.2 mA | Not charging"


def test_monitor_falls_back_when_driver_errors() -> None:
    """Monitor returns unavailable snapshot on driver errors."""
    monitor = BatteryMonitor(driver=_BrokenDriver())
    snapshot = monitor.read_snapshot()

    assert snapshot.available is False
    assert snapshot.message == "Battery unavailable"
    assert format_battery_status(snapshot) == "Battery unavailable"