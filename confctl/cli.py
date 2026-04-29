"""Root CLI entry-point for confctl."""

from __future__ import annotations

import argparse
import sys

from confctl import (
    cli_audit,
    cli_compare,
    cli_diff,
    cli_encrypt,
    cli_export,
    cli_lint,
    cli_merge,
    cli_patch,
    cli_render,
    cli_schedule,
    cli_scope,
    cli_snapshot,
    cli_summarize,
    cli_trace,
    cli_validate,
    cli_watch,
)


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Lightweight CLI tool for managing environment-specific config files.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    cli_diff.build_parser(sub)
    cli_merge.build_parser(sub)
    cli_validate.build_parser(sub)
    cli_export.build_parser(sub)
    cli_render.build_parser(sub)
    cli_lint.build_parser(sub)
    cli_snapshot.build_parser(sub)
    cli_audit.build_parser(sub)
    cli_compare.build_parser(sub)
    cli_patch.build_parser(sub)
    cli_encrypt.build_parser(sub)
    cli_scope.build_parser(sub)
    cli_schedule.build_parser(sub)
    cli_watch.build_parser(sub)
    cli_summarize.build_parser(sub)
    cli_trace.build_parser(sub)

    return parser


_RUNNERS = {
    "diff": cli_diff.run,
    "merge": cli_merge.run,
    "validate": cli_validate.run,
    "export": cli_export.run,
    "render": cli_render.run,
    "lint": cli_lint.run,
    "snapshot": cli_snapshot.run,
    "audit": cli_audit.run,
    "compare": cli_compare.run,
    "patch": cli_patch.run,
    "encrypt": cli_encrypt.run,
    "scope": cli_scope.run,
    "schedule": cli_schedule.run,
    "watch": cli_watch.run,
    "summarize": cli_summarize.run,
    "trace": cli_trace.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_root_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    runner = _RUNNERS.get(args.command)
    if runner is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1
    return runner(args)


if __name__ == "__main__":
    sys.exit(main())
