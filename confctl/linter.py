"""Linter for config files: checks for common style and structure issues."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class LintError(Exception):
    """Raised when a config file fails linting."""


class LintWarning:
    def __init__(self, path: str, line: int | None, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        loc = f":{self.line}" if self.line is not None else ""
        return f"{self.path}{loc}: {self.message}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"LintWarning({self!s})"


def load_yaml_for_lint(path: str) -> tuple[Any, list[str]]:
    """Load YAML and return (parsed_data, raw_lines). Raises LintError on failure."""
    p = Path(path)
    if not p.exists():
        raise LintError(f"File not found: {path}")
    raw = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise LintError(f"YAML parse error in {path}: {exc}") from exc
    return data, raw.splitlines()


def check_trailing_whitespace(lines: list[str], path: str) -> list[LintWarning]:
    """Warn about lines with trailing whitespace."""
    warnings: list[LintWarning] = []
    for i, line in enumerate(lines, start=1):
        if line != line.rstrip():
            warnings.append(LintWarning(path, i, "trailing whitespace"))
    return warnings


def check_duplicate_keys(lines: list[str], path: str) -> list[LintWarning]:
    """Warn about duplicate top-level keys (simple heuristic)."""
    warnings: list[LintWarning] = []
    seen: dict[str, int] = {}
    key_re = re.compile(r'^([A-Za-z0-9_\-\.]+)\s*:')
    for i, line in enumerate(lines, start=1):
        m = key_re.match(line)
        if m:
            key = m.group(1)
            if key in seen:
                warnings.append(
                    LintWarning(path, i, f"duplicate key '{key}' (first seen at line {seen[key]})")
                )
            else:
                seen[key] = i
    return warnings


def check_empty_values(data: Any, path: str) -> list[LintWarning]:
    """Warn about keys with null/None values in a mapping."""
    warnings: list[LintWarning] = []
    if not isinstance(data, dict):
        return warnings
    for key, value in data.items():
        if value is None:
            warnings.append(LintWarning(path, None, f"key '{key}' has a null value"))
    return warnings


def lint_config(path: str) -> list[LintWarning]:
    """Run all lint checks on a config file and return a list of warnings."""
    data, lines = load_yaml_for_lint(path)
    warnings: list[LintWarning] = []
    warnings.extend(check_trailing_whitespace(lines, path))
    warnings.extend(check_duplicate_keys(lines, path))
    warnings.extend(check_empty_values(data, path))
    return warnings
