from __future__ import annotations

import subprocess
from typing import Callable, Optional

from scapy.all import sniff
from scapy.layers.dot11 import Dot11


def _run_cmd(command: list[str]) -> bool:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_monitor_mode(interface: str) -> bool:
    try:
        result = subprocess.run(
            ["iw", "dev", interface, "info"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return False

    if result.returncode != 0:
        return False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("type ") and "monitor" in line:
            return True
    return False


def enable_monitor_mode(interface: str) -> bool:
    if not _run_cmd(["ip", "link", "set", interface, "down"]):
        return False
    if not _run_cmd(["iw", "dev", interface, "set", "type", "monitor"]):
        return False
    if not _run_cmd(["ip", "link", "set", interface, "up"]):
        return False
    return True


def ensure_monitor_mode(interface: str, enable: bool = True) -> bool:
    if check_monitor_mode(interface):
        return True
    if not enable:
        return False
    if not enable_monitor_mode(interface):
        return False
    return check_monitor_mode(interface)


def set_channel(interface: str, channel: int) -> bool:
    if channel <= 0:
        return False
    return _run_cmd(["iw", "dev", interface, "set", "channel", str(channel)])


def capture_test(
    interface: str,
    seconds: float = 3.0,
    management_only: bool = True,
) -> bool:
    count = 0

    def _count(pkt) -> None:
        nonlocal count
        count += 1

    def _filter(pkt) -> bool:
        if not pkt.haslayer(Dot11):
            return False
        if management_only:
            return pkt[Dot11].type == 0
        return True

    sniff(
        iface=interface,
        prn=_count,
        store=False,
        timeout=seconds,
        lfilter=_filter,
    )
    return count > 0


def sniff_loop(
    interface: str,
    on_packet: Callable,
    stop_event,
    management_only: bool = True,
    tick_interval: float = 1.0,
    on_tick: Optional[Callable] = None,
) -> None:
    def _filter(pkt) -> bool:
        if not pkt.haslayer(Dot11):
            return False
        if management_only:
            return pkt[Dot11].type == 0
        return True

    while not stop_event.is_set():
        sniff(
            iface=interface,
            prn=on_packet,
            store=False,
            timeout=tick_interval,
            lfilter=_filter,
        )
        if on_tick:
            on_tick()
