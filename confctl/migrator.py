"""Migrate config files by applying versioned transformation rules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class MigrateError(Exception):
    pass


def load_yaml_for_migrate(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise MigrateError(f"File not found: {path}")
    text = p.read_text()
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise MigrateError(f"Expected a YAML mapping in {path}")
    return data


def load_migration_rules(rules_path: str) -> list[dict[str, Any]]:
    """Load an ordered list of migration rules from a YAML file."""
    p = Path(rules_path)
    if not p.exists():
        raise MigrateError(f"Rules file not found: {rules_path}")
    data = yaml.safe_load(p.read_text())
    if data is None:
        return []
    if not isinstance(data, list):
        raise MigrateError("Migration rules must be a YAML list")
    return data


def _apply_rule(data: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    """Apply a single migration rule (rename, delete, set_default) to data."""
    action = rule.get("action")
    if action == "rename":
        old = rule.get("from")
        new = rule.get("to")
        if old in data:
            data[new] = data.pop(old)
    elif action == "delete":
        key = rule.get("key")
        data.pop(key, None)
    elif action == "set_default":
        key = rule.get("key")
        value = rule.get("value")
        data.setdefault(key, value)
    else:
        raise MigrateError(f"Unknown migration action: {action!r}")
    return data


def migrate_config(
    data: dict[str, Any], rules: list[dict[str, Any]]
) -> dict[str, Any]:
    """Apply all rules sequentially to a config dict."""
    import copy
    result = copy.deepcopy(data)
    for rule in rules:
        result = _apply_rule(result, rule)
    return result


def dump_migrated(data: dict[str, Any]) -> str:
    """Serialize migrated config to YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
