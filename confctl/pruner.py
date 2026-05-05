"""Pruner: remove unused or stale keys from YAML config files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class PruneError(Exception):
    """Raised when pruning fails."""


def load_yaml_for_prune(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise PruneError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PruneError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _flatten(data: dict, prefix: str = "") -> set[str]:
    """Return a flat set of dotted key paths."""
    keys: set[str] = set()
    for k, v in data.items():
        full = f"{prefix}.{k}" if prefix else str(k)
        keys.add(full)
        if isinstance(v, dict):
            keys |= _flatten(v, full)
    return keys


def find_stale_keys(data: dict, reference: dict) -> list[str]:
    """Return keys present in *data* but absent from *reference*."""
    data_keys = _flatten(data)
    ref_keys = _flatten(reference)
    stale = sorted(data_keys - ref_keys)
    return stale


def _remove_key(data: dict, dotted: str) -> bool:
    """Remove a dotted key path from *data* in-place. Returns True if removed."""
    parts = dotted.split(".")
    node = data
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    leaf = parts[-1]
    if isinstance(node, dict) and leaf in node:
        del node[leaf]
        return True
    return False


def prune_keys(data: dict, keys_to_remove: list[str]) -> dict:
    """Remove *keys_to_remove* from *data* and return the pruned dict."""
    import copy
    result = copy.deepcopy(data)
    for key in keys_to_remove:
        _remove_key(result, key)
    return result


def dump_pruned(data: dict) -> str:
    """Serialise *data* back to a YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=True)
