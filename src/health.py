from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple

from .config import Config
from .battery import BatteryMonitor


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str
    fix: Optional[str] = None


def _run_cmd(command: List[str]) -> Tuple[str, str, int]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as exc:
        return "", str(exc), 1


def _parse_iw_interfaces(output: str) -> List[str]:
    interfaces: List[str] = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Interface "):
            parts = line.split()
            if len(parts) >= 2:
                interfaces.append(parts[1])
    return interfaces


def list_wireless_interfaces() -> List[str]:
    out, _, code = _run_cmd(["iw", "dev"])
    if code == 0:
        return _parse_iw_interfaces(out)
    return []


def list_all_interfaces() -> List[str]:
    out, _, code = _run_cmd(["ip", "-o", "link", "show"])
    interfaces: List[str] = []
    if code != 0:
        return interfaces
    for line in out.splitlines():
        parts = line.split(":", 2)
        if len(parts) >= 2:
            name = parts[1].strip()
            if name:
                interfaces.append(name)
    return interfaces


def _check_python_version(min_major: int = 3, min_minor: int = 9) -> CheckResult:
    version = sys.version_info
    ok = (version.major, version.minor) >= (min_major, min_minor)
    details = f"{version.major}.{version.minor}.{version.micro}"
    fix = None if ok else "Install Python 3.9+ and run with that interpreter."
    return CheckResult("Python version", ok, details, fix)


def _check_os() -> CheckResult:
    details = f"{platform.system()} {platform.release()}"
    return CheckResult("Operating system", True, details)


def _check_tools(tools: List[str]) -> List[CheckResult]:
    results: List[CheckResult] = []
    for tool in tools:
        found = shutil.which(tool) is not None
        details = "found" if found else "missing"
        fix = None if found else f"Install '{tool}' (sudo apt install {tool})."
        results.append(CheckResult(f"Tool: {tool}", found, details, fix))
    return results


def _check_packages() -> List[CheckResult]:
    results: List[CheckResult] = []
    try:
        import scapy  # noqa: F401

        results.append(CheckResult("Package: scapy", True, "import ok"))
    except Exception:
        results.append(
            CheckResult(
                "Package: scapy",
                False,
                "import failed",
                "Install scapy: pip install scapy",
            )
        )
    try:
        import yaml  # noqa: F401

        results.append(CheckResult("Package: PyYAML", True, "import ok"))
    except Exception:
        results.append(
            CheckResult(
                "Package: PyYAML",
                False,
                "import failed",
                "Install PyYAML: pip install pyyaml",
            )
        )
    return results


def _check_permissions() -> CheckResult:
    ok = os.geteuid() == 0
    details = "root" if ok else "not root"
    fix = None
    if not ok:
        fix = "Run with sudo or grant CAP_NET_ADMIN and CAP_NET_RAW."
    return CheckResult("Capture permissions", ok, details, fix)


def _check_interfaces(config: Optional[Config], interface: Optional[str]) -> List[CheckResult]:
    results: List[CheckResult] = []
    wireless = list_wireless_interfaces()
    all_ifaces = list_all_interfaces()
    results.append(
        CheckResult(
            "Interfaces found",
            bool(all_ifaces),
            ", ".join(all_ifaces) if all_ifaces else "none",
            "Check adapter connection and drivers.",
        )
    )

    target_iface = interface or (config.capture.interface if config else None)
    if target_iface:
        ok = target_iface in wireless
        details = (
            f"{target_iface} present" if ok else f"{target_iface} not found"
        )
        fix = (
            None
            if ok
            else "Use the correct interface name from 'iw dev'."
        )
        results.append(CheckResult("Wi-Fi adapter", ok, details, fix))
    else:
        ok = bool(wireless)
        details = ", ".join(wireless) if wireless else "none"
        fix = None if ok else "Ensure the Wi-Fi adapter is plugged in."
        results.append(CheckResult("Wi-Fi adapters", ok, details, fix))
    return results


def run_health_check(
    config: Optional[Config] = None, interface: Optional[str] = None
) -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(_check_os())
    results.append(_check_python_version())
    results.extend(_check_tools(["iw", "ip"]))
    results.extend(_check_packages())
    results.extend(_check_interfaces(config, interface))
    results.append(_check_permissions())
    # Battery check: use INA219 (or demo driver) to sample battery voltage/current
    try:
        monitor = BatteryMonitor()
        snap = monitor.read_snapshot()
        if not snap.available:
            results.append(CheckResult("Battery", False, snap.message, "Connect INA219 or set PWDBOX_BATTERY_DEMO=1 for demo output."))
        else:
            details = f"{snap.percentage}% (V={snap.voltage_v:.2f} V, I={snap.current_ma:+.1f} mA)"
            # Consider battery ok if above 10% or currently charging
            ok = (snap.percentage is not None and snap.percentage >= 10) or bool(snap.charging)
            fix = None if ok else "Charge battery or check power supply."
            results.append(CheckResult("Battery", ok, details, fix))
    except Exception as exc:
        results.append(CheckResult("Battery", False, f"error: {exc}", "Connect INA219 or set PWDBOX_BATTERY_DEMO=1 for demo output."))
    return results


def format_results(results: List[CheckResult]) -> str:
    lines: List[str] = []
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"[{status}] {result.name}: {result.details}")
        if not result.ok and result.fix:
            lines.append(f"  Fix: {result.fix}")
    return "\n".join(lines)
