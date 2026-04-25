"""CLI sub-command: compare two config directories."""

from __future__ import annotations

import argparse
import sys

from confctl.comparator import CompareError, compare_dirs, format_compare_result


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Compare two config directories for structural differences."
    if subparsers is not None:
        parser = subparsers.add_parser("compare", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl compare", description=description)

    parser.add_argument("left", help="Path to the left config directory")
    parser.add_argument("right", help="Path to the right config directory")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress output; only set exit code",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        result = compare_dirs(args.left, args.right)
    except CompareError as exc:
        print(f"compare error: {exc}", file=sys.stderr)
        return 2

    has_diff = bool(
        result.only_in_left or result.only_in_right or result.key_diffs
    )

    if not args.quiet:
        print(format_compare_result(result, args.left, args.right))

    if args.exit_code and has_diff:
        return 1
    return 0
