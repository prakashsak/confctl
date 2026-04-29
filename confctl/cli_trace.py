"""CLI sub-command: confctl trace — trace key origins across config files."""

from __future__ import annotations

import argparse
import sys

from confctl.tracer import TraceError, format_trace, trace_all_keys, trace_key


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Trace where a config key is defined across multiple files."
    if subparsers is not None:
        parser = subparsers.add_parser("trace", help=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl trace", description=description)

    parser.add_argument("files", nargs="+", metavar="FILE", help="Config files to search")
    parser.add_argument(
        "--key", "-k", metavar="KEY", default=None,
        help="Dot-separated key to trace (omit to list all keys)"
    )
    parser.add_argument(
        "--duplicates-only", action="store_true",
        help="Only show keys defined in more than one file"
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        if args.key:
            origins = trace_key(args.key, args.files)
            if not origins:
                print(f"Key '{args.key}' not found in any of the provided files.",
                      file=sys.stderr)
                return 1
            print(f"Key '{args.key}' found in:")
            print(format_trace(origins))
        else:
            index = trace_all_keys(args.files)
            shown = 0
            for key, records in sorted(index.items()):
                if args.duplicates_only and len(records) < 2:
                    continue
                print(f"{key}:")
                print(format_trace(records))
                shown += 1
            if shown == 0:
                print("(nothing to show)")
    except TraceError as exc:
        print(f"trace error: {exc}", file=sys.stderr)
        return 1
    return 0
