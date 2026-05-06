"""Integration shim to register the 'tokenize' sub-command with the root CLI."""

from __future__ import annotations

from confctl.cli_tokenize import build_parser, run


def register(subparsers) -> None:
    """Register the tokenize sub-command onto *subparsers*."""
    parser = build_parser(subparsers)
    parser.set_defaults(func=run)
