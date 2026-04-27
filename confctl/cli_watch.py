"""CLI sub-command: watch config files for changes."""

import argparse
import sys
from pathlib import Path

from confctl.watcher import WatchError, watch


def build_parser(subparsers=None):
    """Build argument parser for the watch sub-command."""
    description = "Watch config files and report changes."
    if subparsers is not None:
        parser = subparsers.add_parser("watch", help=description)
    else:
        parser = argparse.ArgumentParser(prog="confctl watch", description=description)
    parser.add_argument("files", nargs="+", metavar="FILE", help="Files to watch")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N poll cycles (default: run forever)",
    )
    return parser


def _on_change(changes):
    for path, status in sorted(changes.items()):
        print(f"[{status.upper()}] {path}")
    sys.stdout.flush()


def run(args):
    """Entry point for the watch sub-command."""
    for f in args.files:
        if not Path(f).is_file():
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)
    try:
        watch(
            paths=args.files,
            callback=_on_change,
            interval=args.interval,
            max_cycles=args.max_cycles,
        )
    except WatchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
