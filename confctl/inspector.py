"""Inspector: report key statistics and structure overview of a config file."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


class InspectError(Exception):
    pass


def load_yaml_for_inspect(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise InspectError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise InspectError(f"YAML parse error in {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise InspectError(f"Expected a YAML mapping in {path}")
    return data


def _walk(data: Any, depth: int = 0) -> list[tuple[str, Any, int]]:
    """Yield (key_path, value, depth) for every leaf."""
    results: list[tuple[str, Any, int]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                results.extend(_walk(v, depth + 1))
            else:
                results.append((str(k), v, depth))
    elif isinstance(data, list):
        for item in data:
            results.extend(_walk(item, depth))
    else:
        results.append(("", data, depth))
    return results


def _count_keys(data: Any) -> int:
    count = 0
    if isinstance(data, dict):
        for v in data.values():
            count += 1 + _count_keys(v)
    elif isinstance(data, list):
        for item in data:
            count += _count_keys(item)
    return count


def _max_depth(data: Any, current: int = 0) -> int:
    if isinstance(data, dict):
        if not data:
            return current
        return max(_max_depth(v, current + 1) for v in data.values())
    if isinstance(data, list):
        if not data:
            return current
        return max(_max_depth(item, current) for item in data)
    return current


def inspect_config(path: str) -> dict:
    """Return an inspection report dict for the given YAML config file."""
    data = load_yaml_for_inspect(path)
    total_keys = _count_keys(data)
    depth = _max_depth(data)
    null_keys = [k for k, v, _ in _walk(data) if v is None]
    top_level_keys = list(data.keys())
    value_types: dict[str, int] = {}
    for _, v, _ in _walk(data):
        t = type(v).__name__
        value_types[t] = value_types.get(t, 0) + 1
    return {
        "path": path,
        "top_level_keys": top_level_keys,
        "total_keys": total_keys,
        "max_depth": depth,
        "null_keys": null_keys,
        "value_types": value_types,
    }


def format_inspection(report: dict) -> str:
    lines = [
        f"File       : {report['path']}",
        f"Top-level  : {', '.join(report['top_level_keys']) or '(none)'}",
        f"Total keys : {report['total_keys']}",
        f"Max depth  : {report['max_depth']}",
        f"Null keys  : {', '.join(report['null_keys']) or 'none'}",
        "Value types:",
    ]
    for t, count in sorted(report["value_types"].items()):
        lines.append(f"  {t}: {count}")
    return "\n".join(lines)
