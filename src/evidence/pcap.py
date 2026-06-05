"""PCAP buffering, capture, and retention helpers."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import time
from typing import Deque, List, Optional, Tuple

from scapy.utils import PcapWriter, wrpcap

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PCAP_DIR = PROJECT_ROOT / "data" / "pcaps"
DEFAULT_LINKTYPE = 127


class PcapBuffer:
    """Keep a rolling packet buffer for alert evidence."""

    def __init__(self, max_seconds: float, max_packets: int) -> None:
        """Set buffer limits and initialize storage."""
        self.max_seconds = max(max_seconds, 1.0)
        self.max_packets = max(max_packets, 1)
        self._packets: Deque[Tuple[float, object]] = deque()

    def add(self, pkt, timestamp: Optional[float] = None) -> None:
        """Add a packet and prune to the configured limits."""
        ts = timestamp if timestamp is not None else float(getattr(pkt, "time", time.time()))
        self._packets.append((ts, pkt))
        self._prune(ts)

    def snapshot(self) -> List[object]:
        """Return a list of buffered packets."""
        return [pkt for _, pkt in self._packets]

    def _prune(self, now: float) -> None:
        """Drop packets outside the time or size window."""
        cutoff = now - self.max_seconds
        while self._packets and self._packets[0][0] < cutoff:
            self._packets.popleft()
        while len(self._packets) > self.max_packets:
            self._packets.popleft()


class SessionPcapCapture:
    """Write all session traffic to a single PCAP file."""

    def __init__(self, pcap_dir: Optional[str] = None, linktype: int = DEFAULT_LINKTYPE) -> None:
        """Prepare the capture output path and linktype."""
        self._pcap_dir = pcap_dir
        self._linktype = linktype
        self._writer: Optional[PcapWriter] = None
        self.path: Optional[Path] = None

    @property
    def is_active(self) -> bool:
        """Return True when a writer and output path are ready."""
        return self._writer is not None and self.path is not None

    def start(
        self,
        session_id: int,
        timestamp: Optional[float] = None,
    ) -> Path:
        """Open a new PCAP file for the given session."""
        if self.path is not None:
            return self.path

        target_dir = resolve_pcap_dir(self._pcap_dir)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"Could not create evidence directory: {target_dir}") from exc
        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp or time.time()))
        output_path = target_dir / f"pwd_{ts}_s{session_id}.pcap"
        writer = PcapWriter(
            str(output_path),
            append=False,
            sync=True,
            linktype=self._linktype,
        )
        self._writer = writer
        self.path = output_path
        return output_path

    def write(self, pkt) -> None:
        """Append a packet to the session PCAP."""
        if self._writer is None:
            return
        self._writer.write(pkt)

    def stop(self) -> Optional[Path]:
        """Close the PCAP writer and return the file path."""
        writer = self._writer
        self._writer = None
        if writer is not None:
            writer.close()
        return self.path


def resolve_pcap_dir(pcap_dir: Optional[str]) -> Path:
    """Resolve a PCAP directory to an absolute path."""
    path = Path(pcap_dir) if pcap_dir else DEFAULT_PCAP_DIR
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def save_pcap_for_alert(
    buffer: PcapBuffer,
    session_id: int,
    alert_id: int,
    pcap_dir: Optional[str] = None,
    timestamp: Optional[float] = None,
) -> Optional[Path]:
    """Save buffered packets as a per-alert PCAP file."""
    packets = buffer.snapshot()
    if not packets:
        return None

    target_dir = resolve_pcap_dir(pcap_dir)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Could not create evidence directory: {target_dir}") from exc
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp or time.time()))
    filename = f"pwd_{ts}_s{session_id}_a{alert_id}.pcap"
    output_path = target_dir / filename
    wrpcap(str(output_path), packets)
    return output_path


def enforce_pcap_retention(
    pcap_dir: Optional[str] = None,
    max_files: int = 0,
    max_total_mb: int = 0,
) -> None:
    """Delete old PCAP files to stay under retention limits."""
    target_dir = resolve_pcap_dir(pcap_dir)
    if not target_dir.exists():
        return

    pcap_files = sorted(
        (path for path in target_dir.glob("*.pcap") if path.is_file()),
        key=lambda item: item.stat().st_mtime,
    )
    if not pcap_files:
        return

    total_bytes = sum(path.stat().st_size for path in pcap_files)
    max_bytes = max_total_mb * 1024 * 1024 if max_total_mb > 0 else 0

    def over_limits() -> bool:
        if max_files > 0 and len(pcap_files) > max_files:
            return True
        if max_bytes > 0 and total_bytes > max_bytes:
            return True
        return False

    while pcap_files and over_limits():
        oldest = pcap_files.pop(0)
        try:
            size = oldest.stat().st_size
        except OSError:
            size = 0
        try:
            oldest.unlink(missing_ok=True)
        except OSError:
            break
        total_bytes = max(total_bytes - size, 0)
