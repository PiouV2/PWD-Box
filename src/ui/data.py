from __future__ import annotations

import random
import time
from typing import Dict, List


def demo_networks() -> List[Dict[str, object]]:
    now = time.time()
    base = [
        {"ssid": "CafeNet", "bssid": "aa:bb:cc:dd:ee:01", "rssi": -42, "age_seconds": 2},
        {"ssid": "PWD-Box", "bssid": "aa:bb:cc:dd:ee:02", "rssi": -55, "age_seconds": 5},
        {"ssid": "Office", "bssid": "aa:bb:cc:dd:ee:03", "rssi": -63, "age_seconds": 8},
        {"ssid": "Guest", "bssid": "aa:bb:cc:dd:ee:04", "rssi": -70, "age_seconds": 12},
    ]
    jitter = []
    for row in base:
        jitter.append(
            {
                **row,
                "rssi": row["rssi"] + random.randint(-3, 3),
                "age_seconds": int(now) % 10,
            }
        )
    return jitter


def demo_alerts() -> List[Dict[str, object]]:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return [
        {
            "timestamp": ts,
            "alert_type": "deauth_flood",
            "key": "aa:bb:cc:dd:ee:ff|11:22:33:44:55:66",
            "count": 36,
            "pcap_path": "data/pcaps/pwd_demo.pcap",
        }
    ]
