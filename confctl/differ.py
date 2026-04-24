"""Module for computing and displaying diffs between config files."""

import difflib
from pathlib import Path
from typing import Optional


def load_file(path: str) -> list[str]:
    """Read a file and return its lines."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        return f.readlines()


def compute_diff(
    source_path: str,
    target_path: str,
    context_lines: int = 3,
) -> str:
    """Compute a unified diff between two config files.

    Args:
        source_path: Path to the source (base) config file.
        target_path: Path to the target (modified) config file.
        context_lines: Number of context lines to include around changes.

    Returns:
        A string containing the unified diff output.
    """
    source_lines = load_file(source_path)
    target_lines = load_file(target_path)

    diff = difflib.unified_diff(
        source_lines,
        target_lines,
        fromfile=source_path,
        tofile=target_path,
        n=context_lines,
    )
    return "".join(diff)


def colorize_diff(diff: str) -> str:
    """Apply ANSI color codes to a unified diff string.

    Args:
        diff: Raw unified diff string.

    Returns:
        Colorized diff string for terminal output.
    """
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"

    colored_lines = []
    for line in diff.splitlines(keepends=True):
        if line.startswith("+++") or line.startswith("---"):
            colored_lines.append(f"{BOLD}{line}{RESET}")
        elif line.startswith("+"):
            colored_lines.append(f"{GREEN}{line}{RESET}")
        elif line.startswith("-"):
            colored_lines.append(f"{RED}{line}{RESET}")
        elif line.startswith("@@"):
            colored_lines.append(f"{CYAN}{line}{RESET}")
        else:
            colored_lines.append(line)
    return "".join(colored_lines)


def diff_configs(
    source_path: str,
    target_path: str,
    context_lines: int = 3,
    colorize: bool = True,
) -> Optional[str]:
    """High-level function to diff two config files.

    Returns None if the files are identical, otherwise returns the diff.
    """
    diff = compute_diff(source_path, target_path, context_lines)
    if not diff:
        return None
    return colorize_diff(diff) if colorize else diff
