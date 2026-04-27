"""Root CLI entry point for confctl."""

import argparse
import sys

from confctl import cli_merge, cli_validate, cli_diff, cli_export
from confctl import cli_render, cli_lint, cli_compare, cli_patch
from confctl import cli_encrypt, cli_scope, cli_schedule, cli_audit
from confctl import cli_snapshot, cli_watch


def build_root_parser():
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Lightweight CLI for managing environment-specific config files.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    cli_merge.build_parser(sub)
    cli_validate.build_parser(sub)
    cli_diff.build_parser(sub)
    cli_export.build_parser(sub)
    cli_render.build_parser(sub)
    cli_lint.build_parser(sub)
    cli_compare.build_parser(sub)
    cli_patch.build_parser(sub)
    cli_encrypt.build_parser(sub)
    cli_scope.build_parser(sub)
    cli_schedule.build_parser(sub)
    cli_audit.build_parser(sub)
    cli_snapshot.build_parser(sub)
    cli_watch.build_parser(sub)

    return parser


_RUNNERS = {
    "merge": cli_merge.run,
    "validate": cli_validate.run,
    "diff": cli_diff.run,
    "export": cli_export.run,
    "render": cli_render.run,
    "lint": cli_lint.run,
    "compare": cli_compare.run,
    "patch": cli_patch.run,
    "encrypt": cli_encrypt.run,
    "scope": cli_scope.run,
    "schedule": cli_schedule.run,
    "audit": cli_audit.run,
    "snapshot": cli_snapshot.run,
    "watch": cli_watch.run,
}


def main(argv=None):
    parser = build_root_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    runner = _RUNNERS.get(args.command)
    if runner is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)
    runner(args)


if __name__ == "__main__":
    main()
