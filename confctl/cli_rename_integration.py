"""Integration helper: register the rename subcommand in the root CLI.

This module is imported by confctl/cli.py to wire up the rename command.
It follows the same pattern used by cli_merge, cli_diff, etc.
"""

from __future__ import annotations

import argparse

from confctl import cli_rename


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the rename subcommand onto *subparsers*."""
    cli_rename.build_parser(subparsers)


__all__ = ["register"]
