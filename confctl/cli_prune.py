"""CLI sub-command: confctl prune."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from confctl.pruner import PruneError, dump_pruned, find_stale_keys, load_yaml_for_prune, prune_keys


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "prune",
        help="Remove keys from a config file that are absent in a reference file.",
    )
    p.add_argument("config", help="Config file to prune.")
    p.add_argument("reference", help="Reference file that defines the allowed key set.")
    p.add_argument(
        "-o", "--output",
        default=None,
        help="Write pruned output to this file (default: stdout).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stale keys without modifying anything.",
    )
    return p


def run(args: argparse.Namespace) -> int:
    try:
        data = load_yaml_for_prune(args.config)
        reference = load_yaml_for_prune(args.reference)
    except PruneError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    stale = find_stale_keys(data, reference)

    if args.dry_run:
        if stale:
            print("Stale keys found:")
            for key in stale:
                print(f"  - {key}")
        else:
            print("No stale keys found.")
        return 0

    pruned = prune_keys(data, stale)
    output = dump_pruned(pruned)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Pruned config written to {args.output}")
    else:
        print(output, end="")

    return 0
