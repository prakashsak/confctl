"""CLI sub-command: validate config files."""

from __future__ import annotations

import argparse
import sys

from confctl.validator import ValidationError, validate_all


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the 'validate' sub-command."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate one or more YAML config files.",
    )
    parser.add_argument(
        "configs",
        nargs="+",
        metavar="FILE",
        help="Config files to validate.",
    )
    parser.add_argument(
        "--require",
        dest="required_keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Top-level keys that must be present in every config.",
    )
    return parser


def run(args: argparse.Namespace, stdout=sys.stdout, stderr=sys.stderr) -> int:
    """Execute the validate command; return exit code."""
    try:
        results = validate_all(args.configs, required_keys=args.required_keys)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=stderr)
        return 1
    except ValidationError as exc:
        print(str(exc), file=stderr)
        return 1

    for path in results:
        print(f"OK  {path}", file=stdout)
    return 0
