"""Detect deauthentication floods within a time window."""

from __future__ import annotations

from collections import deque
import time
from typing import Deque, Dict, Optional

from ..models import AlertEvent, DeauthEvent


class DeauthDetector:
    """Maintain a rolling window of deauth events per key."""

    def __init__(
        self,
        threshold: int,
        window_seconds: float,
        cooldown_seconds: float,
    ) -> None:
        """Initialize limits and internal buckets."""
        self.threshold = max(threshold, 1)
        self.window_seconds = max(window_seconds, 0.1)
        self.cooldown_seconds = max(cooldown_seconds, 0.0)
        self._events: Dict[str, Deque[float]] = {}
        self._last_alert: Dict[str, float] = {}

    def _key(self, event: DeauthEvent) -> str:
        """Build a stable key from BSSID and source address."""
        bssid = event.bssid or "unknown"
        src = event.src or "unknown"
        return f"{bssid}|{src}"

    def process(
        self, event: DeauthEvent, now: Optional[float] = None
    ) -> Optional[AlertEvent]:
        """Ingest a deauth event and emit an alert if triggered."""
        ts = (
            event.monotonic_ts
            if event.monotonic_ts is not None
            else (now if now is not None else time.monotonic())
        )
        key = self._key(event)
        bucket = self._events.setdefault(key, deque())

        while bucket and ts - bucket[0] > self.window_seconds:
            bucket.popleft()
        bucket.append(ts)

        if len(bucket) < self.threshold:
            return None

        last_alert_ts = self._last_alert.get(key)
        if last_alert_ts is not None and ts - last_alert_ts < self.cooldown_seconds:
            return None

        self._last_alert[key] = ts
        return AlertEvent(
            timestamp=event.timestamp,
            monotonic_ts=ts,
            alert_type="deauth_flood",
            key=key,
            count=len(bucket),
            window_seconds=self.window_seconds,
        )
