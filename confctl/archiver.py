"""Archive and restore config file sets as compressed tarballs."""

import os
import tarfile
import tempfile
from pathlib import Path
from typing import List


class ArchiveError(Exception):
    """Raised when archiving or restoring fails."""


def create_archive(file_paths: List[str], output_path: str) -> str:
    """Create a .tar.gz archive from a list of config file paths.

    Args:
        file_paths: Paths to files to include in the archive.
        output_path: Destination path for the resulting tarball.

    Returns:
        Absolute path to the created archive.

    Raises:
        ArchiveError: If any source file is missing or writing fails.
    """
    if not file_paths:
        raise ArchiveError("file_paths must not be empty")

    for fp in file_paths:
        if not os.path.isfile(fp):
            raise ArchiveError(f"File not found: {fp}")

    try:
        with tarfile.open(output_path, "w:gz") as tar:
            for fp in file_paths:
                tar.add(fp, arcname=os.path.relpath(fp))
    except OSError as exc:
        raise ArchiveError(f"Failed to write archive: {exc}") from exc

    return os.path.abspath(output_path)


def list_archive(archive_path: str) -> List[str]:
    """Return the list of member names in an archive.

    Raises:
        ArchiveError: If the archive cannot be opened.
    """
    if not os.path.isfile(archive_path):
        raise ArchiveError(f"Archive not found: {archive_path}")

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            return tar.getnames()
    except tarfile.TarError as exc:
        raise ArchiveError(f"Failed to read archive: {exc}") from exc


def restore_archive(archive_path: str, dest_dir: str) -> List[str]:
    """Extract all files from an archive into dest_dir.

    Returns:
        List of extracted file paths.

    Raises:
        ArchiveError: If extraction fails.
    """
    if not os.path.isfile(archive_path):
        raise ArchiveError(f"Archive not found: {archive_path}")

    os.makedirs(dest_dir, exist_ok=True)

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
            extracted = [os.path.join(dest_dir, m) for m in tar.getnames()]
    except tarfile.TarError as exc:
        raise ArchiveError(f"Failed to extract archive: {exc}") from exc

    return extracted
