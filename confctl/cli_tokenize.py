"""CLI sub-command: tokenize — analyse config value tokens."""

from __future__ import annotations

import argparse
import json
import sys

from confctl.tokenizer import TokenizeError, tokenize_config, format_token_summary


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Tokenize config values and display token types."
    if subparsers is not None:
        parser = subparsers.add_parser("tokenize", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="confctl tokenize", description=desc)
    parser.add_argument("files", nargs="+", metavar="FILE", help="YAML config files to tokenize")
    parser.add_argument(
        "--format",
        choices=["summary", "json"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "--key",
        metavar="KEY",
        default=None,
        help="Filter output to a specific dotted key",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    exit_code = 0
    for path in args.files:
        try:
            tokens = tokenize_config(path)
        except TokenizeError as exc:
            print(f"ERROR [{path}]: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        if args.key:
            tokens = {k: v for k, v in tokens.items() if k == args.key or k.startswith(args.key + ".")}

        print(f"=== {path} ===")
        if args.format == "json":
            print(json.dumps(tokens, indent=2))
        else:
            summary = format_token_summary(tokens)
            print(summary if summary else "  (no values found)")

    return exit_code
