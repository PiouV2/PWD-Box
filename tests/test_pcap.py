from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt, RadioTap
from scapy.utils import rdpcap
import pytest

try:
    from pwdbox.evidence.pcap import PcapBuffer, SessionPcapCapture, save_pcap_for_alert
except ImportError:
    from evidence.pcap import PcapBuffer, SessionPcapCapture, save_pcap_for_alert


def _packet():
    return (
        RadioTap()
        / Dot11(
            type=0,
            subtype=8,
            addr1="ff:ff:ff:ff:ff:ff",
            addr2="aa:bb:cc:dd:ee:ff",
            addr3="aa:bb:cc:dd:ee:ff",
        )
        / Dot11Beacon()
        / Dot11Elt(ID="SSID", info=b"TestNet")
    )


def test_session_capture_records_packets(tmp_path) -> None:
    capture = SessionPcapCapture(pcap_dir=str(tmp_path))

    output_path = capture.start(session_id=42, timestamp=0)
    capture.write(_packet())
    stopped_path = capture.stop()

    assert output_path == stopped_path
    assert output_path.exists()
    assert len(rdpcap(str(output_path))) == 1


def test_session_capture_close_is_idempotent(tmp_path) -> None:
    capture = SessionPcapCapture(pcap_dir=str(tmp_path))

    output_path = capture.start(session_id=77, timestamp=0)
    first = capture.stop()
    second = capture.stop()

    assert first == output_path
    assert second == output_path


def test_session_capture_empty_file_is_readable(tmp_path) -> None:
    capture = SessionPcapCapture(pcap_dir=str(tmp_path))

    output_path = capture.start(session_id=10, timestamp=0)
    capture.stop()

    packets = rdpcap(str(output_path))
    assert len(packets) == 0


def test_alert_pcap_snapshot_still_works(tmp_path) -> None:
    buffer = PcapBuffer(max_seconds=15, max_packets=100)
    buffer.add(_packet())

    output_path = save_pcap_for_alert(
        buffer,
        session_id=1,
        alert_id=2,
        pcap_dir=str(tmp_path),
        timestamp=0,
    )

    assert output_path is not None
    assert output_path.exists()
    assert len(rdpcap(str(output_path))) == 1


def test_session_capture_raises_clear_error_if_dir_creation_fails(monkeypatch, tmp_path) -> None:
    capture = SessionPcapCapture(pcap_dir=str(tmp_path / "pcaps"))

    def _boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("pathlib.Path.mkdir", _boom)

    with pytest.raises(RuntimeError, match="Could not create evidence directory"):
        capture.start(session_id=1)
