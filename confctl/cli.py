"""Main entry point for the confctl CLI."""

from __future__ import annotations

import argparse
import sys

from confctl import cli_merge, cli_validate


def build_root_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Manage and diff environment-specific config files.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    cli_merge.build_parser(subparsers)
    cli_validate.build_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the appropriate sub-command."""
    parser = build_root_parser()
    args = parser.parse_args(argv)

    if args.command == "merge":
        return cli_merge.run(args)
    if args.command == "validate":
        return cli_validate.run(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
