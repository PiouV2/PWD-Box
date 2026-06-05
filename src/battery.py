"""Battery monitoring helpers and platform drivers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


EMPTY_BATTERY_VOLTAGE = 9.0
FULL_BATTERY_VOLTAGE = 12.6


@dataclass(frozen=True)
class BatterySnapshot:
    """Snapshot of battery availability and measurements."""
    available: bool
    percentage: Optional[int] = None
    voltage_v: Optional[float] = None
    current_ma: Optional[float] = None
    charging: Optional[bool] = None
    message: str = "Battery unavailable"

    @classmethod
    def unavailable(cls, message: str = "Battery unavailable") -> "BatterySnapshot":
        """Return a snapshot with no battery data."""
        return cls(available=False, message=message)

    @property
    def tone(self) -> str:
        """Return a short UI tone based on status."""
        if not self.available:
            return "neutral"
        return "ok" if self.charging else "warn"


def estimate_battery_percentage(voltage_v: float) -> int:
    """Estimate battery percentage from voltage."""
    if voltage_v <= EMPTY_BATTERY_VOLTAGE:
        return 0
    if voltage_v >= FULL_BATTERY_VOLTAGE:
        return 100
    span = FULL_BATTERY_VOLTAGE - EMPTY_BATTERY_VOLTAGE
    return int(round(((voltage_v - EMPTY_BATTERY_VOLTAGE) / span) * 100.0))


def format_current_ma(current_ma: float) -> str:
    """Format current in milliamps with sign."""
    return f"{current_ma:+.1f} mA"


def format_battery_status(snapshot: BatterySnapshot) -> str:
    """Return a user-friendly battery summary string."""
    if not snapshot.available:
        return snapshot.message

    percentage = snapshot.percentage if snapshot.percentage is not None else 0
    current_ma = snapshot.current_ma if snapshot.current_ma is not None else 0.0
    charging_text = "Charging" if snapshot.charging else "Not charging"
    return f"Battery {percentage}% | {format_current_ma(current_ma)} | {charging_text}"


class _DemoDriver:
    """Hardcoded driver used for demo output."""
    def getBusVoltage_V(self) -> float:
        return 11.7

    def getCurrent_mA(self) -> float:
        return -86.2


class _SysfsDriver:
    """Read voltage and current from Linux sysfs."""

    def __init__(self, base_path: str) -> None:
        """Store the sysfs base path."""
        self.base = Path(base_path)

    def _read_text(self, name: str) -> Optional[str]:
        """Read a text value from sysfs."""
        try:
            return (self.base / name).read_text().strip()
        except Exception:
            return None

    def _read_int_loose(self, name: str) -> Optional[int]:
        """Read an int, with a loose regex fallback."""
        txt = self._read_text(name)
        if not txt:
            return None
        try:
            return int(txt)
        except ValueError:
            import re

            match = re.search(r"(-?\d+)", txt)
            if not match:
                return None
            try:
                return int(match.group(1))
            except Exception:
                return None

    def _read_uevent_value(self, key: str) -> Optional[int]:
        """Read a value from the uevent file."""
        txt = self._read_text("uevent")
        if not txt:
            return None
        for line in txt.splitlines():
            if line.startswith(key + "="):
                try:
                    return int(line.split("=", 1)[1])
                except Exception:
                    return None
        return None

    def getBusVoltage_V(self) -> Optional[float]:
        """Return bus voltage in volts if available."""
        raw = self._read_int_loose("voltage_now")
        if raw is None:
            raw = self._read_int_loose("voltage")
        if raw is None:
            raw = self._read_uevent_value("POWER_SUPPLY_VOLTAGE_NOW")
        if raw is None:
            return None
        if abs(raw) >= 1_000_000:
            return float(raw) / 1_000_000.0
        if abs(raw) >= 1000:
            return float(raw) / 1000.0
        return float(raw)

    def getCurrent_mA(self) -> Optional[float]:
        """Return current in milliamps if available."""
        raw = self._read_int_loose("current_now")
        if raw is None:
            raw = self._read_int_loose("current")
        if raw is None:
            raw = self._read_uevent_value("POWER_SUPPLY_CURRENT_NOW")
        if raw is None:
            power = self._read_int_loose("power_now") or self._read_uevent_value("POWER_SUPPLY_POWER_NOW")
            voltage_v = self.getBusVoltage_V()
            if power is None or not voltage_v:
                return None
            power_w = float(power) / 1_000_000.0 if abs(power) >= 1_000_000 else float(power) / 1000.0
            current_a = power_w / voltage_v if voltage_v != 0 else None
            return current_a * 1000.0 if current_a is not None else None
        if abs(raw) >= 1000:
            return float(raw) / 1000.0
        return float(raw)


def _find_sysfs_battery() -> Optional[str]:
    """Locate a sysfs power supply that looks like a battery."""
    base = Path("/sys/class/power_supply")
    if not base.exists():
        return None
    for dev in base.iterdir():
        tfile = dev / "type"
        try:
            battery_type = tfile.read_text().strip().lower()
        except Exception:
            battery_type = ""
        if "battery" in battery_type:
            return str(dev)
    for dev in base.iterdir():
        for name in ("voltage_now", "current_now", "power_now", "voltage"):
            if (dev / name).exists():
                return str(dev)
    return None


class BatteryMonitor:
    """Select a driver and return battery snapshots."""

    def __init__(self, driver: Optional[object] = None) -> None:
        """Create a monitor with an optional driver override."""
        self._driver = driver

    def _get_driver(self) -> Optional[object]:
        """Choose a driver based on env vars and sysfs."""
        if self._driver is not None:
            return self._driver
        if os.environ.get("PWDBOX_BATTERY_DEMO") == "1":
            self._driver = _DemoDriver()
            return self._driver
        sysfs_path = _find_sysfs_battery()
        if sysfs_path:
            self._driver = _SysfsDriver(sysfs_path)
            return self._driver
        return None

    def read_snapshot(self) -> BatterySnapshot:
        """Read voltage/current and return a snapshot."""
        driver = self._get_driver()
        if driver is None:
            return BatterySnapshot.unavailable()

        try:
            voltage_v = float(driver.getBusVoltage_V())
            current_ma = float(driver.getCurrent_mA())
        except Exception:
            return BatterySnapshot.unavailable()

        return BatterySnapshot(
            available=True,
            percentage=estimate_battery_percentage(voltage_v),
            voltage_v=voltage_v,
            current_ma=current_ma,
            charging=current_ma > 0,
        )
