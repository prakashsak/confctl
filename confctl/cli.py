"""Root CLI entry point for confctl."""

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


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Lightweight CLI tool for managing environment-specific config files.",
    )
    sub = parser.add_subparsers(dest="command")

    cli_diff.build_parser(sub)
    cli_merge.build_parser(sub)
    cli_validate.build_parser(sub)
    cli_export.build_parser(sub)
    cli_render.build_parser(sub)
    cli_lint.build_parser(sub)
    cli_compare.build_parser(sub)
    cli_patch.build_parser(sub)
    cli_encrypt.build_parser(sub)
    cli_scope.build_parser(sub)
    cli_schedule.build_parser(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_root_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

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
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
