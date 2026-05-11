from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pwdbox.config import load_config
from pwdbox.health import format_results, run_health_check


def main() -> int:
    parser = argparse.ArgumentParser(description="PWD-Box environment validation")
    parser.add_argument(
        "--config",
        help="Path to YAML config file (default: config/default.yaml)",
    )
    parser.add_argument("--interface", help="Interface to validate")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except RuntimeError as exc:
        if "PyYAML" in str(exc):
            config = None
        else:
            raise
    results = run_health_check(config, interface=args.interface)
    print(format_results(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
