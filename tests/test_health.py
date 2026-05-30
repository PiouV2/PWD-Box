from pathlib import Path

import pytest

try:
    from pwdbox.health import _check_storage_directories
    from pwdbox.config import (
        Config,
        CaptureConfig,
        DeauthConfig,
        EvidenceConfig,
        LoggingConfig,
        ScannerConfig,
        StorageConfig,
    )
except ImportError:
    from src.health import _check_storage_directories
    from src.config import (
        Config,
        CaptureConfig,
        DeauthConfig,
        EvidenceConfig,
        LoggingConfig,
        ScannerConfig,
        StorageConfig,
    )


def _config(tmp_path: Path) -> Config:
    return Config(
        capture=CaptureConfig(interface="wlan1"),
        scanner=ScannerConfig(),
        deauth=DeauthConfig(),
        logging=LoggingConfig(),
        storage=StorageConfig(db_path=str(tmp_path / "db" / "pwd_box.sqlite")),
        evidence=EvidenceConfig(pcap_dir=str(tmp_path / "pcaps")),
    )


def test_health_check_storage_directories_success(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    results = _check_storage_directories(cfg)

    assert len(results) == 2
    assert all(result.ok for result in results)
    assert (tmp_path / "db").exists()
    assert (tmp_path / "pcaps").exists()


def test_health_check_storage_directories_failure_reports_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = _config(tmp_path)

    def _boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "mkdir", _boom)
    results = _check_storage_directories(cfg)

    assert len(results) == 2
    assert all(not result.ok for result in results)
    assert all("permission denied" in result.details for result in results)
