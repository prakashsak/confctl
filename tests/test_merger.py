"""Tests for confctl.merger."""

from __future__ import annotations

import pytest
import yaml

from confctl.merger import MergeError, deep_merge, dump_merged, load_yaml, merge_configs


@pytest.fixture()
def yaml_files(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text("db:\n  host: localhost\n  port: 5432\napp:\n  debug: false\n")

    env = tmp_path / "prod.yaml"
    env.write_text("db:\n  host: prod-db.example.com\napp:\n  debug: false\n  workers: 4\n")

    return base, env, tmp_path


# --- load_yaml ---

def test_load_yaml_returns_dict(yaml_files):
    base, _, _ = yaml_files
    data = load_yaml(base)
    assert isinstance(data, dict)
    assert data["db"]["port"] == 5432


def test_load_yaml_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_yaml(tmp_path / "nonexistent.yaml")


def test_load_yaml_empty_file_returns_empty_dict(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_yaml(empty) == {}


def test_load_yaml_non_mapping_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(MergeError):
        load_yaml(bad)


# --- deep_merge ---

def test_deep_merge_override_wins():
    base = {"key": "base_value"}
    override = {"key": "override_value"}
    result = deep_merge(base, override)
    assert result["key"] == "override_value"


def test_deep_merge_keeps_base_only_keys():
    base = {"a": 1, "b": 2}
    override = {"b": 99}
    result = deep_merge(base, override)
    assert result["a"] == 1
    assert result["b"] == 99


def test_deep_merge_nested_dicts():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"host": "remote"}}
    result = deep_merge(base, override)
    assert result["db"]["host"] == "remote"
    assert result["db"]["port"] == 5432


def test_deep_merge_does_not_mutate_base():
    base = {"nested": {"x": 1}}
    override = {"nested": {"x": 2}}
    deep_merge(base, override)
    assert base["nested"]["x"] == 1


# --- merge_configs ---

def test_merge_configs_combines_files(yaml_files):
    base, env, _ = yaml_files
    result = merge_configs(base, env)
    assert result["db"]["host"] == "prod-db.example.com"
    assert result["db"]["port"] == 5432
    assert result["app"]["workers"] == 4


# --- dump_merged ---

def test_dump_merged_writes_yaml(yaml_files):
    base, env, tmp_path = yaml_files
    merged = merge_configs(base, env)
    out = tmp_path / "out" / "merged.yaml"
    dump_merged(merged, out)
    assert out.exists()
    loaded = yaml.safe_load(out.read_text())
    assert loaded["db"]["port"] == 5432
