"""CLI subcommand: confctl rename — rename keys in YAML config files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from confctl.renamer import RenameError, apply_renames, dump_renamed, load_yaml_for_rename


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "rename",
        help="Rename keys in a YAML config file",
    )
    p.add_argument("file", help="YAML config file to modify")
    p.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        dest="renames",
        required=True,
        help="Key rename in old.path=new.path format (repeatable)",
    )
    p.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of stdout",
    )
    p.add_argument(
        "--in-place", "-i",
        action="store_true",
        default=False,
        help="Overwrite the input file",
    )
    return p


def _parse_renames(raw: list[str]) -> dict[str, str]:
    result = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid rename spec (expected OLD=NEW): {item!r}")
        old, new = item.split("=", 1)
        result[old.strip()] = new.strip()
    return result


def run(args: argparse.Namespace) -> int:
    try:
        renames = _parse_renames(args.renames)
        data = load_yaml_for_rename(args.file)
        apply_renames(data, renames)
        output = dump_renamed(data)
    except (RenameError, ValueError) as exc:
        print(f"rename error: {exc}", file=sys.stderr)
        return 1

    if args.in_place:
        Path(args.file).write_text(output)
    elif args.output:
        Path(args.output).write_text(output)
    else:
        print(output, end="")
    return 0
