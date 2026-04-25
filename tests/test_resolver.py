"""Tests for confctl.resolver."""

import pytest
import yaml
from pathlib import Path

from confctl.resolver import (
    ResolveError,
    load_yaml_for_resolve,
    _flatten_keys,
    resolve_config,
    resolve_file,
)


@pytest.fixture
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("base: /opt\napp_dir: ${base}/app\nlog_dir: ${base}/logs\n")
    return str(cfg)


@pytest.fixture
def circular_yaml(tmp_path):
    cfg = tmp_path / "circular.yaml"
    cfg.write_text("a: ${b}\nb: ${a}\n")
    return str(cfg)


def test_load_yaml_for_resolve_returns_dict(yaml_config):
    data = load_yaml_for_resolve(yaml_config)
    assert isinstance(data, dict)
    assert "base" in data


def test_load_yaml_for_resolve_missing_raises(tmp_path):
    with pytest.raises(ResolveError, match="File not found"):
        load_yaml_for_resolve(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_resolve_empty_returns_empty(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_yaml_for_resolve(str(empty)) == {}


def test_load_yaml_for_resolve_non_mapping_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(ResolveError, match="Expected a YAML mapping"):
        load_yaml_for_resolve(str(bad))


def test_flatten_keys_simple():
    data = {"a": 1, "b": 2}
    assert _flatten_keys(data) == {"a": 1, "b": 2}


def test_flatten_keys_nested():
    data = {"db": {"host": "localhost", "port": 5432}}
    flat = _flatten_keys(data)
    assert flat["db.host"] == "localhost"
    assert flat["db.port"] == 5432


def test_resolve_config_substitutes_variables():
    data = {"base": "/opt", "app": "${base}/app"}
    resolved = resolve_config(data)
    assert resolved["app"] == "/opt/app"


def test_resolve_config_no_references_unchanged():
    data = {"key": "value", "num": 42}
    assert resolve_config(data) == data


def test_resolve_config_undefined_variable_raises():
    data = {"path": "${undefined}/dir"}
    with pytest.raises(ResolveError, match="Undefined variable"):
        resolve_config(data)


def test_resolve_config_circular_reference_raises():
    data = {"a": "${b}", "b": "${a}"}
    with pytest.raises(ResolveError, match="Circular reference"):
        resolve_config(data)


def test_resolve_file_returns_resolved_dict(yaml_config):
    resolved = resolve_file(yaml_config)
    assert resolved["app_dir"] == "/opt/app"
    assert resolved["log_dir"] == "/opt/logs"


def test_resolve_file_circular_raises(circular_yaml):
    with pytest.raises(ResolveError, match="Circular reference"):
        resolve_file(circular_yaml)
