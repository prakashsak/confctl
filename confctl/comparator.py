"""Compare two config directories and report structural differences."""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

import yaml


class CompareError(Exception):
    pass


class CompareResult(NamedTuple):
    only_in_left: list[str]
    only_in_right: list[str]
    common: list[str]
    key_diffs: dict[str, dict]  # filename -> {only_left, only_right, changed}


def _load_flat_keys(path: Path) -> dict[str, object]:
    """Load a YAML file and return a flat key->value mapping."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CompareError(f"File not found: {path}")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise CompareError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def _flatten(mapping: dict, prefix: str = "") -> dict[str, object]:
    """Recursively flatten nested dict into dot-separated keys."""
    result = {}
    for k, v in mapping.items():
        full_key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            result.update(_flatten(v, full_key))
        else:
            result[full_key] = v
    return result


def compare_dirs(left: str, right: str) -> CompareResult:
    """Compare two config directories by their YAML file contents."""
    left_path = Path(left)
    right_path = Path(right)

    if not left_path.is_dir():
        raise CompareError(f"Directory not found: {left}")
    if not right_path.is_dir():
        raise CompareError(f"Directory not found: {right}")

    exts = {".yaml", ".yml"}
    left_files = {p.name for p in left_path.iterdir() if p.suffix in exts}
    right_files = {p.name for p in right_path.iterdir() if p.suffix in exts}

    only_left = sorted(left_files - right_files)
    only_right = sorted(right_files - left_files)
    common = sorted(left_files & right_files)

    key_diffs: dict[str, dict] = {}
    for name in common:
        lf = _flatten(_load_flat_keys(left_path / name))
        rf = _flatten(_load_flat_keys(right_path / name))
        lkeys = set(lf)
        rkeys = set(rf)
        changed = {k for k in lkeys & rkeys if lf[k] != rf[k]}
        if (lkeys - rkeys) or (rkeys - lkeys) or changed:
            key_diffs[name] = {
                "only_left": sorted(lkeys - rkeys),
                "only_right": sorted(rkeys - lkeys),
                "changed": sorted(changed),
            }

    return CompareResult(
        only_in_left=only_left,
        only_in_right=only_right,
        common=common,
        key_diffs=key_diffs,
    )


def format_compare_result(result: CompareResult, left: str, right: str) -> str:
    """Format a CompareResult into a human-readable string."""
    lines = []
    if result.only_in_left:
        lines.append(f"Only in {left}:")
        for f in result.only_in_left:
            lines.append(f"  + {f}")
    if result.only_in_right:
        lines.append(f"Only in {right}:")
        for f in result.only_in_right:
            lines.append(f"  + {f}")
    for name, diff in result.key_diffs.items():
        lines.append(f"Differences in {name}:")
        for k in diff["only_left"]:
            lines.append(f"  < {k}")
        for k in diff["only_right"]:
            lines.append(f"  > {k}")
        for k in diff["changed"]:
            lines.append(f"  ~ {k}")
    if not lines:
        lines.append("No differences found.")
    return "\n".join(lines)
