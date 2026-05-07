"""Redactor: mask sensitive values in config files before display or export."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api_key", re.IGNORECASE),
    re.compile(r"private_key", re.IGNORECASE),
]

REDACT_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    """Raised when redaction fails."""


def load_yaml_for_redact(path: str) -> dict:
    """Load a YAML file and return its contents as a dict."""
    p = Path(path)
    if not p.exists():
        raise RedactError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RedactError(f"Expected a YAML mapping at top level: {path}")
    return data


def _is_sensitive(key: str, patterns: list[re.Pattern]) -> bool:
    """Return True if *key* matches any sensitive pattern."""
    return any(p.search(key) for p in patterns)


def _walk_and_redact(
    data: Any,
    patterns: list[re.Pattern],
    placeholder: str,
) -> Any:
    """Recursively walk *data* and replace sensitive leaf values."""
    if isinstance(data, dict):
        return {
            k: (placeholder if _is_sensitive(str(k), patterns) else _walk_and_redact(v, patterns, placeholder))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_walk_and_redact(item, patterns, placeholder) for item in data]
    return data


def redact_config(
    data: dict,
    extra_patterns: list[str] | None = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> dict:
    """Return a copy of *data* with sensitive values replaced by *placeholder*.

    Args:
        data: Parsed YAML mapping.
        extra_patterns: Additional regex patterns (as strings) to treat as sensitive.
        placeholder: Replacement string for redacted values.
    """
    patterns = list(DEFAULT_PATTERNS)
    for raw in extra_patterns or []:
        try:
            patterns.append(re.compile(raw, re.IGNORECASE))
        except re.error as exc:
            raise RedactError(f"Invalid pattern {raw!r}: {exc}") from exc
    return _walk_and_redact(data, patterns, placeholder)


def dump_redacted(data: dict) -> str:
    """Serialize *data* to a YAML string."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
