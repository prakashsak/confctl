"""CLI sub-commands: encrypt and decrypt config values."""

import argparse
import sys
from pathlib import Path

import yaml

from confctl.encryptor import EncryptError, decrypt_config, encrypt_config


def build_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Encrypt/decrypt config values")
        sub = parser.add_subparsers(dest="encmode")
    else:
        parser = subparsers.add_parser("encrypt", help="Encrypt or decrypt config values")
        sub = parser.add_subparsers(dest="encmode")

    enc = sub.add_parser("encrypt", help="Encrypt values in a config file")
    enc.add_argument("file", type=Path, help="YAML config file")
    enc.add_argument("--secret", required=True, help="Encryption secret")
    enc.add_argument(
        "--keys", nargs="+", metavar="KEY", help="Specific keys to encrypt (default: all)"
    )
    enc.add_argument("--output", "-o", type=Path, default=None, help="Output file (default: stdout)")

    dec = sub.add_parser("decrypt", help="Decrypt ENC:-prefixed values in a config file")
    dec.add_argument("file", type=Path, help="YAML config file")
    dec.add_argument("--secret", required=True, help="Encryption secret")
    dec.add_argument("--output", "-o", type=Path, default=None, help="Output file (default: stdout)")

    return parser


def run(args):
    if args.encmode == "encrypt":
        try:
            result = encrypt_config(args.file, args.secret, keys=getattr(args, "keys", None))
        except (EncryptError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.encmode == "decrypt":
        try:
            result = decrypt_config(args.file, args.secret)
        except (EncryptError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Specify a sub-command: encrypt or decrypt", file=sys.stderr)
        sys.exit(1)

    output = yaml.dump(result, default_flow_style=False, sort_keys=True)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
