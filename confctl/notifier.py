"""notifier.py — Send notifications when config changes are detected or actions are performed.

Supports console (stderr) and webhook (HTTP POST) notification channels.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


class NotifyError(Exception):
    """Raised when a notification cannot be delivered."""


@dataclass
class NotifyEvent:
    """Represents a single notification event."""

    action: str
    files: List[str]
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: Optional[str] = None
    extra: Optional[dict] = None

    def to_dict(self) -> dict:
        """Serialise the event to a plain dictionary."""
        data = {
            "action": self.action,
            "files": self.files,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.user is not None:
            data["user"] = self.user
        if self.extra:
            data["extra"] = self.extra
        return data


def build_event(
    action: str,
    files: List[str],
    message: str,
    user: Optional[str] = None,
    extra: Optional[dict] = None,
) -> NotifyEvent:
    """Construct a NotifyEvent, validating required fields."""
    if not action or not action.strip():
        raise NotifyError("action must not be empty")
    if not files:
        raise NotifyError("files list must not be empty")
    if not message or not message.strip():
        raise NotifyError("message must not be empty")
    return NotifyEvent(
        action=action.strip(),
        files=list(files),
        message=message.strip(),
        user=user,
        extra=extra,
    )


def notify_console(event: NotifyEvent) -> str:
    """Format the event as a human-readable string (for stderr/stdout output)."""
    parts = [f"[{event.timestamp}] [{event.action.upper()}]"]
    if event.user:
        parts.append(f"user={event.user}")
    parts.append(event.message)
    parts.append(f"files: {', '.join(event.files)}")
    return " | ".join(parts)


def notify_webhook(
    event: NotifyEvent,
    url: str,
    timeout: int = 5,
    headers: Optional[dict] = None,
) -> int:
    """POST the event as JSON to *url*.

    Returns the HTTP status code on success.
    Raises NotifyError if the request fails or returns a non-2xx status.
    """
    if not url or not url.strip():
        raise NotifyError("webhook url must not be empty")

    payload = json.dumps(event.to_dict()).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    request = urllib.request.Request(url.strip(), data=payload, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        raise NotifyError(f"webhook returned HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise NotifyError(f"webhook request failed: {exc.reason}") from exc

    if not (200 <= status < 300):
        raise NotifyError(f"webhook returned non-2xx status: {status}")
    return status
