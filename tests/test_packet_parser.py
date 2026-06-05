"""Packet parser tests."""

from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt, RadioTap

from pwdbox.capture.packet_parser import parse_packet
from pwdbox.models import DeauthEvent


def test_parse_beacon_extracts_ssid() -> None:
    """Beacon frames produce SSID and RSSI values."""
    pkt = (
        RadioTap(dBm_AntSignal=-40)
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

    event = parse_packet(pkt)
    assert event is not None
    assert event.ssid == "TestNet"
    assert event.bssid == "aa:bb:cc:dd:ee:ff"
    assert event.rssi == -40


def test_parse_deauth_event() -> None:
    """Deauth frames produce DeauthEvent records."""
    pkt = (
        RadioTap()
        / Dot11(
            type=0,
            subtype=12,
            addr1="ff:ff:ff:ff:ff:ff",
            addr2="11:22:33:44:55:66",
            addr3="11:22:33:44:55:66",
        )
        / Dot11Deauth(reason=7)
    )
    event = parse_packet(pkt)
    assert isinstance(event, DeauthEvent)
    assert event.reason_code == 7


def test_parse_malformed_packet_returns_none() -> None:
    """Malformed inputs return None."""
    assert parse_packet(None) is None
    assert parse_packet(object()) is None
