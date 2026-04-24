"""CLI subcommand: lint — check config files for style and structure issues."""

from __future__ import annotations

import argparse
import sys

from confctl.linter import LintError, lint_config


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "lint",
        help="Lint config files for common issues",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more YAML config files to lint",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with non-zero status even for warnings",
    )
    return parser


def run(args: argparse.Namespace, stdout=sys.stdout, stderr=sys.stderr) -> int:
    """Run the lint subcommand. Returns exit code."""
    total_warnings = 0
    errors = 0

    for path in args.files:
        try:
            warnings = lint_config(path)
        except LintError as exc:
            print(f"ERROR: {exc}", file=stderr)
            errors += 1
            continue

        for warning in warnings:
            print(str(warning), file=stdout)

        total_warnings += len(warnings)

    if errors:
        return 2

    if args.strict and total_warnings:
        return 1

    return 0
