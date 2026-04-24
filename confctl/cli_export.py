"""CLI sub-command: confctl export — export a config file to json/yaml/env."""

import argparse
import sys

from confctl.exporter import ExportError, export_config, write_export
from confctl.merger import MergeError, load_yaml


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    """Register (or create standalone) the *export* sub-command parser."""
    description = "Export a YAML config file to json, yaml, or env format."
    if subparsers is not None:
        parser = subparsers.add_parser("export", help=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl export", description=description)

    parser.add_argument("file", help="Path to the YAML config file to export.")
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        default="json",
        choices=["json", "yaml", "env"],
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the export command; return exit code."""
    try:
        data = load_yaml(args.file)
    except (MergeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        content = export_config(data, args.fmt)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        try:
            write_export(content, args.output)
            print(f"Exported to {args.output}")
        except OSError as exc:
            print(f"error: could not write file: {exc}", file=sys.stderr)
            return 1
    else:
        print(content, end="" if content.endswith("\n") else "\n")

    return 0
