"""CLI sub-command: confctl summarize — print a structural summary of config files."""

from __future__ import annotations

import argparse
import sys

from confctl.summarizer import SummaryError, format_summary, load_yaml_for_summary, summarize


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "summarize",
        help="Print a structural summary of one or more YAML config files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML config files to summarize.",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output summaries as JSON.",
    )
    return p


def run(args: argparse.Namespace) -> int:
    import json

    results: list[dict] = []
    exit_code = 0

    for path in args.files:
        try:
            data = load_yaml_for_summary(path)
            summary = summarize(data)
            if args.as_json:
                results.append({"file": path, **summary})
            else:
                print(format_summary(path, summary))
        except SummaryError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            exit_code = 1

    if args.as_json:
        print(json.dumps(results, indent=2))

    return exit_code
