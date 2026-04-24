"""Tests for confctl.exporter."""

import pytest

from confctl.exporter import (
    ExportError,
    export_as_env,
    export_as_json,
    export_as_yaml,
    export_config,
    write_export,
)


SAMPLE = {"database": {"host": "localhost", "port": 5432}, "debug": True}


# ---------------------------------------------------------------------------
# export_as_json
# ---------------------------------------------------------------------------

def test_export_as_json_returns_string():
    result = export_as_json(SAMPLE)
    assert isinstance(result, str)
    assert '"host": "localhost"' in result


def test_export_as_json_is_valid_json():
    import json
    result = export_as_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed["database"]["port"] == 5432


def test_export_as_json_empty_dict():
    assert export_as_json({}) == "{}"


# ---------------------------------------------------------------------------
# export_as_yaml
# ---------------------------------------------------------------------------

def test_export_as_yaml_returns_string():
    result = export_as_yaml(SAMPLE)
    assert "localhost" in result
    assert "database:" in result


def test_export_as_yaml_empty_dict():
    result = export_as_yaml({})
    assert result.strip() == "{}"


# ---------------------------------------------------------------------------
# export_as_env
# ---------------------------------------------------------------------------

def test_export_as_env_flattens_nested():
    result = export_as_env(SAMPLE)
    assert "DATABASE_HOST=localhost" in result
    assert "DATABASE_PORT=5432" in result


def test_export_as_env_top_level_key():
    result = export_as_env({"debug": True})
    assert "DEBUG=True" in result


def test_export_as_env_empty_dict():
    assert export_as_env({}) == ""


# ---------------------------------------------------------------------------
# export_config dispatch
# ---------------------------------------------------------------------------

def test_export_config_dispatches_json():
    import json
    result = export_config(SAMPLE, "json")
    assert json.loads(result)["debug"] is True


def test_export_config_dispatches_yaml():
    result = export_config(SAMPLE, "yaml")
    assert "host" in result


def test_export_config_dispatches_env():
    result = export_config(SAMPLE, "env")
    assert "DATABASE_HOST" in result


def test_export_config_case_insensitive():
    result = export_config(SAMPLE, "JSON")
    assert "localhost" in result


def test_export_config_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_config(SAMPLE, "toml")


# ---------------------------------------------------------------------------
# write_export
# ---------------------------------------------------------------------------

def test_write_export_creates_file(tmp_path):
    out = tmp_path / "out" / "config.json"
    write_export('{"key": 1}', str(out))
    assert out.exists()
    assert '"key"' in out.read_text()


def test_write_export_appends_newline_if_missing(tmp_path):
    out = tmp_path / "config.env"
    write_export("KEY=val", str(out))
    assert out.read_text().endswith("\n")


def test_write_export_does_not_double_newline(tmp_path):
    out = tmp_path / "config.env"
    write_export("KEY=val\n", str(out))
    assert out.read_text() == "KEY=val\n"
