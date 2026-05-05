"""Tests for confctl.sorter."""

from __future__ import annotations

import pytest
import yaml

from confctl.sorter import (
    SortError,
    load_yaml_for_sort,
    sort_config,
    dump_sorted,
    sort_file,
)


@pytest.fixture()
def yaml_config(tmp_path):
    content = """zebra: 1\napple: 2\nmango:\n  beta: 3\n  alpha: 4\n"""
    p = tmp_path / "config.yaml"
    p.write_text(content)
    return p


@pytest.fixture()
def empty_yaml(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    return p


def test_load_yaml_for_sort_returns_dict(yaml_config):
    data = load_yaml_for_sort(str(yaml_config))
    assert isinstance(data, dict)
    assert "zebra" in data


def test_load_yaml_for_sort_missing_raises(tmp_path):
    with pytest.raises(SortError, match="not found"):
        load_yaml_for_sort(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_sort_empty_returns_empty(empty_yaml):
    data = load_yaml_for_sort(str(empty_yaml))
    assert data == {}


def test_load_yaml_for_sort_non_mapping_raises(tmp_path):
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n")
    with pytest.raises(SortError, match="mapping"):
        load_yaml_for_sort(str(p))


def test_sort_config_sorts_top_level_keys():
    data = {"zebra": 1, "apple": 2, "mango": 3}
    result = sort_config(data)
    assert list(result.keys()) == ["apple", "mango", "zebra"]


def test_sort_config_sorts_nested_keys():
    data = {"b": {"z": 1, "a": 2}, "a": 0}
    result = sort_config(data)
    assert list(result.keys()) == ["a", "b"]
    assert list(result["b"].keys()) == ["a", "z"]


def test_sort_config_reverse():
    data = {"apple": 1, "mango": 2, "zebra": 3}
    result = sort_config(data, reverse=True)
    assert list(result.keys()) == ["zebra", "mango", "apple"]


def test_sort_config_non_dict_raises():
    with pytest.raises(SortError):
        sort_config(["a", "b"])


def test_sort_config_preserves_list_values():
    data = {"b": [3, 1, 2], "a": 0}
    result = sort_config(data)
    assert result["b"] == [3, 1, 2]


def test_dump_sorted_returns_string():
    data = {"a": 1, "b": 2}
    out = dump_sorted(data)
    assert isinstance(out, str)
    assert "a:" in out


def test_dump_sorted_preserves_order():
    data = {"z": 1, "a": 2}
    out = dump_sorted(data)
    lines = [l for l in out.splitlines() if ":" in l]
    keys = [l.split(":")[0].strip() for l in lines]
    assert keys == ["z", "a"]


def test_sort_file_writes_sorted_yaml(yaml_config):
    sort_file(str(yaml_config))
    data = yaml.safe_load(yaml_config.read_text())
    keys = list(data.keys())
    assert keys == sorted(keys)


def test_sort_file_output_writes_to_new_path(yaml_config, tmp_path):
    out = tmp_path / "out.yaml"
    sort_file(str(yaml_config), output=str(out))
    assert out.exists()
    data = yaml.safe_load(out.read_text())
    assert list(data.keys()) == sorted(data.keys())
