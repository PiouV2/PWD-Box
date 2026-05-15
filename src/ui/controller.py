from __future__ import annotations

import queue
import threading
from typing import Optional

from ..orchestration.session_manager import SessionManager
from ..config import Config


class MonitorController:
    def __init__(self, config: Config, event_queue: queue.Queue, network_filter_mode: str = "weak") -> None:
        self.config = config
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None
        self.session: Optional[SessionManager] = None
        self.network_filter_mode = network_filter_mode if network_filter_mode in {"weak", "strong", "all"} else "weak"
        self._lock = threading.Lock()

    def start(self, interface: Optional[str] = None, network_filter_mode: Optional[str] = None) -> None:
        with self._lock:
            if self.thread and self.thread.is_alive():
                return
            if network_filter_mode in {"weak", "strong", "all"}:
                self.network_filter_mode = network_filter_mode
            self.session = SessionManager(
                self.config,
                event_queue=self.event_queue,
                network_filter_mode=self.network_filter_mode,
            )
            self.thread = threading.Thread(
                target=self._run,
                args=(interface,),
                daemon=True,
            )
            self.thread.start()

    def set_network_filter_mode(self, mode: str) -> None:
        if mode not in {"weak", "strong", "all"}:
            mode = "weak"
        with self._lock:
            self.network_filter_mode = mode
            if self.session:
                self.session.set_network_filter_mode(mode)

    def _run(self, interface: Optional[str]) -> None:
        if self.session is None:
            return
        exit_code = self.session.run(
            interface=interface,
            install_signal_handlers=False,
            render_console=False,
        )
        self.event_queue.put({"type": "stopped", "data": {"code": exit_code}})

    def stop(self) -> None:
        with self._lock:
            if self.session:
                self.session.stop()
            if self.thread:
                self.thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())
