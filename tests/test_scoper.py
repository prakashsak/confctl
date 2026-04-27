"""Tests for confctl.scoper and confctl.cli_scope."""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from confctl.scoper import (
    load_yaml_for_scope,
    filter_by_scope,
    scope_config,
    format_scoped,
    ScopeError,
)


@pytest.fixture
def yaml_config(tmp_path):
    data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {"user": "admin", "password": "secret"},
        },
        "app": {
            "debug": True,
            "server": {"host": "0.0.0.0", "port": 8080},
        },
        "feature_flag": "enabled",
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data))
    return str(p)


def test_load_yaml_for_scope_returns_dict(yaml_config):
    data = load_yaml_for_scope(yaml_config)
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_scope_missing_raises(tmp_path):
    with pytest.raises(ScopeError, match="File not found"):
        load_yaml_for_scope(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_scope_empty_returns_empty(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    assert load_yaml_for_scope(str(p)) == {}


def test_load_yaml_for_scope_non_mapping_raises(tmp_path):
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n")
    with pytest.raises(ScopeError, match="Expected a YAML mapping"):
        load_yaml_for_scope(str(p))


def test_filter_by_scope_returns_nested_keys(yaml_config):
    data = load_yaml_for_scope(yaml_config)
    result = filter_by_scope(data, "database")
    assert "host" in result
    assert "port" in result


def test_filter_by_scope_deep_nesting(yaml_config):
    data = load_yaml_for_scope(yaml_config)
    result = filter_by_scope(data, "database.credentials")
    assert result.get("user") == "admin"
    assert result.get("password") == "secret"


def test_filter_by_scope_empty_scope_raises(yaml_config):
    data = load_yaml_for_scope(yaml_config)
    with pytest.raises(ScopeError, match="must not be empty"):
        filter_by_scope(data, "")


def test_filter_by_scope_missing_scope_returns_empty(yaml_config):
    data = load_yaml_for_scope(yaml_config)
    result = filter_by_scope(data, "nonexistent")
    assert result == {}


def test_scope_config_combines_load_and_filter(yaml_config):
    result = scope_config(yaml_config, "app.server")
    assert result.get("host") == "0.0.0.0"
    assert result.get("port") == 8080


def test_format_scoped_yaml(yaml_config):
    result = scope_config(yaml_config, "database")
    output = format_scoped(result, fmt="yaml")
    assert "host" in output
    assert "localhost" in output


def test_format_scoped_env(yaml_config):
    result = scope_config(yaml_config, "database")
    output = format_scoped(result, fmt="env")
    assert "HOST=localhost" in output
    assert "PORT=5432" in output


def test_format_scoped_unknown_format_raises():
    with pytest.raises(ScopeError, match="Unknown format"):
        format_scoped({"key": "val"}, fmt="toml")


def test_format_scoped_empty_dict_yaml():
    assert format_scoped({}, fmt="yaml") == ""
