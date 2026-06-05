"""CLI helper to enable monitor mode on an interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pwdbox.capture.wifi_sniffer import ensure_monitor_mode


def main() -> int:
    """Set monitor mode and return an exit code."""
    parser = argparse.ArgumentParser(
        description="Set a Wi-Fi interface to monitor mode for passive capture"
    )
    parser.add_argument(
        "--interface",
        default="wlan1",
        help="Wi-Fi interface name (default: wlan1)",
    )
    args = parser.parse_args()

    interface = (args.interface or "wlan1").strip() or "wlan1"
    ok = ensure_monitor_mode(interface, enable=True)
    if ok:
        print(f"{interface}: monitor mode ready")
        return 0

    print(
        f"{interface}: failed to enter monitor mode. "
        "Run with sudo or grant CAP_NET_ADMIN/CAP_NET_RAW."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
