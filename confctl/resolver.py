"""Resolve variable references within config files, supporting ${var} interpolation."""

import re
import yaml
from pathlib import Path
from typing import Any

VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


class ResolveError(Exception):
    """Raised when variable resolution fails."""


def load_yaml_for_resolve(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise ResolveError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ResolveError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def _flatten_keys(data: dict, prefix: str = "") -> dict:
    """Flatten a nested dict into dot-separated keys."""
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(_flatten_keys(value, full_key))
        else:
            result[full_key] = value
    return result


def _resolve_value(value: Any, context: dict, path: str, visited: set) -> Any:
    """Recursively resolve ${var} references in a value."""
    if isinstance(value, str):
        def replacer(match):
            var = match.group(1)
            if var in visited:
                raise ResolveError(f"Circular reference detected for variable '{var}' in {path}")
            if var not in context:
                raise ResolveError(f"Undefined variable '{var}' referenced in {path}")
            visited.add(var)
            resolved = _resolve_value(str(context[var]), context, path, visited)
            visited.discard(var)
            return resolved
        return VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_value(v, context, path, visited) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item, context, path, visited) for item in value]
    return value


def resolve_config(data: dict, source_path: str = "<dict>") -> dict:
    """Resolve all ${var} references in a config dict using its own keys as context."""
    context = _flatten_keys(data)
    return {k: _resolve_value(v, context, source_path, set()) for k, v in data.items()}


def resolve_file(path: str) -> dict:
    """Load a YAML config file and resolve all variable references within it."""
    data = load_yaml_for_resolve(path)
    return resolve_config(data, source_path=path)
