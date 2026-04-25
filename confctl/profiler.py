"""Profile comparison: summarize differences between two config environments."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


class ProfileError(Exception):
    """Raised when profile comparison cannot be completed."""


def load_yaml_profile(path: str) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise ProfileError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProfileError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _all_keys(*dicts: dict[str, Any]) -> set[str]:
    """Return union of all top-level keys across provided dicts."""
    keys: set[str] = set()
    for d in dicts:
        keys.update(d.keys())
    return keys


def compare_profiles(
    base: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    """Compare two config profiles and return a structured diff summary.

    Returns a dict with keys:
      - added:    keys present in target but not base
      - removed:  keys present in base but not target
      - changed:  keys whose values differ between base and target
      - unchanged: keys with identical values
    """
    all_keys = _all_keys(base, target)
    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    changed: dict[str, tuple[Any, Any]] = {}
    unchanged: list[str] = []

    for key in sorted(all_keys):
        in_base = key in base
        in_target = key in target
        if in_base and not in_target:
            removed[key] = base[key]
        elif in_target and not in_base:
            added[key] = target[key]
        elif base[key] != target[key]:
            changed[key] = (base[key], target[key])
        else:
            unchanged.append(key)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def format_profile_summary(summary: dict[str, Any], *, color: bool = True) -> str:
    """Render a human-readable profile comparison summary."""
    lines: list[str] = []

    def _c(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if color else text

    for key, val in summary["added"].items():
        lines.append(_c(f"  + {key}: {val}", "32"))
    for key, val in summary["removed"].items():
        lines.append(_c(f"  - {key}: {val}", "31"))
    for key, (old, new) in summary["changed"].items():
        lines.append(_c(f"  ~ {key}: {old!r} -> {new!r}", "33"))
    for key in summary["unchanged"]:
        lines.append(f"    {key}: (unchanged)")

    if not lines:
        return "No differences found."
    return "\n".join(lines)
