"""Schedule and record timed config operations for deferred execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ScheduleError(Exception):
    """Raised when a scheduling operation fails."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(
    action: str,
    files: list[str],
    run_at: str,
    *,
    args: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Return a new schedule job dict."""
    if not action:
        raise ScheduleError("action must not be empty")
    if not files:
        raise ScheduleError("files list must not be empty")
    try:
        datetime.fromisoformat(run_at)
    except ValueError as exc:
        raise ScheduleError(f"invalid run_at timestamp: {run_at!r}") from exc
    return {
        "action": action,
        "files": list(files),
        "run_at": run_at,
        "args": args or {},
        "note": note,
        "created_at": _utcnow(),
        "status": "pending",
    }


def save_schedule(jobs: list[dict[str, Any]], path: Path) -> None:
    """Persist a list of jobs to *path* as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(jobs, fh, indent=2)


def load_schedule(path: Path) -> list[dict[str, Any]]:
    """Load jobs from *path*; returns empty list if file absent."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ScheduleError(f"corrupt schedule file: {exc}") from exc
    if not isinstance(data, list):
        raise ScheduleError("schedule file must contain a JSON array")
    return data


def list_pending(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only jobs whose status is 'pending'."""
    return [j for j in jobs if j.get("status") == "pending"]


def mark_done(jobs: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
    """Return a new list with job at *index* marked as 'done'."""
    if index < 0 or index >= len(jobs):
        raise ScheduleError(f"job index {index} out of range")
    updated = [dict(j) for j in jobs]
    updated[index]["status"] = "done"
    return updated
