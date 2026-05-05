"""Sort keys in YAML config files alphabetically or by custom order."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SortError(Exception):
    """Raised when sorting fails."""


def load_yaml_for_sort(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise SortError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SortError(f"Invalid YAML in {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SortError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _sort_recursive(data: Any, reverse: bool = False) -> Any:
    """Recursively sort dict keys; leave other types untouched."""
    if isinstance(data, dict):
        return {
            k: _sort_recursive(v, reverse=reverse)
            for k in sorted(data.keys(), key=str, reverse=reverse)
        }
    if isinstance(data, list):
        return [_sort_recursive(item, reverse=reverse) for item in data]
    return data


def sort_config(data: dict, reverse: bool = False) -> dict:
    """Return a new dict with all keys sorted recursively."""
    if not isinstance(data, dict):
        raise SortError("sort_config requires a dict")
    return _sort_recursive(data, reverse=reverse)


def dump_sorted(data: dict) -> str:
    """Dump a sorted dict to a YAML string."""
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def sort_file(path: str, reverse: bool = False, output: str | None = None) -> str:
    """Load, sort, and optionally write a YAML config file.

    Returns the sorted YAML string.
    """
    data = load_yaml_for_sort(path)
    sorted_data = sort_config(data, reverse=reverse)
    result = dump_sorted(sorted_data)
    dest = output or path
    Path(dest).write_text(result, encoding="utf-8")
    return result
