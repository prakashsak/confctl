"""Tag management for config files — attach, remove, and filter tags stored in YAML front-matter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import yaml


class TagError(Exception):
    """Raised when a tagging operation fails."""


_TAG_COMMENT_RE = re.compile(r"^#\s*tags:\s*(.+)$", re.IGNORECASE)


def read_tags(path: str | Path) -> List[str]:
    """Return the list of tags declared in the first comment line of *path*.

    Tags are stored as a comma-separated list on a line like::

        # tags: production, critical, reviewed

    Returns an empty list when no tag line is found.
    """
    p = Path(path)
    if not p.exists():
        raise TagError(f"File not found: {path}")
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            m = _TAG_COMMENT_RE.match(line.rstrip())
            if m:
                return [t.strip() for t in m.group(1).split(",") if t.strip()]
    return []


def write_tags(path: str | Path, tags: List[str]) -> None:
    """Rewrite *path* so that its first line is the canonical tag comment.

    If a tag comment already exists it is replaced; otherwise the new line is
    prepended to the file content.
    """
    p = Path(path)
    if not p.exists():
        raise TagError(f"File not found: {path}")
    tag_line = "# tags: " + ", ".join(sorted(set(tags))) + "\n"
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    if lines and _TAG_COMMENT_RE.match(lines[0].rstrip()):
        lines[0] = tag_line
    else:
        lines.insert(0, tag_line)
    p.write_text("".join(lines), encoding="utf-8")


def add_tag(path: str | Path, tag: str) -> List[str]:
    """Add *tag* to *path* and return the updated tag list."""
    if not tag or not tag.strip():
        raise TagError("Tag must be a non-empty string.")
    current = read_tags(path)
    if tag not in current:
        current.append(tag)
    write_tags(path, current)
    return sorted(set(current))


def remove_tag(path: str | Path, tag: str) -> List[str]:
    """Remove *tag* from *path* and return the updated tag list."""
    current = read_tags(path)
    updated = [t for t in current if t != tag]
    write_tags(path, updated)
    return updated


def filter_by_tag(paths: List[str | Path], tag: str) -> List[Path]:
    """Return the subset of *paths* that carry *tag*."""
    return [Path(p) for p in paths if tag in read_tags(p)]
