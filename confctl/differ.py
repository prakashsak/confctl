"""Utilities for loading, computing, and displaying diffs between config files."""

import difflib
from pathlib import Path
from typing import List, Optional


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"


def load_file(path: str) -> List[str]:
    """Read a file and return its lines, raising FileNotFoundError if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return p.read_text().splitlines(keepends=True)


def compute_diff(
    lines_a: List[str],
    lines_b: List[str],
    label_a: str = "a",
    label_b: str = "b",
) -> List[str]:
    """Return unified diff lines between two lists of text lines."""
    return list(
        difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile=label_a,
            tofile=label_b,
        )
    )


def colorize_diff(diff_lines: List[str]) -> str:
    """Apply ANSI color codes to a list of unified diff lines."""
    colored = []
    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            colored.append(f"{ANSI_CYAN}{line}{ANSI_RESET}")
        elif line.startswith("+"):
            colored.append(f"{ANSI_GREEN}{line}{ANSI_RESET}")
        elif line.startswith("-"):
            colored.append(f"{ANSI_RED}{line}{ANSI_RESET}")
        else:
            colored.append(line)
    return "".join(colored)


def diff_configs(
    path_a: str,
    path_b: str,
    label_a: Optional[str] = None,
    label_b: Optional[str] = None,
    colorize: bool = True,
) -> str:
    """Load two config files and return a formatted diff string.

    Returns an empty string when the files are identical.
    """
    lines_a = load_file(path_a)
    lines_b = load_file(path_b)

    diff = compute_diff(
        lines_a,
        lines_b,
        label_a=label_a or path_a,
        label_b=label_b or path_b,
    )

    if not diff:
        return ""

    if colorize:
        return colorize_diff(diff)

    return "".join(diff)
