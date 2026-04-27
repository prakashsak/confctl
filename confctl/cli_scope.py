"""CLI interface for the scope subcommand."""

from __future__ import annotations

import argparse
import sys

from confctl.scoper import scope_config, format_scoped, ScopeError


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Filter config keys by scope prefix"
    if subparsers is not None:
        parser = subparsers.add_parser("scope", help=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl scope", description=description)

    parser.add_argument("file", help="YAML config file to scope")
    parser.add_argument("scope", help="Dot-separated scope prefix (e.g. 'database' or 'app.server')")
    parser.add_argument(
        "--format",
        choices=["yaml", "env"],
        default="yaml",
        dest="fmt",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to file instead of stdout",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        scoped = scope_config(args.file, args.scope)
    except ScopeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not scoped:
        print(f"Warning: no keys found under scope '{args.scope}'", file=sys.stderr)

    try:
        output = format_scoped(scoped, fmt=args.fmt)
    except ScopeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output)
            if output and not output.endswith("\n"):
                fh.write("\n")
    else:
        print(output, end="" if output.endswith("\n") else "\n")

    return 0
