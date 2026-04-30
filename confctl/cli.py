"""Root CLI entry-point for confctl."""

from __future__ import annotations

import argparse
import sys

from confctl import cli_diff
from confctl import cli_merge
from confctl import cli_validate
from confctl import cli_export
from confctl import cli_render
from confctl import cli_lint
from confctl import cli_compare
from confctl import cli_patch
from confctl import cli_encrypt
from confctl import cli_scope
from confctl import cli_schedule
from confctl import cli_watch
from confctl import cli_summarize
from confctl import cli_trace
from confctl import cli_pin


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Manage and diff environment-specific config files.",
    )
    subparsers = parser.add_subparsers(dest="command")

    cli_diff.build_parser(subparsers)
    cli_merge.build_parser(subparsers)
    cli_validate.build_parser(subparsers)
    cli_export.build_parser(subparsers)
    cli_render.build_parser(subparsers)
    cli_lint.build_parser(subparsers)
    cli_compare.build_parser(subparsers)
    cli_patch.build_parser(subparsers)
    cli_encrypt.build_parser(subparsers)
    cli_scope.build_parser(subparsers)
    cli_schedule.build_parser(subparsers)
    cli_watch.build_parser(subparsers)
    cli_summarize.build_parser(subparsers)
    cli_trace.build_parser(subparsers)
    cli_pin.build_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_root_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "diff": cli_diff.run,
        "merge": cli_merge.run,
        "validate": cli_validate.run,
        "export": cli_export.run,
        "render": cli_render.run,
        "lint": cli_lint.run,
        "compare": cli_compare.run,
        "patch": cli_patch.run,
        "encrypt": cli_encrypt.run,
        "scope": cli_scope.run,
        "schedule": cli_schedule.run,
        "watch": cli_watch.run,
        "summarize": cli_summarize.run,
        "trace": cli_trace.run,
        "pin": cli_pin.run,
    }

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
