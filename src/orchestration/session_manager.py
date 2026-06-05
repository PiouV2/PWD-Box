from __future__ import annotations

from collections import deque
import logging
import os
import queue
import signal
import threading
import time
from typing import Any, Deque, Dict, Optional

from ..capture.packet_parser import parse_packet
from ..capture.wifi_sniffer import capture_test, check_monitor_mode, sniff_loop
from ..config import Config
from ..detection.deauth_detector import DeauthDetector
from ..evidence.pcap import (
    PcapBuffer,
    SessionPcapCapture,
    enforce_pcap_retention,
    save_pcap_for_alert,
)
from ..models import DeauthEvent, FrameEvent, NetworkInfo
from ..storage.db import (
    close_session,
    create_session,
    init_db,
    log_alert,
    log_network_snapshot,
    update_alert_pcap,
    update_session_pcap,
)
from ..utils.logging import RateLimiter


class SessionManager:
    def __init__(
        self,
        config: Config,
        event_queue: Optional[queue.Queue] = None,
    ) -> None:
        self.config = config
        self.event_queue = event_queue
        self.ap_table: Dict[str, NetworkInfo] = {}
        self.alerts: Deque[str] = deque(maxlen=5)
        self.deauth_seen = 0
        self.stop_event = threading.Event()
        self.session_id: Optional[int] = None
        self.db_path: Optional[str] = None
        self.status: Dict[str, Any] = {
            "adapter_ok": False,
            "monitor_mode": False,
            "logging_on": False,
            "evidence_active": False,
            "running": False,
            "interface": None,
            "message": None,
        }
        self.detector = DeauthDetector(
            threshold=config.deauth.threshold,
            window_seconds=config.deauth.window_seconds,
            cooldown_seconds=config.deauth.cooldown_seconds,
        )
        self.deauth_limiter = RateLimiter(config.logging.rate_limit_seconds)
        self.render_limiter = RateLimiter(config.scanner.render_interval_seconds)
        self.snapshot_limiter = RateLimiter(config.storage.snapshot_interval_seconds)
        self.render_console = True
        self.pcap_buffer: Optional[PcapBuffer] = None
        self.session_capture: Optional[SessionPcapCapture] = None
        self.session_pcap_path: Optional[str] = None
        self.session_capture_error: Optional[str] = None
        if config.evidence.pcap_enabled:
            self.pcap_buffer = PcapBuffer(
                config.evidence.pcap_buffer_seconds,
                config.evidence.pcap_max_packets,
            )
            self.session_capture = SessionPcapCapture(config.evidence.pcap_dir)

    def run(
        self,
        interface: Optional[str] = None,
        install_signal_handlers: bool = True,
        render_console: bool = True,
    ) -> int:
        self.stop_event.clear()
        self.render_console = render_console
        iface = interface or self.config.capture.interface
        self._emit_status(interface=iface)
        if not iface:
            logging.error("No capture interface specified.")
            self._emit_status(message="No capture interface specified.")
            return 1

        self._init_storage(iface)

        if not check_monitor_mode(iface):
            logging.error("Interface %s is not in monitor mode.", iface)
            self._emit_status(
                monitor_mode=False,
                message=self._capture_error_message(iface, "Interface is not in monitor mode"),
            )
            self._close_session("error")
            return 2
        self._emit_status(monitor_mode=True)

        if not capture_test(
            iface,
            self.config.capture.test_seconds,
            self.config.capture.management_only,
        ):
            logging.error(
                "Capture test failed: no 802.11 management frames seen on %s.",
                iface,
            )
            self._emit_status(
                adapter_ok=False,
                message=self._capture_error_message(iface, "Capture test failed"),
            )
            self._close_session("error")
            return 3

        self._start_session_capture()

        self._emit_status(adapter_ok=True, running=True, message=None)
        if install_signal_handlers:
            self._install_signal_handlers()
        logging.info("Starting passive capture on %s.", iface)

        exit_code = 0
        try:
            sniff_loop(
                iface,
                self._handle_packet,
                self.stop_event,
                self.config.capture.management_only,
                1.0,
                self._on_tick,
            )
        except Exception as exc:
            logging.exception("Capture error: %s", exc)
            self._emit_status(message=f"Capture error on {iface}: {exc}")
            exit_code = 4
        logging.info("Capture stopped.")
        self._emit_status(
            running=False,
            evidence_active=False,
            message=None if exit_code == 0 else self.status.get("message"),
        )
        self._close_session("stopped" if self.stop_event.is_set() else "ended")
        return exit_code

    def _install_signal_handlers(self) -> None:
        def _handler(_signum, _frame) -> None:
            self.stop_event.set()

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    def stop(self) -> None:
        self.stop_event.set()

    def _capture_error_message(self, iface: str, prefix: str) -> str:
        if os.geteuid() != 0:
            return (
                f"{prefix} on {iface}. Run the UI with sudo or grant "
                "CAP_NET_ADMIN and CAP_NET_RAW."
            )
        return f"{prefix} on {iface}. Check monitor-mode support and adapter state."

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self.event_queue:
            return
        try:
            self.event_queue.put_nowait({"type": event_type, "data": data})
        except queue.Full:
            return

    def _emit_status(self, **updates: Any) -> None:
        self.status.update({key: value for key, value in updates.items()})
        self._emit_event("status", dict(self.status))

    def _init_storage(self, iface: str) -> None:
        try:
            self.db_path = str(init_db(self.config.storage.db_path))
            self.session_id = create_session(
                iface,
                status="running",
                db_path=self.db_path,
            )
            self._emit_status(logging_on=True, evidence_active=False)
        except Exception as exc:
            logging.error("Database init failed: %s", exc)
            self.db_path = None
            self.session_id = None
            self._emit_status(
                logging_on=False,
                evidence_active=False,
                message=f"DB init failed: {exc}",
            )

    def _close_session(self, status: str) -> None:
        self._finalize_session_capture()
        if self.session_id is None:
            return
        try:
            close_session(self.session_id, status=status, db_path=self.db_path)
        except Exception as exc:
            logging.error("Session close failed: %s", exc)

    def _start_session_capture(self) -> None:
        if self.session_capture is None or self.session_id is None:
            return
        try:
            output_path = self.session_capture.start(self.session_id)
        except Exception as exc:
            self._disable_session_capture(exc)
            return

        self.session_pcap_path = str(output_path)
        try:
            update_session_pcap(self.session_id, self.session_pcap_path, db_path=self.db_path)
        except Exception as exc:
            logging.error("Session evidence path update failed: %s", exc)

        self._emit_status(evidence_active=True)
        self._emit_event(
            "evidence",
            {
                "active": True,
                "notice": "Capturing evidence...",
            },
        )

    def _finalize_session_capture(self) -> None:
        if self.session_capture is None:
            return

        try:
            output_path = self.session_capture.stop()
        except Exception as exc:
            self._disable_session_capture(exc)
            return

        self._emit_status(evidence_active=False)
        self.session_capture = None

        if output_path is None:
            return
        self.session_pcap_path = str(output_path)

        if self.session_id is not None:
            try:
                update_session_pcap(self.session_id, self.session_pcap_path, db_path=self.db_path)
            except Exception as exc:
                logging.error("Session evidence path update failed: %s", exc)

        try:
            enforce_pcap_retention(
                self.config.evidence.pcap_dir,
                self.config.evidence.pcap_max_files,
                self.config.evidence.pcap_max_total_mb,
            )
        except Exception as exc:
            logging.error("Evidence retention failed: %s", exc)

        self._emit_event(
            "evidence",
            {
                "active": False,
                "pcap_path": self.session_pcap_path,
                "notice": f"Evidence saved: {output_path.name}",
            },
        )

    def _disable_session_capture(self, exc: Exception) -> None:
        self.session_capture_error = f"Evidence capture failed: {exc}"
        logging.error(self.session_capture_error)
        if self.session_capture is not None:
            try:
                self.session_capture.stop()
            except Exception:
                pass
        self.session_capture = None
        self._emit_status(evidence_active=False)
        self._emit_event(
            "evidence",
            {
                "active": False,
                "error": self.session_capture_error,
            },
        )

    def _handle_packet(self, pkt) -> None:
        if self.session_capture is not None:
            try:
                self.session_capture.write(pkt)
            except Exception as exc:
                self._disable_session_capture(exc)
        if self.pcap_buffer is not None:
            self.pcap_buffer.add(pkt)
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
            alert_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(alert.timestamp))
            alert_payload: Dict[str, Any] = {
                "timestamp": alert_ts,
                "alert_type": alert.alert_type,
                "key": alert.key,
                "count": alert.count,
                "window_seconds": alert.window_seconds,
                "src": event.src,
                "dst": event.dst,
                "bssid": event.bssid,
                "reason_code": event.reason_code,
            }
            alert_id: Optional[int] = None
            pcap_path: Optional[str] = None

            if self.session_id is not None:
                try:
                    alert_id = log_alert(
                        self.session_id,
                        alert_payload,
                        db_path=self.db_path,
                    )
                    if self.pcap_buffer is not None:
                        pcap_file = save_pcap_for_alert(
                            self.pcap_buffer,
                            self.session_id,
                            alert_id,
                            pcap_dir=self.config.evidence.pcap_dir,
                            timestamp=alert.timestamp,
                        )
                        if pcap_file is not None:
                            pcap_path = str(pcap_file)
                            update_alert_pcap(alert_id, pcap_path, db_path=self.db_path)
                            enforce_pcap_retention(
                                self.config.evidence.pcap_dir,
                                self.config.evidence.pcap_max_files,
                                self.config.evidence.pcap_max_total_mb,
                            )
                except Exception as exc:
                    logging.error("Alert logging failed: %s", exc)

            if pcap_path:
                alert_payload["pcap_path"] = pcap_path

            message = (
                f"{time.strftime('%H:%M:%S')} ALERT deauth_flood key={alert.key} "
                f"count={alert.count} window={alert.window_seconds}s"
            )
            if pcap_path:
                message = f"{message} pcap={pcap_path}"
            self.alerts.append(message)
            logging.error(message)
            self._emit_event("alert", alert_payload)

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
        now = time.time()
        self._prune_ap_table(now)

        if self.render_limiter.allow("render"):
            if self.render_console:
                self._render(now)
            self._emit_networks(now)

        if self.snapshot_limiter.allow("snapshot"):
            self._log_network_snapshots(now)

    def _emit_networks(self, now: float) -> None:
        if not self.event_queue:
            return
        items = []
        for info in sorted(
            self.ap_table.values(),
            key=lambda item: item.last_seen,
            reverse=True,
        ):
            items.append(
                {
                    "ssid": info.ssid,
                    "bssid": info.bssid,
                    "rssi": info.rssi,
                    "last_seen": info.last_seen,
                    "age_seconds": int(now - info.last_seen),
                }
            )
        self._emit_event("networks", {"items": items, "timestamp": now})

    def _log_network_snapshots(self, now: float) -> None:
        if self.session_id is None:
            return
        snapshots = []
        for info in self.ap_table.values():
            snapshots.append(
                {
                    "ssid": info.ssid,
                    "bssid": info.bssid,
                    "channel": None,
                    "rssi": info.rssi,
                    "encryption": None,
                    "caps": None,
                }
            )
        if not snapshots:
            return
        try:
            log_network_snapshot(
                self.session_id,
                snapshots,
                db_path=self.db_path,
            )
        except Exception as exc:
            logging.error("Network snapshot logging failed: %s", exc)

    def _render(self, now: float) -> None:
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
