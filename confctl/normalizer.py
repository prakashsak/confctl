"""Normalize config keys: strip whitespace, lowercase, replace hyphens with underscores."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class NormalizeError(Exception):
    """Raised when normalization fails."""


def load_yaml_for_normalize(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise NormalizeError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise NormalizeError(f"Expected a YAML mapping, got {type(data).__name__}: {path}")
    return data


def _normalize_key(key: Any) -> str:
    """Normalize a single key to a clean snake_case string."""
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def normalize_keys(data: dict) -> dict:
    """Recursively normalize all keys in a nested dict."""
    result: dict = {}
    for k, v in data.items():
        normalized = _normalize_key(k)
        if isinstance(v, dict):
            result[normalized] = normalize_keys(v)
        else:
            result[normalized] = v
    return result


def dump_normalized(data: dict) -> str:
    """Serialize a normalized dict back to a YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=True)


def normalize_config(path: str) -> dict:
    """Load a YAML config file and return a normalized dict."""
    raw = load_yaml_for_normalize(path)
    return normalize_keys(raw)
