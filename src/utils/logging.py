"""Logging helpers used by CLI and runtime."""

import logging
import time
from typing import Optional


def setup_logging(level: str) -> None:
    """Configure root logging with a standard format."""
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


class RateLimiter:
    """Simple per-key rate limiter using monotonic time."""

    def __init__(self, min_interval_seconds: float) -> None:
        """Initialize the minimum interval between events."""
        self.min_interval = max(min_interval_seconds, 0.0)
        self.last_time = {}

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        """Return True if enough time has passed for the key."""
        if self.min_interval <= 0:
            return True
        now = now if now is not None else time.monotonic()
        last = self.last_time.get(key)
        if last is None or now - last >= self.min_interval:
            self.last_time[key] = now
            return True
        return False
