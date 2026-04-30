"""Tests for confctl.normalizer."""

import textwrap

import pytest

from confctl.normalizer import (
    NormalizeError,
    dump_normalized,
    load_yaml_for_normalize,
    normalize_config,
    normalize_keys,
)


@pytest.fixture()
def yaml_config(tmp_path):
    content = textwrap.dedent("""\
        Database-Host: localhost
        DB_PORT: 5432
        "App Name":
          Debug-Mode: true
          Max Connections: 10
    """)
    f = tmp_path / "config.yaml"
    f.write_text(content)
    return str(f)


@pytest.fixture()
def empty_yaml(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    return str(f)


def test_load_yaml_for_normalize_returns_dict(yaml_config):
    data = load_yaml_for_normalize(yaml_config)
    assert isinstance(data, dict)


def test_load_yaml_for_normalize_missing_raises(tmp_path):
    with pytest.raises(NormalizeError, match="File not found"):
        load_yaml_for_normalize(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_normalize_empty_returns_empty(empty_yaml):
    data = load_yaml_for_normalize(empty_yaml)
    assert data == {}


def test_load_yaml_for_normalize_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(NormalizeError, match="Expected a YAML mapping"):
        load_yaml_for_normalize(str(f))


def test_normalize_keys_lowercases(yaml_config):
    data = load_yaml_for_normalize(yaml_config)
    result = normalize_keys(data)
    assert "database_host" in result
    assert "db_port" in result


def test_normalize_keys_replaces_hyphens():
    data = {"some-key": "value", "another-key": 1}
    result = normalize_keys(data)
    assert "some_key" in result
    assert "another_key" in result


def test_normalize_keys_replaces_spaces():
    data = {"App Name": "confctl"}
    result = normalize_keys(data)
    assert "app_name" in result


def test_normalize_keys_recurses_into_nested_dicts():
    data = {"Outer-Key": {"Inner-Key": 42}}
    result = normalize_keys(data)
    assert result["outer_key"]["inner_key"] == 42


def test_normalize_keys_preserves_values():
    data = {"Port": 8080, "Host": "localhost"}
    result = normalize_keys(data)
    assert result["port"] == 8080
    assert result["host"] == "localhost"


def test_dump_normalized_returns_string():
    data = {"host": "localhost", "port": 5432}
    out = dump_normalized(data)
    assert isinstance(out, str)
    assert "host" in out


def test_normalize_config_end_to_end(yaml_config):
    result = normalize_config(yaml_config)
    assert "database_host" in result
    assert "app_name" in result
    assert result["app_name"]["debug_mode"] is True
    assert result["app_name"]["max_connections"] == 10
