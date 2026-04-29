"""Summarize config files: key count, depth, null values, and top-level sections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SummaryError(Exception):
    pass


def load_yaml_for_summary(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise SummaryError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SummaryError(f"Expected a YAML mapping in {path}")
    return data


def _walk(obj: Any, depth: int = 0) -> list[tuple[str, Any, int]]:
    """Recursively yield (dotted_key, value, depth) tuples."""
    results: list[tuple[str, Any, int]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            results.append((str(k), v, depth))
            results.extend(_walk(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_walk(item, depth + 1))
    return results


def summarize(data: dict) -> dict:
    """Return a summary dict describing the config structure."""
    entries = _walk(data)
    all_values = [v for _, v, _ in entries if not isinstance(v, (dict, list))]
    null_count = sum(1 for v in all_values if v is None)
    max_depth = max((d for _, _, d in entries), default=0)
    top_level_keys = list(data.keys())
    return {
        "total_keys": len(entries),
        "scalar_values": len(all_values),
        "null_values": null_count,
        "max_depth": max_depth,
        "top_level_sections": top_level_keys,
        "top_level_count": len(top_level_keys),
    }


def format_summary(path: str, summary: dict) -> str:
    """Format a summary dict into a human-readable string."""
    lines = [f"Summary for: {path}"]
    lines.append(f"  Top-level sections ({summary['top_level_count']}): {', '.join(summary['top_level_sections']) or '(none)'}")
    lines.append(f"  Total keys   : {summary['total_keys']}")
    lines.append(f"  Scalar values: {summary['scalar_values']}")
    lines.append(f"  Null values  : {summary['null_values']}")
    lines.append(f"  Max depth    : {summary['max_depth']}")
    return "\n".join(lines)
