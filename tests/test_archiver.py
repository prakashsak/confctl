"""Tests for confctl.archiver."""

import os
import pytest

from confctl.archiver import ArchiveError, create_archive, list_archive, restore_archive


@pytest.fixture()
def config_files(tmp_path):
    """Create a small set of config files for testing."""
    files = []
    for name in ("app.yaml", "db.yaml", "secrets.yaml"):
        p = tmp_path / name
        p.write_text(f"key: {name}\n")
        files.append(str(p))
    return files


@pytest.fixture()
def archive_path(tmp_path):
    return str(tmp_path / "configs.tar.gz")


# --- create_archive ---

def test_create_archive_returns_path(config_files, archive_path):
    result = create_archive(config_files, archive_path)
    assert result == os.path.abspath(archive_path)


def test_create_archive_file_exists(config_files, archive_path):
    create_archive(config_files, archive_path)
    assert os.path.isfile(archive_path)


def test_create_archive_empty_list_raises(archive_path):
    with pytest.raises(ArchiveError, match="must not be empty"):
        create_archive([], archive_path)


def test_create_archive_missing_file_raises(tmp_path, archive_path):
    with pytest.raises(ArchiveError, match="File not found"):
        create_archive([str(tmp_path / "ghost.yaml")], archive_path)


# --- list_archive ---

def test_list_archive_returns_names(config_files, archive_path):
    create_archive(config_files, archive_path)
    names = list_archive(archive_path)
    assert isinstance(names, list)
    assert len(names) == 3


def test_list_archive_contains_filenames(config_files, archive_path):
    create_archive(config_files, archive_path)
    names = list_archive(archive_path)
    for cf in config_files:
        assert any(os.path.basename(cf) in n for n in names)


def test_list_archive_missing_raises(tmp_path):
    with pytest.raises(ArchiveError, match="Archive not found"):
        list_archive(str(tmp_path / "no_such.tar.gz"))


# --- restore_archive ---

def test_restore_archive_returns_paths(config_files, archive_path, tmp_path):
    create_archive(config_files, archive_path)
    dest = str(tmp_path / "restored")
    extracted = restore_archive(archive_path, dest)
    assert isinstance(extracted, list)
    assert len(extracted) == 3


def test_restore_archive_files_exist(config_files, archive_path, tmp_path):
    create_archive(config_files, archive_path)
    dest = str(tmp_path / "restored")
    restore_archive(archive_path, dest)
    for cf in config_files:
        restored = os.path.join(dest, os.path.relpath(cf))
        assert os.path.isfile(restored)


def test_restore_archive_missing_raises(tmp_path):
    with pytest.raises(ArchiveError, match="Archive not found"):
        restore_archive(str(tmp_path / "missing.tar.gz"), str(tmp_path / "out"))


def test_restore_archive_creates_dest_dir(config_files, archive_path, tmp_path):
    create_archive(config_files, archive_path)
    dest = str(tmp_path / "brand" / "new" / "dir")
    restore_archive(archive_path, dest)
    assert os.path.isdir(dest)
