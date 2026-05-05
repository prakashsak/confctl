"""Tests for confctl.pruner."""

from __future__ import annotations

import pytest

from confctl.pruner import (
    PruneError,
    _flatten,
    dump_pruned,
    find_stale_keys,
    load_yaml_for_prune,
    prune_keys,
)


@pytest.fixture()
def yaml_config(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("db:\n  host: localhost\n  port: 5432\napp:\n  debug: true\n")
    return f


@pytest.fixture()
def reference_config(tmp_path):
    ref = tmp_path / "reference.yaml"
    ref.write_text("db:\n  host: localhost\n")
    return ref


@pytest.fixture()
def empty_yaml(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    return f


def test_load_yaml_for_prune_returns_dict(yaml_config):
    data = load_yaml_for_prune(str(yaml_config))
    assert isinstance(data, dict)


def test_load_yaml_for_prune_missing_raises(tmp_path):
    with pytest.raises(PruneError, match="not found"):
        load_yaml_for_prune(str(tmp_path / "ghost.yaml"))


def test_load_yaml_for_prune_empty_returns_empty(empty_yaml):
    data = load_yaml_for_prune(str(empty_yaml))
    assert data == {}


def test_load_yaml_for_prune_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(PruneError, match="mapping"):
        load_yaml_for_prune(str(f))


def test_flatten_returns_dotted_keys():
    data = {"a": {"b": {"c": 1}, "d": 2}, "e": 3}
    keys = _flatten(data)
    assert "a" in keys
    assert "a.b" in keys
    assert "a.b.c" in keys
    assert "a.d" in keys
    assert "e" in keys


def test_flatten_empty_dict():
    assert _flatten({}) == set()


def test_find_stale_keys_detects_extras(yaml_config, reference_config):
    data = load_yaml_for_prune(str(yaml_config))
    reference = load_yaml_for_prune(str(reference_config))
    stale = find_stale_keys(data, reference)
    assert "db.port" in stale
    assert "app" in stale
    assert "app.debug" in stale


def test_find_stale_keys_no_stale_when_identical(yaml_config):
    data = load_yaml_for_prune(str(yaml_config))
    stale = find_stale_keys(data, data)
    assert stale == []


def test_prune_keys_removes_specified_keys():
    data = {"db": {"host": "localhost", "port": 5432}, "app": {"debug": True}}
    pruned = prune_keys(data, ["db.port", "app"])
    assert "port" not in pruned.get("db", {})
    assert "app" not in pruned


def test_prune_keys_does_not_mutate_original():
    data = {"a": {"b": 1, "c": 2}}
    prune_keys(data, ["a.b"])
    assert "b" in data["a"]


def test_prune_keys_empty_list_returns_copy():
    data = {"x": 1}
    result = prune_keys(data, [])
    assert result == data
    assert result is not data


def test_dump_pruned_returns_string():
    data = {"key": "value"}
    output = dump_pruned(data)
    assert isinstance(output, str)
    assert "key" in output


def test_dump_pruned_empty_dict():
    output = dump_pruned({})
    assert output.strip() == "{}"
