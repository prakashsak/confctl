"""Snapshot module for capturing and comparing config states at a point in time."""

import json
import os
from datetime import datetime, timezone
from typing import Any

import yaml


class SnapshotError(Exception):
    pass


def capture_snapshot(config_paths: list[str]) -> dict[str, Any]:
    """Load each config file and return a snapshot dict keyed by path."""
    snapshot: dict[str, Any] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "configs": {},
    }
    for path in config_paths:
        if not os.path.isfile(path):
            raise SnapshotError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            try:
                data = yaml.safe_load(fh) or {}
            except yaml.YAMLError as exc:
                raise SnapshotError(f"Failed to parse {path}: {exc}") from exc
        snapshot["configs"][path] = data
    return snapshot


def save_snapshot(snapshot: dict[str, Any], output_path: str) -> None:
    """Persist a snapshot to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, default=str)


def load_snapshot(snapshot_path: str) -> dict[str, Any]:
    """Load a previously saved snapshot from disk."""
    if not os.path.isfile(snapshot_path):
        raise SnapshotError(f"Snapshot file not found: {snapshot_path}")
    with open(snapshot_path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise SnapshotError(f"Invalid snapshot JSON: {exc}") from exc


def diff_snapshots(
    old: dict[str, Any], new: dict[str, Any]
) -> dict[str, Any]:
    """Compare two snapshots and return added, removed, and changed keys per file."""
    old_configs = old.get("configs", {})
    new_configs = new.get("configs", {})
    all_paths = set(old_configs) | set(new_configs)
    result: dict[str, Any] = {}

    for path in sorted(all_paths):
        if path not in old_configs:
            result[path] = {"status": "added"}
        elif path not in new_configs:
            result[path] = {"status": "removed"}
        else:
            old_flat = _flatten(old_configs[path])
            new_flat = _flatten(new_configs[path])
            added = {k: new_flat[k] for k in new_flat if k not in old_flat}
            removed = {k: old_flat[k] for k in old_flat if k not in new_flat}
            changed = {
                k: {"old": old_flat[k], "new": new_flat[k]}
                for k in old_flat
                if k in new_flat and old_flat[k] != new_flat[k]
            }
            if added or removed or changed:
                result[path] = {"status": "changed", "added": added, "removed": removed, "changed": changed}
            else:
                result[path] = {"status": "unchanged"}
    return result


def summary_diff(diff: dict[str, Any]) -> str:
    """Return a human-readable summary string for a diff produced by diff_snapshots.

    Each line reports the path and its status. For changed files the counts of
    added, removed, and modified keys are included.
    """
    lines: list[str] = []
    for path, info in diff.items():
        status = info.get("status", "unknown")
        if status == "changed":
            n_added = len(info.get("added", {}))
            n_removed = len(info.get("removed", {}))
            n_changed = len(info.get("changed", {}))
            lines.append(
                f"{path}: changed "
                f"(+{n_added} added, -{n_removed} removed, ~{n_changed} modified)"
            )
        else:
            lines.append(f"{path}: {status}")
    return "\n".join(lines)


def _flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-separated keys."""
    items: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            items.update(_flatten(value, full_key))
    else:
        items[prefix] = data
    return items
