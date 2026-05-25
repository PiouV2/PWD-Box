from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


EMPTY_BATTERY_VOLTAGE = 9.0
FULL_BATTERY_VOLTAGE = 12.6


@dataclass(frozen=True)
class BatterySnapshot:
    available: bool
    percentage: Optional[int] = None
    voltage_v: Optional[float] = None
    current_ma: Optional[float] = None
    charging: Optional[bool] = None
    message: str = "Battery unavailable"

    @classmethod
    def unavailable(cls, message: str = "Battery unavailable") -> "BatterySnapshot":
        return cls(available=False, message=message)

    @property
    def tone(self) -> str:
        if not self.available:
            return "neutral"
        return "ok" if self.charging else "warn"


def estimate_battery_percentage(voltage_v: float) -> int:
    if voltage_v <= EMPTY_BATTERY_VOLTAGE:
        return 0
    if voltage_v >= FULL_BATTERY_VOLTAGE:
        return 100
    span = FULL_BATTERY_VOLTAGE - EMPTY_BATTERY_VOLTAGE
    return int(round(((voltage_v - EMPTY_BATTERY_VOLTAGE) / span) * 100.0))


def format_current_ma(current_ma: float) -> str:
    return f"{current_ma:+.1f} mA"


def format_battery_status(snapshot: BatterySnapshot) -> str:
    if not snapshot.available:
        return snapshot.message

    percentage = snapshot.percentage if snapshot.percentage is not None else 0
    current_ma = snapshot.current_ma if snapshot.current_ma is not None else 0.0
    charging_text = "Charging" if snapshot.charging else "Not charging"
    return f"Battery {percentage}% | {format_current_ma(current_ma)} | {charging_text}"


class _DemoDriver:
    """Return stable demo readings for non-hardware environments."""

    def getBusVoltage_V(self) -> float:
        return 11.7

    def getCurrent_mA(self) -> float:
        return -86.2


class _SysfsDriver:
    """Read battery attributes from /sys/class/power_supply/<device>/.

    This is a generic, best-effort reader and returns None when values
    are not present or cannot be parsed.
    """

    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path)

    def _read_int(self, name: str) -> Optional[int]:
        p = self.base / name
        try:
            txt = p.read_text().strip()
            return int(txt)
        except Exception:
            return None

    def getBusVoltage_V(self) -> Optional[float]:
        v = self._read_int("voltage_now") or self._read_int("voltage")
        if v is None:
            return None
        # voltage_now is typically in microvolts
        return float(v) / 1_000_000.0

    def getCurrent_mA(self) -> Optional[float]:
        cur = self._read_int("current_now")
        if cur is not None:
            # current_now often in microamps
            return float(cur) / 1000.0
        # fallback: derive from power_now (microwatts) / voltage
        power = self._read_int("power_now")
        v = self.getBusVoltage_V()
        if power is not None and v:
            power_w = float(power) / 1_000_000.0
            current_a = power_w / v if v != 0 else None
            return current_a * 1000.0 if current_a is not None else None
        return None


def _find_sysfs_battery() -> Optional[str]:
    base = Path("/sys/class/power_supply")
    if not base.exists():
        return None
    # Prefer devices whose 'type' file contains 'Battery'
    for dev in base.iterdir():
        tfile = dev / "type"
        try:
            t = tfile.read_text().strip().lower()
        except Exception:
            t = ""
        if "battery" in t:
            return str(dev)
    # fallback: any device exposing common battery attributes
    for dev in base.iterdir():
        for fn in ("voltage_now", "current_now", "power_now", "voltage"):
            if (dev / fn).exists():
                return str(dev)
    return None


class BatteryMonitor:
    """High-level monitor that picks a provider:
    - demo mode when PWDBOX_BATTERY_DEMO=1
    - sysfs when available
    - returns unavailable otherwise
    """

    def __init__(self, driver: Optional[object] = None) -> None:
        self._driver = driver

    def _get_driver(self) -> Optional[object]:
        if self._driver is not None:
            return self._driver
        if os.environ.get("PWDBOX_BATTERY_DEMO") == "1":
            self._driver = _DemoDriver()
            return self._driver
        path = _find_sysfs_battery()
        if path:
            self._driver = _SysfsDriver(path)
            return self._driver
        return None

    def read_snapshot(self) -> BatterySnapshot:
        driver = self._get_driver()
        if driver is None:
            return BatterySnapshot.unavailable()
        try:
            voltage = driver.getBusVoltage_V()
            current = driver.getCurrent_mA()
        except Exception:
            return BatterySnapshot.unavailable()
        if voltage is None:
            return BatterySnapshot.unavailable()
        percentage = estimate_battery_percentage(voltage)
        charging = bool(current and current > 0)
        return BatterySnapshot(
            available=True,
            percentage=percentage,
            voltage_v=voltage,
            current_ma=current,
            charging=charging,
        )
