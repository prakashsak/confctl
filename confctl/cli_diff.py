"""CLI subcommand for diffing environment-specific config files."""

import argparse
import sys

from confctl.differ import diff_configs


def build_parser(subparsers=None):
    """Build the argument parser for the diff subcommand."""
    if subparsers is None:
        parser = argparse.ArgumentParser(
            prog="confctl diff",
            description="Diff two environment config files.",
        )
    else:
        parser = subparsers.add_parser(
            "diff",
            help="Diff two environment config files.",
        )

    parser.add_argument("file_a", help="First config file (baseline).")
    parser.add_argument("file_b", help="Second config file (target).")
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colorized output.",
    )
    parser.add_argument(
        "--label-a",
        default=None,
        help="Override label for the first file in diff header.",
    )
    parser.add_argument(
        "--label-b",
        default=None,
        help="Override label for the second file in diff header.",
    )
    return parser


def run(args, stdout=None):
    """Execute the diff subcommand.

    Returns 0 if the files are identical, 1 if they differ, or 2 if an
    error occurs (e.g. a file is not found or cannot be read).
    """
    if stdout is None:
        stdout = sys.stdout

    label_a = args.label_a or args.file_a
    label_b = args.label_b or args.file_b

    try:
        output = diff_configs(
            args.file_a,
            args.file_b,
            label_a=label_a,
            label_b=label_b,
            colorize=not args.no_color,
        )
    except FileNotFoundError as exc:
        sys.stderr.write(f"confctl diff: error: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"confctl diff: error reading file: {exc}\n")
        return 2

    if output:
        stdout.write(output)
        stdout.write("\n")
        return 1

    stdout.write("Files are identical.\n")
    return 0
