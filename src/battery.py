from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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


class BatteryMonitor:
    def __init__(self, i2c_bus: int = 1, address: int = 0x41, driver: Optional[object] = None) -> None:
        self.i2c_bus = i2c_bus
        self.address = address
        self._driver = driver

    def _create_driver(self):
        from .INA219 import INA219

        return INA219(i2c_bus=self.i2c_bus, addr=self.address)

    def _get_driver(self):
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    def read_snapshot(self) -> BatterySnapshot:
        try:
            driver = self._get_driver()
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
