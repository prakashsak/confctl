"""CLI sub-command: merge a base config with an environment override."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from confctl.merger import MergeError, dump_merged, merge_configs


def build_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *merge* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "merge",
        help="Merge a base config with an environment-specific override.",
    )
    parser.add_argument("base", type=Path, help="Path to the base YAML config file.")
    parser.add_argument("env", type=Path, help="Path to the environment YAML config file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write merged config to this file instead of stdout.",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the merge command; return exit code."""
    try:
        merged = merge_configs(args.base, args.env)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except MergeError as exc:
        print(f"merge error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        try:
            dump_merged(merged, args.output)
            print(f"Merged config written to {args.output}")
        except OSError as exc:
            print(f"error writing output: {exc}", file=sys.stderr)
            return 1
    else:
        import yaml  # local import to keep startup fast when not needed

        print(yaml.dump(merged, default_flow_style=False, sort_keys=True), end="")

    return 0
