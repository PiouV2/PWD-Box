# PWD-Box — Portable Wireless Defence Box

Hey! 👋 Welcome to PWD-Box. a small, friendly, and very passive Wi‑Fi watchdog.

This repo is a prototype: it sniffs, parses, and watches for suspicious
deauthentication floods. It is intentionally simple, lightweight, and safe.

Important vibes (read this first):
- This tool is passive-only. It listens. It does NOT send packets, deauths,
  jam, or mess with networks. Use responsibly and only where you have permission.

What it does :
- Health checks for tools, OS/Python, and adapter presence
- Enables/validates monitor mode (where possible)
- Passively scans for nearby APs and keeps an in-memory list
- Parses 802.11 management frames and recognizes deauth frames
- Alerts when deauth frames exceed configured thresholds (sliding window)
- Stores sessions/alerts/network snapshots in SQLite
- Captures short PCAP evidence windows on alerts

Quick setup (Raspberry Pi OS-ish)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run health checks (replace `wlan1` with your monitor interface):
```bash
sudo env PYTHONPATH=. .venv/bin/python -m src.main health-check --interface wlan1
```

Start passive monitoring:
```bash
sudo env PYTHONPATH=. .venv/bin/python -m src.main monitor --interface wlan1
```

Start the touchscreen UI:
```bash
sudo env PYTHONPATH=. .venv/bin/python -m src.ui
```

UI smoke test (boots UI with demo data, no sniffing):
```bash
PYTHONPATH=. .venv/bin/python scripts/ui_smoke_test.py
```

Run the (safe) tests:
```bash
pytest -q
```

Config
- The default settings are in `config/default.yaml`. Tweak the `interface`,
  deauth thresholds, and AP stale timeout there. Keep thresholds conservative.

Notes & limits
- Touchscreen UI is provided via Kivy (see troubleshooting below).
- No Bluetooth, no packet injection, and no offensive features.
- Keeps CPU/memory low-ish for use on a Raspberry Pi 3B+.

Data storage
- SQLite DB: data/db/pwd_box.sqlite (auto-created)
- PCAP evidence: data/pcaps/ (auto-created)

Retention defaults
- DB: all sessions/alerts are kept by default (no automatic purge).
- PCAP: defaults to max 200 files or 100 MB total, deleting oldest first.
- Tune storage and evidence settings in config/default.yaml.

Troubleshooting
- Permissions: run with sudo or grant CAP_NET_ADMIN and CAP_NET_RAW.
- Interface: confirm the adapter name with `iw dev` and update config/default.yaml.
- Kivy install: on Raspberry Pi OS, install build deps if pip fails
    (e.g., `sudo apt install libgl1-mesa-dev libgles2-mesa-dev`).

If you break anything, blame the cat. If the cat is innocent, ping me.

Have fun being a polite network detective! 🕵️‍♀️

— The PWD-Box Team (well, mainly code and good intentions)
