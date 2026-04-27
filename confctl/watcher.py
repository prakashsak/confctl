"""Watch config files for changes and emit events."""

import hashlib
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional


class WatchError(Exception):
    pass


def _file_hash(path: Path) -> str:
    """Return MD5 hex digest of file contents."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise WatchError(f"Cannot read file for hashing: {path}") from exc


def build_snapshot(paths: List[Path]) -> Dict[str, str]:
    """Return a mapping of path -> hash for all given files."""
    snapshot: Dict[str, str] = {}
    for path in paths:
        p = Path(path)
        if not p.is_file():
            raise WatchError(f"File not found: {path}")
        snapshot[str(p)] = _file_hash(p)
    return snapshot


def detect_changes(
    old: Dict[str, str], new: Dict[str, str]
) -> Dict[str, str]:
    """Compare two snapshots and return changed/added/removed paths.

    Returns a dict mapping path -> status: 'modified', 'added', 'removed'.
    """
    changes: Dict[str, str] = {}
    all_keys = set(old) | set(new)
    for key in all_keys:
        if key not in old:
            changes[key] = "added"
        elif key not in new:
            changes[key] = "removed"
        elif old[key] != new[key]:
            changes[key] = "modified"
    return changes


def watch(
    paths: List[str],
    callback: Callable[[Dict[str, str]], None],
    interval: float = 1.0,
    max_cycles: Optional[int] = None,
) -> None:
    """Poll files for changes and invoke callback with change dict.

    Args:
        paths: List of file paths to watch.
        callback: Called with a {path: status} dict on each change.
        interval: Seconds between polls.
        max_cycles: Stop after this many poll cycles (None = forever).
    """
    resolved = [Path(p) for p in paths]
    current = build_snapshot(resolved)
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        time.sleep(interval)
        updated = build_snapshot(resolved)
        changes = detect_changes(current, updated)
        if changes:
            callback(changes)
        current = updated
        cycles += 1
