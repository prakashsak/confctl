"""Root CLI entry point for confctl."""

import argparse
import sys

from confctl import cli_diff, cli_export, cli_merge, cli_render, cli_validate


def build_root_parser() -> argparse.ArgumentParser:
    """Build and return the root argument parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="confctl",
        description="Manage and diff environment-specific config files.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    cli_diff.build_parser(subparsers)
    cli_merge.build_parser(subparsers)
    cli_validate.build_parser(subparsers)
    cli_export.build_parser(subparsers)
    cli_render.build_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate sub-command."""
    parser = build_root_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "diff": cli_diff.run,
        "merge": cli_merge.run,
        "validate": cli_validate.run,
        "export": cli_export.run,
        "render": cli_render.run,
    }

    if args.command in dispatch:
        try:
            dispatch[args.command](args)
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
