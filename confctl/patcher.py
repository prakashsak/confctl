"""Apply key-value patches to YAML config files."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class PatchError(Exception):
    """Raised when a patch operation fails."""


def load_yaml_for_patch(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise PatchError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PatchError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def apply_patch(data: dict, patches: dict[str, Any]) -> dict:
    """Return a new dict with dotted-key patches applied.

    Supports nested keys via dot notation, e.g. ``"database.host"``.
    """
    result = copy.deepcopy(data)
    for dotted_key, value in patches.items():
        keys = dotted_key.split(".")
        node = result
        for part in keys[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[keys[-1]] = value
    return result


def dump_patched(data: dict) -> str:
    """Serialise *data* back to a YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def patch_config(path: str, patches: dict[str, Any], output: str | None = None) -> str:
    """Load *path*, apply *patches*, write to *output* (or stdout string).

    Returns the resulting YAML string.
    """
    data = load_yaml_for_patch(path)
    patched = apply_patch(data, patches)
    result = dump_patched(patched)
    if output:
        Path(output).write_text(result, encoding="utf-8")
    return result
