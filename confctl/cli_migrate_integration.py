"""Integration hook to register the migrate subcommand with the root CLI."""

from __future__ import annotations

import argparse

from confctl.cli_migrate import build_parser, run


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the migrate subcommand and bind its run handler."""
    p = build_parser(subparsers)
    p.set_defaults(func=run)
