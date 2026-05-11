from __future__ import annotations

import argparse
import sys
from typing import Optional

from .config import load_config
from .health import format_results, run_health_check
from .orchestration.session_manager import SessionManager
from .utils.logging import setup_logging


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PWD-Box passive monitoring CLI")
    parser.add_argument(
        "--config",
        help="Path to YAML config file (default: config/default.yaml)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    health_parser = subparsers.add_parser("health-check", help="Run readiness checks")
    health_parser.add_argument("--interface", help="Interface to validate")

    monitor_parser = subparsers.add_parser("monitor", help="Start passive monitoring")
    monitor_parser.add_argument("--interface", help="Interface to capture from")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "health-check":
        config = load_config(args.config)
        results = run_health_check(config, interface=args.interface)
        print(format_results(results))
        return 0 if all(result.ok for result in results) else 1

    if args.command == "monitor":
        config = load_config(args.config)
        setup_logging(config.logging.level)
        session = SessionManager(config)
        return session.run(interface=args.interface)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
