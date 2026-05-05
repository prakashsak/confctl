"""Rename keys across YAML config files using a mapping of old->new key paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class RenameError(Exception):
    pass


def load_yaml_for_rename(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise RenameError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RenameError(f"Expected a YAML mapping in {path}")
    return data


def _get_nested(data: dict, key_path: str) -> tuple[dict, str]:
    """Return (parent_dict, final_key) for a dot-separated key path."""
    parts = key_path.split(".")
    current = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise RenameError(f"Key path not found: {key_path}")
        current = current[part]
    return current, parts[-1]


def rename_key(data: dict, old_path: str, new_path: str) -> dict:
    """Rename a key at old_path to new_path within data (in-place, returns data)."""
    old_parent, old_key = _get_nested(data, old_path)
    if old_key not in old_parent:
        raise RenameError(f"Key not found: {old_path}")

    new_parts = new_path.split(".")
    new_parent = data
    for part in new_parts[:-1]:
        new_parent = new_parent.setdefault(part, {})
    new_key = new_parts[-1]

    if new_key in new_parent:
        raise RenameError(f"Target key already exists: {new_path}")

    new_parent[new_key] = old_parent.pop(old_key)
    return data


def apply_renames(data: dict, renames: dict[str, str]) -> dict:
    """Apply multiple renames given as {old_path: new_path}."""
    for old_path, new_path in renames.items():
        rename_key(data, old_path, new_path)
    return data


def dump_renamed(data: dict) -> str:
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
