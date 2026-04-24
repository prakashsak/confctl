"""Config loader module for confctl.

Handles discovery and loading of environment-specific config files
from a given base directory.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_CONFIG_EXTENSIONS = (".env", ".cfg", ".ini", ".conf", ".yaml", ".yml")


def discover_configs(
    base_dir: str,
    extensions: tuple = DEFAULT_CONFIG_EXTENSIONS,
) -> List[str]:
    """Recursively discover config files under base_dir.

    Args:
        base_dir: Root directory to search.
        extensions: Tuple of file extensions to include.

    Returns:
        Sorted list of absolute file paths.

    Raises:
        FileNotFoundError: If base_dir does not exist.
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Config directory not found: {base_dir}")
    if not base_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {base_dir}")

    found = []
    for root, _dirs, files in os.walk(base_path):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                found.append(str(Path(root) / filename))

    return sorted(found)


def group_by_environment(
    file_paths: List[str],
    env_names: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """Group config file paths by environment name.

    Looks for environment names as path components (e.g. configs/prod/app.env).

    Args:
        file_paths: List of file paths to group.
        env_names: Explicit list of environment names to look for.
                   If None, every immediate subdirectory name is treated as an env.

    Returns:
        Dict mapping environment name -> list of file paths.
    """
    groups: Dict[str, List[str]] = {}
    for path in file_paths:
        parts = Path(path).parts
        # Use the first path component that matches an env name (or any subdir)
        env = None
        for part in parts[:-1]:  # exclude filename
            if env_names is None or part in env_names:
                env = part
                break
        if env is None:
            env = "default"
        groups.setdefault(env, []).append(path)
    return groups


def load_env_configs(base_dir: str, environment: str) -> Dict[str, List[str]]:
    """Load all config file contents for a specific environment.

    Args:
        base_dir: Root directory containing environment subdirectories.
        environment: Name of the environment subdirectory.

    Returns:
        Dict mapping filename -> list of lines.

    Raises:
        FileNotFoundError: If environment directory does not exist.
    """
    env_path = Path(base_dir) / environment
    if not env_path.exists():
        raise FileNotFoundError(f"Environment directory not found: {env_path}")

    configs: Dict[str, List[str]] = {}
    for file_path in discover_configs(str(env_path)):
        rel_name = os.path.relpath(file_path, str(env_path))
        with open(file_path, "r", encoding="utf-8") as fh:
            configs[rel_name] = fh.readlines()
    return configs
