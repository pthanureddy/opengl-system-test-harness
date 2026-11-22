from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .runner import run_harness


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opengl-system-test",
        description="Run deterministic headless OpenGL workloads and produce CI-readable evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a scenario file")
    validate.add_argument("--config", required=True, type=Path)
    run = subparsers.add_parser("run", help="execute configured workloads")
    run.add_argument("--config", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--backend", default="auto", choices=["auto", "egl", "wgl", "x11"])
    run.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "validate":
            print(
                json.dumps(
                    {
                        "valid": True,
                        "schema_version": config.schema_version,
                        "scenario_count": len(config.scenarios),
                    },
                    sort_keys=True,
                )
            )
            return 0
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        report = run_harness(config, args.output, backend=args.backend)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "scenario_count": report["scenario_count"],
                    "passed_scenario_count": report["passed_scenario_count"],
                    "report": str(args.output / "report.json"),
                },
                sort_keys=True,
            )
        )
        return 0 if report["status"] == "passed" else 1
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"setup error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
