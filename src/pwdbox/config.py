from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class CaptureConfig:
    interface: Optional[str] = None
    enable_monitor: bool = True
    test_seconds: float = 3.0
    management_only: bool = True


@dataclass
class ScannerConfig:
    ap_stale_seconds: int = 60
    render_interval_seconds: float = 2.0


@dataclass
class DeauthConfig:
    window_seconds: float = 10.0
    threshold: int = 20
    cooldown_seconds: float = 30.0


@dataclass
class LoggingConfig:
    level: str = "INFO"
    rate_limit_seconds: float = 1.0


@dataclass
class Config:
    capture: CaptureConfig
    scanner: ScannerConfig
    deauth: DeauthConfig
    logging: LoggingConfig

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Config":
        capture_data = _get_section(data, "capture")
        scanner_data = _get_section(data, "scanner")
        deauth_data = _get_section(data, "deauth")
        logging_data = _get_section(data, "logging")
        return Config(
            capture=CaptureConfig(
                interface=capture_data.get("interface"),
                enable_monitor=bool(capture_data.get("enable_monitor", True)),
                test_seconds=float(capture_data.get("test_seconds", 3.0)),
                management_only=bool(capture_data.get("management_only", True)),
            ),
            scanner=ScannerConfig(
                ap_stale_seconds=int(scanner_data.get("ap_stale_seconds", 60)),
                render_interval_seconds=float(
                    scanner_data.get("render_interval_seconds", 2.0)
                ),
            ),
            deauth=DeauthConfig(
                window_seconds=float(deauth_data.get("window_seconds", 10.0)),
                threshold=int(deauth_data.get("threshold", 20)),
                cooldown_seconds=float(deauth_data.get("cooldown_seconds", 30.0)),
            ),
            logging=LoggingConfig(
                level=str(logging_data.get("level", "INFO")),
                rate_limit_seconds=float(logging_data.get("rate_limit_seconds", 1.0)),
            ),
        )


def _default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "default.yaml"


def _get_section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    section = data.get(key, {})
    return section if isinstance(section, dict) else {}


def load_config(path: Optional[str] = None) -> Config:
    config_path = Path(path) if path else _default_config_path()
    data: Dict[str, Any] = {}
    if config_path.exists():
        raw_text = config_path.read_text()
        data = yaml.safe_load(raw_text) or {}
    return Config.from_dict(data)
