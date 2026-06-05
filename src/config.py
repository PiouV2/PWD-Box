"""Configuration loading and dataclass definitions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CaptureConfig:
    """Capture-related configuration values."""
    interface: Optional[str] = None
    enable_monitor: bool = True
    test_seconds: float = 3.0
    management_only: bool = True


@dataclass
class ScannerConfig:
    """Scanner-related timing and UI refresh settings."""
    ap_stale_seconds: int = 60
    render_interval_seconds: float = 2.0


@dataclass
class DeauthConfig:
    """Thresholds for deauth detection."""
    window_seconds: float = 10.0
    threshold: int = 20
    cooldown_seconds: float = 30.0


@dataclass
class LoggingConfig:
    """Logging level and rate limits."""
    level: str = "INFO"
    rate_limit_seconds: float = 1.0


@dataclass
class StorageConfig:
    """Storage paths and snapshot intervals."""
    db_path: Optional[str] = None
    snapshot_interval_seconds: float = 10.0


@dataclass
class EvidenceConfig:
    """Evidence capture and retention settings."""
    pcap_enabled: bool = True
    pcap_dir: Optional[str] = None
    pcap_buffer_seconds: float = 15.0
    pcap_max_packets: int = 2000
    pcap_max_files: int = 200
    pcap_max_total_mb: int = 100


@dataclass
class Config:
    """Top-level configuration structure."""
    capture: CaptureConfig
    scanner: ScannerConfig
    deauth: DeauthConfig
    logging: LoggingConfig
    storage: StorageConfig
    evidence: EvidenceConfig

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Config":
        """Build a Config from a nested dictionary."""
        capture_data = _get_section(data, "capture")
        scanner_data = _get_section(data, "scanner")
        deauth_data = _get_section(data, "deauth")
        logging_data = _get_section(data, "logging")
        storage_data = _get_section(data, "storage")
        evidence_data = _get_section(data, "evidence")
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
            storage=StorageConfig(
                db_path=storage_data.get("db_path"),
                snapshot_interval_seconds=float(
                    storage_data.get("snapshot_interval_seconds", 10.0)
                ),
            ),
            evidence=EvidenceConfig(
                pcap_enabled=bool(evidence_data.get("pcap_enabled", True)),
                pcap_dir=evidence_data.get("pcap_dir"),
                pcap_buffer_seconds=float(
                    evidence_data.get("pcap_buffer_seconds", 15.0)
                ),
                pcap_max_packets=int(evidence_data.get("pcap_max_packets", 2000)),
                pcap_max_files=int(evidence_data.get("pcap_max_files", 200)),
                pcap_max_total_mb=int(evidence_data.get("pcap_max_total_mb", 100)),
            ),
        )


def _default_config_path() -> Path:
    """Return the default config file path."""
    return Path(__file__).resolve().parents[2] / "config" / "default.yaml"


def _get_section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Return a dict section or an empty fallback."""
    section = data.get(key, {})
    return section if isinstance(section, dict) else {}


def load_config(path: Optional[str] = None) -> Config:
    """Load config from YAML and return a Config object."""
    config_path = Path(path) if path else _default_config_path()
    data: Dict[str, Any] = {}
    if config_path.exists():
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PyYAML is required to load the config. Install with: pip install pyyaml"
            ) from exc
        raw_text = config_path.read_text()
        data = yaml.safe_load(raw_text) or {}
    return Config.from_dict(data)
