"""CLI sub-command for pinning and verifying config file hashes."""

from __future__ import annotations

import argparse
import sys

from confctl.pinner import (
    PinError,
    create_pin,
    format_verify_summary,
    load_pin,
    save_pin,
    verify_pin,
)


def build_parser(subparsers: argparse.Action) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("pin", help="Pin or verify config file hashes.")
    sub = p.add_subparsers(dest="pin_cmd", required=True)

    create_p = sub.add_parser("create", help="Create a pin file from config files.")
    create_p.add_argument("files", nargs="+", help="Config files to pin.")
    create_p.add_argument(
        "--output", "-o", required=True, help="Path to write the pin JSON file."
    )

    verify_p = sub.add_parser("verify", help="Verify config files against a pin file.")
    verify_p.add_argument("pin_file", help="Path to an existing pin JSON file.")
    verify_p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if any file has changed.",
    )

    return p


def run(args: argparse.Namespace) -> None:
    try:
        if args.pin_cmd == "create":
            pin = create_pin(args.files)
            save_pin(pin, args.output)
            print(f"Pinned {len(pin)} file(s) to {args.output}")

        elif args.pin_cmd == "verify":
            pin = load_pin(args.pin_file)
            results = verify_pin(pin)
            summary = format_verify_summary(results)
            print(summary)
            if args.exit_code and not all(results.values()):
                sys.exit(1)

    except PinError as exc:
        print(f"pin error: {exc}", file=sys.stderr)
        sys.exit(1)
