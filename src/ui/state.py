from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AppState:
    status: Dict[str, Any] = field(default_factory=dict)
    networks: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_error: Optional[str] = None
    last_alert_time: Optional[str] = None
    session_alert_count: int = 0
    running: bool = False
