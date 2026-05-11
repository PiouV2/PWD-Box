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

Quick setup (Raspberry Pi OS-ish)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run health checks (replace `wlan1` with your monitor interface):
```bash
sudo .venv/bin/python -m pwdbox.main health-check --interface wlan1
```

Start passive monitoring:
```bash
sudo .venv/bin/python -m pwdbox.main monitor --interface wlan1
```

Run the (safe) tests:
```bash
pytest -q
```

Config
- The default settings are in `config/default.yaml`. Tweak the `interface`,
  deauth thresholds, and AP stale timeout there. Keep thresholds conservative.

Notes & limits
- No UI (yet). This is CLI-only for Phase 1.
- No database or PCAP evidence capture in this phase.
- No Bluetooth, no packet injection, and no offensive features.
- Keeps CPU/memory low-ish for use on a Raspberry Pi 3B+.

If you break anything, blame the cat. If the cat is innocent, ping me.

Have fun being a polite network detective! 🕵️‍♀️

— The PWD-Box Team (well, mainly code and good intentions)
