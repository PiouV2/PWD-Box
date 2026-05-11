from __future__ import annotations

from collections import deque
import logging
import signal
import threading
import time
from typing import Dict, Optional

from ..capture.packet_parser import parse_packet
from ..capture.wifi_sniffer import capture_test, ensure_monitor_mode, sniff_loop
from ..config import Config
from ..detection.deauth_detector import DeauthDetector
from ..models import DeauthEvent, FrameEvent, NetworkInfo
from ..utils.logging import RateLimiter


class SessionManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.ap_table: Dict[str, NetworkInfo] = {}
        self.alerts = deque(maxlen=5)
        self.deauth_seen = 0
        self.stop_event = threading.Event()
        self.detector = DeauthDetector(
            threshold=config.deauth.threshold,
            window_seconds=config.deauth.window_seconds,
            cooldown_seconds=config.deauth.cooldown_seconds,
        )
        self.deauth_limiter = RateLimiter(config.logging.rate_limit_seconds)
        self.render_limiter = RateLimiter(config.scanner.render_interval_seconds)

    def run(self, interface: Optional[str] = None) -> int:
        iface = interface or self.config.capture.interface
        if not iface:
            logging.error("No capture interface specified.")
            return 1

        if not ensure_monitor_mode(iface, self.config.capture.enable_monitor):
            logging.error("Monitor mode could not be enabled on %s.", iface)
            return 2

        if not capture_test(
            iface,
            self.config.capture.test_seconds,
            self.config.capture.management_only,
        ):
            logging.error(
                "Capture test failed: no 802.11 management frames seen on %s.",
                iface,
            )
            return 3

        self._install_signal_handlers()
        logging.info("Starting passive capture on %s.", iface)

        sniff_loop(
            iface,
            self._handle_packet,
            self.stop_event,
            self.config.capture.management_only,
            1.0,
            self._on_tick,
        )
        logging.info("Capture stopped.")
        return 0

    def _install_signal_handlers(self) -> None:
        def _handler(_signum, _frame) -> None:
            self.stop_event.set()

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    def _handle_packet(self, pkt) -> None:
        event = parse_packet(pkt)
        if event is None:
            return
        if isinstance(event, DeauthEvent):
            self._handle_deauth(event)
        if isinstance(event, FrameEvent):
            self._update_ap_table(event)

    def _handle_deauth(self, event: DeauthEvent) -> None:
        self.deauth_seen += 1
        alert = self.detector.process(event)

        if self.deauth_limiter.allow("deauth"):
            logging.warning(
                "DEAUTH src=%s dst=%s bssid=%s reason=%s",
                event.src,
                event.dst,
                event.bssid,
                event.reason_code,
            )

        if alert:
            message = (
                f"{time.strftime('%H:%M:%S')} ALERT deauth_flood key={alert.key} "
                f"count={alert.count} window={alert.window_seconds}s"
            )
            self.alerts.append(message)
            logging.error(message)

    def _update_ap_table(self, event: FrameEvent) -> None:
        if event.frame_type != 0 or event.frame_subtype not in (8, 5):
            return
        if not event.bssid:
            return
        existing = self.ap_table.get(event.bssid)
        ssid = event.ssid if event.ssid is not None else (existing.ssid if existing else None)
        rssi = event.rssi if event.rssi is not None else (existing.rssi if existing else None)
        self.ap_table[event.bssid] = NetworkInfo(
            bssid=event.bssid,
            ssid=ssid,
            last_seen=event.timestamp,
            rssi=rssi,
        )

    def _prune_ap_table(self, now: float) -> None:
        stale_seconds = self.config.scanner.ap_stale_seconds
        for bssid in list(self.ap_table.keys()):
            info = self.ap_table[bssid]
            if now - info.last_seen > stale_seconds:
                del self.ap_table[bssid]

    def _on_tick(self) -> None:
        if not self.render_limiter.allow("render"):
            return
        self._render()

    def _render(self) -> None:
        now = time.time()
        self._prune_ap_table(now)
        lines = []
        lines.append("PWD-Box Passive AP Scan")
        lines.append(
            f"APs: {len(self.ap_table)}  Deauth frames: {self.deauth_seen}"
        )
        if self.alerts:
            lines.append("Recent alerts:")
            for message in list(self.alerts):
                lines.append(f"  {message}")
        lines.append("")
        lines.append("{:<24} {:<17} {:<6} {:<8}".format("SSID", "BSSID", "RSSI", "Seen(s)"))
        for info in sorted(
            self.ap_table.values(),
            key=lambda item: item.last_seen,
            reverse=True,
        ):
            ssid = info.ssid or "<hidden>"
            rssi = str(info.rssi) if info.rssi is not None else "-"
            age = int(now - info.last_seen)
            lines.append(
                "{:<24} {:<17} {:<6} {:<8}".format(
                    ssid[:24], info.bssid, rssi, age
                )
            )
        output = "\n".join(lines)
        print("\033[2J\033[H" + output, flush=True)
