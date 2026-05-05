"""CLI interface for the sorter module."""

from __future__ import annotations

import argparse
import sys

from confctl.sorter import SortError, sort_config, load_yaml_for_sort, dump_sorted


def build_parser(subparsers=None):
    """Build (and optionally register) the sort sub-command parser."""
    kwargs = dict(
        description="Sort keys in YAML config files alphabetically.",
        help="sort keys in one or more YAML config files",
    )
    if subparsers is not None:
        parser = subparsers.add_parser("sort", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("files", nargs="+", metavar="FILE", help="YAML config files to sort")
    parser.add_argument(
        "--reverse", action="store_true", default=False, help="sort keys in descending order"
    )
    parser.add_argument(
        "--output", metavar="FILE", default=None,
        help="write result to FILE instead of overwriting the source (only valid with a single input file)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="print sorted output to stdout without writing files",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the sort command; return exit code."""
    if args.output and len(args.files) > 1:
        print("error: --output can only be used with a single input file", file=sys.stderr)
        return 2

    exit_code = 0
    for path in args.files:
        try:
            data = load_yaml_for_sort(path)
            sorted_data = sort_config(data, reverse=args.reverse)
            result = dump_sorted(sorted_data)
        except SortError as exc:
            print(f"error: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        if args.dry_run:
            print(f"# {path}")
            print(result)
        else:
            dest = args.output or path
            from pathlib import Path
            Path(dest).write_text(result, encoding="utf-8")
            print(f"sorted: {dest}")

    return exit_code
