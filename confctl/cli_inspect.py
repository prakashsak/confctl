"""CLI sub-command: confctl inspect — display structure overview of config files."""

from __future__ import annotations

import argparse
import sys

from confctl.inspector import InspectError, inspect_config, format_inspection


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Inspect YAML config files and report structure statistics."
    if subparsers is not None:
        parser = subparsers.add_parser("inspect", help=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl inspect", description=description)
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more YAML config files to inspect.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output inspection report as JSON.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    import json

    exit_code = 0
    reports = []
    for path in args.files:
        try:
            report = inspect_config(path)
            reports.append(report)
        except InspectError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            exit_code = 1

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for i, report in enumerate(reports):
            if i > 0:
                print()
            print(format_inspection(report))

    return exit_code


if __name__ == "__main__":
    _parser = build_parser()
    _args = _parser.parse_args()
    sys.exit(run(_args))
