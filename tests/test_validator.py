"""Tests for confctl.validator module."""

from __future__ import annotations

import textwrap

import pytest

from confctl.validator import (
    ValidationError,
    validate_config,
    validate_all,
    validate_is_mapping,
    validate_no_null_keys,
    validate_required_keys,
)


@pytest.fixture()
def yaml_config(tmp_path):
    """Write a simple valid YAML config and return its path."""
    p = tmp_path / "app.yaml"
    p.write_text(textwrap.dedent("""\
        service: web
        port: 8080
        database:
          host: localhost
          port: 5432
    """))
    return str(p)


@pytest.fixture()
def empty_yaml(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    return str(p)


def test_validate_config_returns_dict(yaml_config):
    data = validate_config(yaml_config)
    assert data["service"] == "web"
    assert data["port"] == 8080


def test_validate_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_config(str(tmp_path / "ghost.yaml"))


def test_validate_config_empty_file_returns_empty(empty_yaml):
    data = validate_config(empty_yaml)
    assert data == {}


def test_validate_is_mapping_raises_for_list():
    with pytest.raises(ValidationError, match="mapping"):
        validate_is_mapping([1, 2, 3], "fake.yaml")


def test_validate_is_mapping_passes_for_dict():
    validate_is_mapping({"a": 1}, "fake.yaml")  # should not raise


def test_validate_no_null_keys_raises_on_none_key():
    with pytest.raises(ValidationError, match="null key"):
        validate_no_null_keys({None: "value"}, "fake.yaml")


def test_validate_required_keys_raises_when_missing():
    with pytest.raises(ValidationError, match="missing required keys"):
        validate_required_keys({"a": 1}, ["a", "b"], "fake.yaml")


def test_validate_required_keys_passes_when_present():
    validate_required_keys({"a": 1, "b": 2}, ["a", "b"], "fake.yaml")


def test_validate_config_with_required_keys(yaml_config):
    data = validate_config(yaml_config, required_keys=["service", "port"])
    assert "service" in data


def test_validate_config_missing_required_key_raises(yaml_config):
    with pytest.raises(ValidationError, match="missing required keys"):
        validate_config(yaml_config, required_keys=["service", "missing_key"])


def test_validate_all_aggregates_errors(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")  # list, not mapping
    good = tmp_path / "good.yaml"
    good.write_text("key: value\n")
    with pytest.raises(ValidationError, match="Validation failed"):
        validate_all([str(bad), str(good)])


def test_validate_all_returns_results(tmp_path):
    f1 = tmp_path / "c1.yaml"
    f1.write_text("env: prod\n")
    f2 = tmp_path / "c2.yaml"
    f2.write_text("env: staging\n")
    results = validate_all([str(f1), str(f2)])
    assert results[str(f1)]["env"] == "prod"
    assert results[str(f2)]["env"] == "staging"
