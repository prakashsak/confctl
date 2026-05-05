"""Tests for confctl.renamer."""

from __future__ import annotations

import pytest
import yaml

from confctl.renamer import (
    RenameError,
    apply_renames,
    dump_renamed,
    load_yaml_for_rename,
    rename_key,
)


@pytest.fixture
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("database:\n  host: localhost\n  port: 5432\napp:\n  debug: true\n")
    return str(cfg)


@pytest.fixture
def empty_yaml(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    return str(f)


def test_load_yaml_for_rename_returns_dict(yaml_config):
    data = load_yaml_for_rename(yaml_config)
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_rename_missing_raises(tmp_path):
    with pytest.raises(RenameError, match="not found"):
        load_yaml_for_rename(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_rename_empty_returns_empty(empty_yaml):
    assert load_yaml_for_rename(empty_yaml) == {}


def test_load_yaml_for_rename_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(RenameError, match="mapping"):
        load_yaml_for_rename(str(f))


def test_rename_key_top_level():
    data = {"old_key": 42, "other": "x"}
    rename_key(data, "old_key", "new_key")
    assert "new_key" in data
    assert data["new_key"] == 42
    assert "old_key" not in data


def test_rename_key_nested():
    data = {"database": {"host": "localhost", "port": 5432}}
    rename_key(data, "database.host", "database.hostname")
    assert "hostname" in data["database"]
    assert data["database"]["hostname"] == "localhost"
    assert "host" not in data["database"]


def test_rename_key_missing_raises():
    data = {"a": 1}
    with pytest.raises(RenameError, match="not found"):
        rename_key(data, "b", "c")


def test_rename_key_target_exists_raises():
    data = {"a": 1, "b": 2}
    with pytest.raises(RenameError, match="already exists"):
        rename_key(data, "a", "b")


def test_rename_key_creates_nested_path():
    data = {"flat_key": "value"}
    rename_key(data, "flat_key", "nested.deep.key")
    assert data["nested"]["deep"]["key"] == "value"
    assert "flat_key" not in data


def test_apply_renames_multiple():
    data = {"x": 1, "y": 2, "z": 3}
    apply_renames(data, {"x": "a", "y": "b"})
    assert "a" in data and "b" in data
    assert "x" not in data and "y" not in data


def test_dump_renamed_returns_valid_yaml():
    data = {"key": "value", "num": 42}
    result = dump_renamed(data)
    parsed = yaml.safe_load(result)
    assert parsed == data
