"""Trace config key origins across multiple files."""

from __future__ import annotations

import os
from typing import Any

import yaml


class TraceError(Exception):
    pass


def load_yaml_for_trace(path: str) -> dict:
    if not os.path.exists(path):
        raise TraceError(f"File not found: {path}")
    with open(path, "r") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TraceError(f"Expected a YAML mapping in {path}")
    return data


def _flatten(data: dict, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dict into dot-separated keys."""
    result = {}
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            result.update(_flatten(v, full_key))
        else:
            result[full_key] = v
    return result


def trace_key(key: str, files: list[str]) -> list[dict]:
    """Return a list of origin records for a given key across files."""
    origins = []
    for path in files:
        data = load_yaml_for_trace(path)
        flat = _flatten(data)
        if key in flat:
            origins.append({"file": path, "key": key, "value": flat[key]})
    return origins


def trace_all_keys(files: list[str]) -> dict[str, list[dict]]:
    """Map every key to the list of files that define it."""
    index: dict[str, list[dict]] = {}
    for path in files:
        data = load_yaml_for_trace(path)
        flat = _flatten(data)
        for key, value in flat.items():
            index.setdefault(key, [])
            index[key].append({"file": path, "value": value})
    return index


def format_trace(origins: list[dict]) -> str:
    """Format a list of origin records into a human-readable string."""
    if not origins:
        return "(no origins found)"
    lines = []
    for record in origins:
        lines.append(f"  {record['file']}: {record['value']!r}")
    return "\n".join(lines)
