"""Thin wrappers around scapy sniffing for monitor mode."""

from __future__ import annotations

import subprocess
from typing import Callable, Optional

from scapy.all import sniff
from scapy.layers.dot11 import Dot11


def check_monitor_mode(interface: str) -> bool:
    """Return True if the interface is in monitor mode."""
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




def capture_test(
    interface: str,
    seconds: float = 3.0,
    management_only: bool = True,
) -> bool:
    """Capture a short sample to confirm packets are visible."""
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
    """Run a stop-aware sniff loop with an optional tick hook."""
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
