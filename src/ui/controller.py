"""Background thread controller for capture sessions."""

from __future__ import annotations

import queue
import threading
from typing import Optional

from ..orchestration.session_manager import SessionManager
from ..config import Config


class MonitorController:
    """Run SessionManager in a background thread for the UI."""

    def __init__(self, config: Config, event_queue: queue.Queue) -> None:
        """Prepare a controller with config and event queue."""
        self.config = config
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None
        self.session: Optional[SessionManager] = None
        self._lock = threading.Lock()

    def start(self, interface: Optional[str] = None) -> bool:
        """Start a new background capture thread."""
        with self._lock:
            if self.thread and self.thread.is_alive():
                return False
            self.session = SessionManager(self.config, event_queue=self.event_queue)
            self.thread = threading.Thread(
                target=self._run,
                args=(interface,),
                daemon=True,
            )
            self.thread.start()
            return True

    def _run(self, interface: Optional[str]) -> None:
        """Thread entry point for the session run loop."""
        with self._lock:
            session = self.session
            thread = self.thread
        if session is None:
            return
        exit_code = session.run(
            interface=interface,
            install_signal_handlers=False,
            render_console=False,
        )
        self.event_queue.put({"type": "stopped", "data": {"code": exit_code}})
        with self._lock:
            if self.thread is thread:
                self.thread = None
                self.session = None

    def stop(self) -> bool:
        """Stop the running capture thread."""
        with self._lock:
            session = self.session
            thread = self.thread
        if session is None and (thread is None or not thread.is_alive()):
            return False
        if session:
            session.stop()
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            if self.thread is thread and (thread is None or not thread.is_alive()):
                self.thread = None
                self.session = None
        return True

    def is_running(self) -> bool:
        """Return True if the capture thread is active."""
        with self._lock:
            return bool(self.thread and self.thread.is_alive())
