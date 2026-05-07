"""Tests for confctl.redactor."""

from __future__ import annotations

import pytest

from confctl.redactor import (
    RedactError,
    dump_redacted,
    load_yaml_for_redact,
    redact_config,
)


@pytest.fixture()
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "database:\n"
        "  host: localhost\n"
        "  password: supersecret\n"
        "app:\n"
        "  api_key: abc123\n"
        "  name: myapp\n"
        "  token: tok-xyz\n"
    )
    return str(cfg)


def test_load_yaml_for_redact_returns_dict(yaml_config):
    data = load_yaml_for_redact(yaml_config)
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_redact_missing_raises(tmp_path):
    with pytest.raises(RedactError, match="File not found"):
        load_yaml_for_redact(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_redact_empty_returns_empty(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_yaml_for_redact(str(empty)) == {}


def test_load_yaml_for_redact_non_mapping_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(RedactError, match="Expected a YAML mapping"):
        load_yaml_for_redact(str(bad))


def test_redact_config_masks_password():
    data = {"database": {"host": "localhost", "password": "s3cr3t"}}
    result = redact_config(data)
    assert result["database"]["password"] == "***REDACTED***"
    assert result["database"]["host"] == "localhost"


def test_redact_config_masks_token():
    data = {"auth": {"token": "tok-abc", "user": "alice"}}
    result = redact_config(data)
    assert result["auth"]["token"] == "***REDACTED***"
    assert result["auth"]["user"] == "alice"


def test_redact_config_masks_api_key():
    data = {"service": {"api_key": "key-123", "endpoint": "https://example.com"}}
    result = redact_config(data)
    assert result["service"]["api_key"] == "***REDACTED***"
    assert result["service"]["endpoint"] == "https://example.com"


def test_redact_config_custom_placeholder():
    data = {"secret": "my-secret"}
    result = redact_config(data, placeholder="<hidden>")
    assert result["secret"] == "<hidden>"


def test_redact_config_extra_patterns():
    data = {"credentials": "creds-value", "name": "keep-me"}
    result = redact_config(data, extra_patterns=["credentials"])
    assert result["credentials"] == "***REDACTED***"
    assert result["name"] == "keep-me"


def test_redact_config_invalid_extra_pattern_raises():
    data = {"key": "value"}
    with pytest.raises(RedactError, match="Invalid pattern"):
        redact_config(data, extra_patterns=["[invalid"])


def test_redact_config_does_not_mutate_input():
    data = {"password": "original"}
    redact_config(data)
    assert data["password"] == "original"


def test_dump_redacted_returns_string():
    data = {"key": "value"}
    out = dump_redacted(data)
    assert isinstance(out, str)
    assert "key" in out
