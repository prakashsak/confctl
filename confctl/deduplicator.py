"""Deduplicator: detect and report duplicate keys across YAML config files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class DeduplicateError(Exception):
    """Raised when deduplication cannot be performed."""


def load_yaml_for_dedup(path: str) -> Dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise DeduplicateError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise DeduplicateError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _flatten(data: Dict, prefix: str = "") -> List[str]:
    """Recursively flatten dict keys into dotted paths."""
    keys: List[str] = []
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else str(k)
        keys.append(full_key)
        if isinstance(v, dict):
            keys.extend(_flatten(v, full_key))
    return keys


def find_duplicates(files: List[str]) -> Dict[str, List[str]]:
    """Return keys that appear in more than one file.

    Returns a dict mapping each duplicate key to the list of files it appears in.
    """
    if not files:
        raise DeduplicateError("No files provided for deduplication.")

    key_sources: Dict[str, List[str]] = {}
    for path in files:
        data = load_yaml_for_dedup(path)
        for key in _flatten(data):
            key_sources.setdefault(key, []).append(path)

    return {k: v for k, v in key_sources.items() if len(v) > 1}


def format_duplicates(duplicates: Dict[str, List[str]]) -> str:
    """Format duplicate key report as a human-readable string."""
    if not duplicates:
        return "No duplicate keys found."
    lines: List[str] = ["Duplicate keys detected:"]
    for key, sources in sorted(duplicates.items()):
        lines.append(f"  {key}:")
        for src in sources:
            lines.append(f"    - {src}")
    return "\n".join(lines)
