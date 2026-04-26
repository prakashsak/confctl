"""Tests for confctl.tagger."""

from __future__ import annotations

import pytest
from pathlib import Path

from confctl.tagger import (
    TagError,
    add_tag,
    filter_by_tag,
    read_tags,
    remove_tag,
    write_tags,
)


@pytest.fixture()
def tagged_file(tmp_path: Path) -> Path:
    """A YAML config that already has a tag comment."""
    f = tmp_path / "app.yaml"
    f.write_text("# tags: production, critical\nkey: value\n")
    return f


@pytest.fixture()
def untagged_file(tmp_path: Path) -> Path:
    """A YAML config with no tag comment."""
    f = tmp_path / "base.yaml"
    f.write_text("key: value\n")
    return f


# --- read_tags ---

def test_read_tags_returns_list(tagged_file: Path):
    tags = read_tags(tagged_file)
    assert isinstance(tags, list)
    assert "production" in tags
    assert "critical" in tags


def test_read_tags_empty_when_no_comment(untagged_file: Path):
    assert read_tags(untagged_file) == []


def test_read_tags_missing_file_raises(tmp_path: Path):
    with pytest.raises(TagError, match="File not found"):
        read_tags(tmp_path / "ghost.yaml")


# --- write_tags ---

def test_write_tags_replaces_existing_tag_line(tagged_file: Path):
    write_tags(tagged_file, ["staging"])
    assert read_tags(tagged_file) == ["staging"]


def test_write_tags_prepends_when_no_tag_line(untagged_file: Path):
    write_tags(untagged_file, ["dev"])
    content = untagged_file.read_text()
    assert content.startswith("# tags:")
    assert "key: value" in content


def test_write_tags_missing_file_raises(tmp_path: Path):
    with pytest.raises(TagError):
        write_tags(tmp_path / "nope.yaml", ["x"])


# --- add_tag ---

def test_add_tag_appends_new_tag(tagged_file: Path):
    result = add_tag(tagged_file, "reviewed")
    assert "reviewed" in result
    assert "production" in result


def test_add_tag_is_idempotent(tagged_file: Path):
    first = add_tag(tagged_file, "production")
    second = add_tag(tagged_file, "production")
    assert first == second


def test_add_tag_empty_string_raises(tagged_file: Path):
    with pytest.raises(TagError, match="non-empty"):
        add_tag(tagged_file, "")


# --- remove_tag ---

def test_remove_tag_removes_existing(tagged_file: Path):
    result = remove_tag(tagged_file, "critical")
    assert "critical" not in result


def test_remove_tag_noop_when_absent(tagged_file: Path):
    result = remove_tag(tagged_file, "nonexistent")
    assert "production" in result


# --- filter_by_tag ---

def test_filter_by_tag_returns_matching(tagged_file: Path, untagged_file: Path):
    matches = filter_by_tag([tagged_file, untagged_file], "production")
    assert tagged_file in matches
    assert untagged_file not in matches


def test_filter_by_tag_empty_when_none_match(tagged_file: Path):
    assert filter_by_tag([tagged_file], "unknown") == []
