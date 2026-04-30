"""Pin config files to a specific version hash for reproducible deployments."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List


class PinError(Exception):
    """Raised when a pin operation fails."""


def _hash_file(path: str) -> str:
    """Return SHA-256 hex digest of a file's contents."""
    if not os.path.isfile(path):
        raise PinError(f"File not found: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_pin(files: List[str]) -> Dict[str, str]:
    """Create a pin mapping {filepath: sha256} for each file."""
    if not files:
        raise PinError("No files provided to pin.")
    return {f: _hash_file(f) for f in files}


def save_pin(pin: Dict[str, str], output_path: str) -> None:
    """Persist a pin mapping to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(pin, fh, indent=2)
        fh.write("\n")


def load_pin(pin_path: str) -> Dict[str, str]:
    """Load a previously saved pin mapping."""
    if not os.path.isfile(pin_path):
        raise PinError(f"Pin file not found: {pin_path}")
    with open(pin_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise PinError(f"Pin file must contain a JSON object: {pin_path}")
    return data


def verify_pin(pin: Dict[str, str]) -> Dict[str, bool]:
    """Verify each file against its pinned hash.

    Returns a mapping {filepath: matches} where True means the file is intact.
    """
    results: Dict[str, bool] = {}
    for path, expected in pin.items():
        try:
            actual = _hash_file(path)
            results[path] = actual == expected
        except PinError:
            results[path] = False
    return results


def format_verify_summary(results: Dict[str, bool]) -> str:
    """Return a human-readable summary of pin verification results."""
    lines: List[str] = []
    for path, ok in sorted(results.items()):
        status = "OK" if ok else "CHANGED"
        lines.append(f"  [{status}] {path}")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    lines.append(f"\n{passed}/{total} files match their pinned hashes.")
    return "\n".join(lines)
