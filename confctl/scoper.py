"""Scoper: filter config keys by scope/prefix for environment-specific views."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


class ScopeError(Exception):
    pass


def load_yaml_for_scope(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise ScopeError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ScopeError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _flatten(data: dict, prefix: str = "", sep: str = ".") -> dict:
    """Recursively flatten nested dict into dot-separated keys."""
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(_flatten(value, full_key, sep))
        else:
            result[full_key] = value
    return result


def filter_by_scope(data: dict, scope: str, sep: str = ".") -> dict:
    """Return only keys that start with the given scope prefix."""
    if not scope:
        raise ScopeError("Scope prefix must not be empty")
    flat = _flatten(data, sep=sep)
    prefix = scope if scope.endswith(sep) else scope + sep
    filtered = {
        key[len(prefix):]: value
        for key, value in flat.items()
        if key.startswith(prefix) or key == scope
    }
    return filtered


def scope_config(path: str, scope: str) -> dict:
    """Load a YAML config file and return keys filtered to the given scope."""
    data = load_yaml_for_scope(path)
    return filter_by_scope(data, scope)


def format_scoped(data: dict, fmt: str = "yaml") -> str:
    """Format a scoped dict as yaml or env."""
    if fmt == "yaml":
        return yaml.dump(data, default_flow_style=False) if data else ""
    elif fmt == "env":
        lines = []
        for key, value in sorted(data.items()):
            safe_key = key.upper().replace(".", "_").replace("-", "_")
            lines.append(f"{safe_key}={value}")
        return "\n".join(lines)
    else:
        raise ScopeError(f"Unknown format: {fmt}")
