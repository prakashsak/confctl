"""Validate config files against a schema or basic structural rules."""

from __future__ import annotations

import os
from typing import Any

import yaml


class ValidationError(Exception):
    """Raised when a config file fails validation."""


def load_yaml_for_validation(path: str) -> Any:
    """Load a YAML file and return its parsed content."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_is_mapping(data: Any, path: str) -> None:
    """Ensure the top-level YAML document is a mapping (dict)."""
    if data is not None and not isinstance(data, dict):
        raise ValidationError(
            f"{path}: top-level value must be a mapping, got {type(data).__name__}"
        )


def validate_no_null_keys(data: dict, path: str, _prefix: str = "") -> None:
    """Recursively ensure no key is None."""
    for key, value in data.items():
        full_key = f"{_prefix}.{key}" if _prefix else str(key)
        if key is None:
            raise ValidationError(f"{path}: null key found at '{full_key}'")
        if isinstance(value, dict):
            validate_no_null_keys(value, path, full_key)


def validate_required_keys(data: dict, required: list[str], path: str) -> None:
    """Check that all required top-level keys are present."""
    missing = [k for k in required if k not in (data or {})]
    if missing:
        raise ValidationError(
            f"{path}: missing required keys: {', '.join(missing)}"
        )


def validate_config(path: str, required_keys: list[str] | None = None) -> dict:
    """Run all validations on a config file and return the parsed data."""
    data = load_yaml_for_validation(path)
    validate_is_mapping(data, path)
    if data:
        validate_no_null_keys(data, path)
    if required_keys:
        validate_required_keys(data or {}, required_keys, path)
    return data or {}


def validate_all(paths: list[str], required_keys: list[str] | None = None) -> dict[str, dict]:
    """Validate multiple config files; return mapping of path -> parsed data."""
    results: dict[str, dict] = {}
    errors: list[str] = []
    for p in paths:
        try:
            results[p] = validate_config(p, required_keys)
        except (ValidationError, FileNotFoundError) as exc:
            errors.append(str(exc))
    if errors:
        raise ValidationError("Validation failed:\n" + "\n".join(errors))
    return results
