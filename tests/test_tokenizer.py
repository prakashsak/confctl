"""Tests for confctl.tokenizer."""

from __future__ import annotations

import pytest

from confctl.tokenizer import (
    TokenizeError,
    load_yaml_for_tokenize,
    tokenize_value,
    tokenize_config,
    format_token_summary,
)


@pytest.fixture
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "database:\n"
        "  host: db.example.com\n"
        "  port: 5432\n"
        "  password: ${DB_PASS}\n"
        "app:\n"
        "  debug: true\n"
        "  endpoint: https://api.example.com/v1\n"
        "  socket: /var/run/app.sock\n"
    )
    return str(cfg)


def test_load_yaml_for_tokenize_returns_dict(yaml_config):
    data = load_yaml_for_tokenize(yaml_config)
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_tokenize_missing_raises(tmp_path):
    with pytest.raises(TokenizeError, match="not found"):
        load_yaml_for_tokenize(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_tokenize_empty_returns_empty(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_yaml_for_tokenize(str(empty)) == {}


def test_load_yaml_for_tokenize_non_mapping_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(TokenizeError, match="Expected mapping"):
        load_yaml_for_tokenize(str(bad))


def test_tokenize_value_detects_env_var():
    tokens = tokenize_value("${MY_VAR}")
    assert any(t["type"] == "ENV_VAR" for t in tokens)


def test_tokenize_value_detects_url():
    tokens = tokenize_value("https://example.com/path")
    assert any(t["type"] == "URL" for t in tokens)


def test_tokenize_value_detects_number():
    tokens = tokenize_value("5432")
    assert any(t["type"] == "NUMBER" for t in tokens)


def test_tokenize_value_detects_bool():
    tokens = tokenize_value("true")
    assert any(t["type"] == "BOOL" for t in tokens)


def test_tokenize_value_detects_path():
    tokens = tokenize_value("/var/run/app.sock")
    assert any(t["type"] == "PATH" for t in tokens)


def test_tokenize_value_empty_string():
    tokens = tokenize_value("")
    assert tokens == []


def test_tokenize_config_returns_flat_keys(yaml_config):
    result = tokenize_config(yaml_config)
    assert "database.port" in result
    assert "database.password" in result
    assert "app.debug" in result


def test_tokenize_config_env_var_key(yaml_config):
    result = tokenize_config(yaml_config)
    password_tokens = result.get("database.password", [])
    assert any(t["type"] == "ENV_VAR" for t in password_tokens)


def test_format_token_summary_returns_string(yaml_config):
    result = tokenize_config(yaml_config)
    summary = format_token_summary(result)
    assert isinstance(summary, str)
    assert "database.port" in summary
