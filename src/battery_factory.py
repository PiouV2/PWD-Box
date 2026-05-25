from __future__ import annotations

import os
import platform

from .battery import BatteryMonitor


class _DemoBatteryDriver:
    def getBusVoltage_V(self) -> float:
        return 11.7

    def getCurrent_mA(self) -> float:
        return -86.2


def _should_try_ina219() -> bool:
    configured = os.environ.get("PWDBOX_BATTERY_USE_INA219")
    if configured is not None:
        return configured == "1"
    return platform.system() == "Linux"


def build_battery_monitor(demo: bool = False) -> BatteryMonitor:
    if demo or os.environ.get("PWDBOX_BATTERY_DEMO") == "1":
        return BatteryMonitor(driver=_DemoBatteryDriver())

    if not _should_try_ina219():
        return BatteryMonitor()

    try:
        from .INA219 import INA219

        i2c_bus = int(os.environ.get("PWDBOX_BATTERY_I2C_BUS", "1"))
        address = int(os.environ.get("PWDBOX_BATTERY_I2C_ADDR", "0x41"), 0)
        driver = INA219(i2c_bus=i2c_bus, addr=address)
        return BatteryMonitor(driver=driver)
    except Exception:
        return BatteryMonitor()