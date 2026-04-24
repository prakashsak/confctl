"""Merge environment-specific configs with a base config."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class MergeError(Exception):
    """Raised when config merging fails."""


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise MergeError(f"Expected a YAML mapping at top level in {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into a deep copy of *base*.

    Keys present only in *base* are kept.  Keys present in *override*
    overwrite or extend *base* values.  Nested dicts are merged
    recursively; all other types are replaced.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_configs(
    base_path: Path,
    env_path: Path,
) -> dict[str, Any]:
    """Load *base_path* and *env_path* and return the merged result.

    The environment config takes precedence over the base config.
    """
    base = load_yaml(base_path)
    env = load_yaml(env_path)
    return deep_merge(base, env)


def dump_merged(merged: dict[str, Any], output_path: Path) -> None:
    """Write *merged* dict to *output_path* as YAML."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        yaml.dump(merged, fh, default_flow_style=False, sort_keys=True)
