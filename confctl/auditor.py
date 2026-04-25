"""Audit trail for config changes: record, load, and summarize audit entries."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class AuditError(Exception):
    """Raised when an audit operation fails."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_entry(
    action: str,
    files: list[str],
    user: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Build a single audit entry dict."""
    if not action:
        raise AuditError("action must not be empty")
    if not files:
        raise AuditError("files list must not be empty")
    entry: dict[str, Any] = {
        "timestamp": _utcnow(),
        "action": action,
        "files": list(files),
    }
    if user:
        entry["user"] = user
    if note:
        entry["note"] = note
    return entry


def append_audit_log(log_path: str, entry: dict[str, Any]) -> None:
    """Append an audit entry as a JSON line to *log_path*."""
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        raise AuditError(f"cannot write audit log '{log_path}': {exc}") from exc


def load_audit_log(log_path: str) -> list[dict[str, Any]]:
    """Return all entries from a JSON-lines audit log file."""
    if not os.path.exists(log_path):
        raise AuditError(f"audit log not found: '{log_path}'")
    entries: list[dict[str, Any]] = []
    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise AuditError(
                        f"malformed JSON on line {lineno} of '{log_path}': {exc}"
                    ) from exc
    except OSError as exc:
        raise AuditError(f"cannot read audit log '{log_path}': {exc}") from exc
    return entries


def summarize_audit_log(entries: list[dict[str, Any]]) -> str:
    """Return a human-readable summary of audit entries."""
    if not entries:
        return "No audit entries found."
    lines = [f"{'TIMESTAMP':<35} {'ACTION':<15} FILES"]
    lines.append("-" * 72)
    for e in entries:
        ts = e.get("timestamp", "unknown")
        action = e.get("action", "unknown")
        files = ", ".join(e.get("files", []))
        lines.append(f"{ts:<35} {action:<15} {files}")
    return "\n".join(lines)
