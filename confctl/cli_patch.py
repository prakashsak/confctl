"""CLI sub-command: patch — apply key-value overrides to a config file."""

from __future__ import annotations

import argparse
import sys

from confctl.patcher import PatchError, patch_config


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *patch* sub-command."""
    p = subparsers.add_parser(
        "patch",
        help="Apply key=value patches to a YAML config file.",
    )
    p.add_argument("file", help="Path to the YAML config file to patch.")
    p.add_argument(
        "--set",
        metavar="KEY=VALUE",
        dest="patches",
        action="append",
        default=[],
        help="Dotted key=value pair to set (repeatable).",
    )
    p.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Write patched output to FILE instead of stdout.",
    )
    return p


def _parse_patches(raw: list[str]) -> dict:
    """Parse a list of ``KEY=VALUE`` strings into a dict."""
    patches: dict = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid patch spec (expected KEY=VALUE): {item!r}")
        key, _, value = item.partition("=")
        patches[key.strip()] = value
    return patches


def run(args: argparse.Namespace) -> int:
    """Execute the patch sub-command. Returns an exit code."""
    try:
        patches = _parse_patches(args.patches)
        result = patch_config(args.file, patches, output=args.output)
        if not args.output:
            sys.stdout.write(result)
        return 0
    except (PatchError, ValueError) as exc:
        print(f"patch error: {exc}", file=sys.stderr)
        return 1
