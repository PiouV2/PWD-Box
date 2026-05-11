from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FrameEvent:
    timestamp: float
    monotonic_ts: float
    frame_type: int
    frame_subtype: int
    src: Optional[str]
    dst: Optional[str]
    bssid: Optional[str]
    ssid: Optional[str]
    rssi: Optional[int]
    raw_len: Optional[int]


@dataclass
class DeauthEvent(FrameEvent):
    reason_code: Optional[int] = None


@dataclass
class NetworkInfo:
    bssid: str
    ssid: Optional[str]
    last_seen: float
    rssi: Optional[int]


@dataclass
class AlertEvent:
    timestamp: float
    monotonic_ts: float
    alert_type: str
    key: str
    count: int
    window_seconds: float
