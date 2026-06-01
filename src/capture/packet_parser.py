from __future__ import annotations

import time
from typing import Optional

from scapy.layers.dot11 import Dot11, Dot11Deauth, Dot11Elt, RadioTap

from ..models import DeauthEvent, FrameEvent


def _extract_ssid(pkt) -> Optional[str]:
    try:
        if not pkt.haslayer(Dot11Elt):
            return None
        element = pkt[Dot11Elt]
        while isinstance(element, Dot11Elt):
            if element.ID == 0:
                info = element.info or b""
                if isinstance(info, bytes):
                    text = info.decode(errors="ignore").strip()
                else:
                    text = str(info).strip()
                return text or None
            element = element.payload
    except Exception:
        return None
    return None


def _extract_rssi(pkt) -> Optional[int]:
    try:
        if pkt.haslayer(RadioTap):
            radiotap = pkt.getlayer(RadioTap)
            # getattr goes through ConditionalField and may return None even when
            # the value is set; read from the fields dict directly.
            val = radiotap.fields.get("dBm_AntSignal")
            if val is not None:
                return int(val)
    except Exception:
        return None
    return None


def parse_packet(pkt) -> Optional[FrameEvent]:
    try:
        if pkt is None or not hasattr(pkt, "haslayer"):
            return None
        if not pkt.haslayer(Dot11):
            return None

        dot11 = pkt[Dot11]
        frame_type = int(getattr(dot11, "type", -1))
        frame_subtype = int(getattr(dot11, "subtype", -1))
        src = getattr(dot11, "addr2", None)
        dst = getattr(dot11, "addr1", None)
        bssid = getattr(dot11, "addr3", None) or getattr(dot11, "addr2", None)
        ssid = _extract_ssid(pkt)
        rssi = _extract_rssi(pkt)
        timestamp = float(getattr(pkt, "time", time.time()))
        monotonic_ts = time.monotonic()
        raw_len = len(pkt) if hasattr(pkt, "__len__") else None

        if pkt.haslayer(Dot11Deauth) or (frame_type == 0 and frame_subtype == 12):
            reason_code = None
            if pkt.haslayer(Dot11Deauth):
                reason_code = getattr(pkt[Dot11Deauth], "reason", None)
            return DeauthEvent(
                timestamp=timestamp,
                monotonic_ts=monotonic_ts,
                frame_type=frame_type,
                frame_subtype=frame_subtype,
                src=src,
                dst=dst,
                bssid=bssid,
                ssid=ssid,
                rssi=rssi,
                raw_len=raw_len,
                reason_code=reason_code,
            )

        return FrameEvent(
            timestamp=timestamp,
            monotonic_ts=monotonic_ts,
            frame_type=frame_type,
            frame_subtype=frame_subtype,
            src=src,
            dst=dst,
            bssid=bssid,
            ssid=ssid,
            rssi=rssi,
            raw_len=raw_len,
        )
    except Exception:
        return None
