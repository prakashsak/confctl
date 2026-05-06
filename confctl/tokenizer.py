"""Tokenizer: split config values into typed tokens for analysis."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


class TokenizeError(Exception):
    pass


TOKEN_PATTERNS = [
    ("ENV_VAR", r"\$\{[^}]+\}|\$[A-Z_][A-Z0-9_]*"),
    ("PLACEHOLDER", r"<[^>]+>"),
    ("URL", r"https?://[^\s]+"),
    ("PATH", r"(?:/[\w.\-]+){2,}"),
    ("NUMBER", r"\b\d+(?:\.\d+)?\b"),
    ("BOOL", r"\b(?:true|false|yes|no)\b"),
    ("WORD", r"[\w.\-]+"),
]

_COMPILED = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in TOKEN_PATTERNS]


def load_yaml_for_tokenize(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise TokenizeError(f"File not found: {path}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TokenizeError(f"Expected mapping, got {type(data).__name__}: {path}")
    return data


def tokenize_value(value: str) -> list[dict]:
    """Return a list of token dicts with 'type' and 'value'."""
    tokens = []
    pos = 0
    text = str(value)
    while pos < len(text):
        match = None
        for name, pattern in _COMPILED:
            m = pattern.match(text, pos)
            if m:
                tokens.append({"type": name, "value": m.group()})
                pos = m.end()
                match = True
                break
        if not match:
            pos += 1
    return tokens


def _walk_and_tokenize(data: Any, prefix: str = "") -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else str(k)
            result.update(_walk_and_tokenize(v, full_key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            full_key = f"{prefix}[{i}]"
            result.update(_walk_and_tokenize(item, full_key))
    else:
        result[prefix] = tokenize_value(str(data) if data is not None else "")
    return result


def tokenize_config(path: str) -> dict[str, list[dict]]:
    """Load a YAML config and return a mapping of dotted key -> token list."""
    data = load_yaml_for_tokenize(path)
    return _walk_and_tokenize(data)


def format_token_summary(tokens: dict[str, list[dict]]) -> str:
    lines = []
    for key, token_list in sorted(tokens.items()):
        types = ", ".join(t["type"] for t in token_list) if token_list else "(empty)"
        lines.append(f"  {key}: [{types}]")
    return "\n".join(lines)
