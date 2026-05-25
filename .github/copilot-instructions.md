# Copilot instructions for PWD-Box

## Commands

Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Health check:
```bash
sudo env PYTHONPATH=. .venv/bin/python -m src.main health-check --interface wlan1
```

Passive monitor:
```bash
sudo env PYTHONPATH=. .venv/bin/python -m src.main monitor --interface wlan1
```

UI:
```bash
PYTHONPATH=. .venv/bin/python -m src.ui
```

UI smoke test:
```bash
PYTHONPATH=. .venv/bin/python scripts/ui_smoke_test.py
```

Tests:
```bash
pytest -q
pytest tests/test_packet_parser.py -q
pytest tests/test_packet_parser.py::test_parse_deauth_event -q
pytest tests/test_deauth_detector.py::test_threshold_triggers_alert -q
```

No dedicated lint command is defined in this repo.

## Architecture

- `src/main.py` is the CLI entry point. It dispatches `health-check`, `monitor`, and `ui`, and keeps a fallback import path for running from the repo layout.
- `src/config.py` loads `config/default.yaml` into dataclasses for capture, scanner, deauth, logging, storage, and evidence settings.
- Passive monitoring flows through `src/capture/wifi_sniffer.py` -> `src/capture/packet_parser.py` -> `src/detection/deauth_detector.py` -> `src/orchestration/session_manager.py`.
- `SessionManager` owns the runtime loop, monitor-mode setup, capture readiness checks, packet handling, deauth alerting, SQLite session/alert writes, AP snapshot logging, and PCAP retention.
- `src/storage/db.py` is the shared persistence layer for sessions, alerts, network snapshots, and UI settings.
- `src/ui/` is a Kivy app. `MonitorController` runs `SessionManager` on a background thread and passes events to the UI through a queue; `PWDBoxApp` reads/writes persisted settings and drives the screen stack (`dashboard`, `networks`, `alerts`, `settings`, `pcap_settings`, `diagnostics`).

## Conventions

- Keep the system passive-only. Do not add packet injection, jamming, or offensive deauth behavior.
- Prefer the dataclasses in `src/models.py` and `src/config.py` for core data instead of ad hoc dicts.
- Keep packet parsing and detection defensive: malformed packets should return `None`, not raise.
- Reuse `src/storage/db.py` helpers for session, alert, snapshot, and settings persistence; the UI already reads and writes settings through `get_setting` / `set_setting`.
- Preserve the queue boundary between the capture thread and Kivy widgets. UI code should consume queued events rather than read capture state directly.
- When adding or changing Kivy screens, follow the existing `Theme` / `Card` / `PrimaryButton` / `SecondaryButton` helpers and the `RecycleView`/`ScrollView` patterns already used in the screens.
- Test modules import `pwdbox.*`, and `tests/conftest.py` adds `src/` to `sys.path`; keep that import layout in mind when moving modules or renaming packages.
