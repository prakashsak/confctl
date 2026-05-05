"""CLI subcommand: confctl migrate"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from confctl.migrator import (
    MigrateError,
    dump_migrated,
    load_migration_rules,
    load_yaml_for_migrate,
    migrate_config,
)


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "migrate",
        help="Apply versioned migration rules to a config file",
    )
    p.add_argument("config", help="Path to the config file to migrate")
    p.add_argument("rules", help="Path to the YAML migration rules file")
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write migrated config to this file (default: stdout)",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the original config file with the migrated result",
    )
    return p


def run(args: argparse.Namespace) -> int:
    try:
        data = load_yaml_for_migrate(args.config)
        rules = load_migration_rules(args.rules)
        migrated = migrate_config(data, rules)
        output = dump_migrated(migrated)
    except MigrateError as exc:
        print(f"migrate error: {exc}", file=sys.stderr)
        return 1

    if args.in_place:
        Path(args.config).write_text(output)
        print(f"Migrated config written to {args.config}")
    elif args.output:
        Path(args.output).write_text(output)
        print(f"Migrated config written to {args.output}")
    else:
        print(output, end="")

    return 0
