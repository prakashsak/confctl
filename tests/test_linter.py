"""Tests for confctl.linter module."""

from __future__ import annotations

import pytest

from confctl.linter import (
    LintError,
    LintWarning,
    check_duplicate_keys,
    check_empty_values,
    check_trailing_whitespace,
    lint_config,
    load_yaml_for_lint,
)


@pytest.fixture()
def clean_yaml(tmp_path):
    f = tmp_path / "clean.yaml"
    f.write_text("host: localhost\nport: 5432\n")
    return str(f)


@pytest.fixture()
def dirty_yaml(tmp_path):
    f = tmp_path / "dirty.yaml"
    f.write_text("host: localhost  \nport: 5432\nhost: duplicate\n")
    return str(f)


@pytest.fixture()
def null_yaml(tmp_path):
    f = tmp_path / "null.yaml"
    f.write_text("host: null\nport: 5432\n")
    return str(f)


def test_load_yaml_for_lint_returns_data_and_lines(clean_yaml):
    data, lines = load_yaml_for_lint(clean_yaml)
    assert data == {"host": "localhost", "port": 5432}
    assert isinstance(lines, list)
    assert len(lines) >= 2


def test_load_yaml_for_lint_missing_raises():
    with pytest.raises(LintError, match="File not found"):
        load_yaml_for_lint("/nonexistent/path.yaml")


def test_load_yaml_for_lint_invalid_yaml(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("key: [unclosed")
    with pytest.raises(LintError, match="YAML parse error"):
        load_yaml_for_lint(str(bad))


def test_check_trailing_whitespace_detects_issues():
    lines = ["host: localhost  ", "port: 5432"]
    warnings = check_trailing_whitespace(lines, "test.yaml")
    assert len(warnings) == 1
    assert warnings[0].line == 1
    assert "trailing whitespace" in warnings[0].message


def test_check_trailing_whitespace_clean_file():
    lines = ["host: localhost", "port: 5432"]
    assert check_trailing_whitespace(lines, "test.yaml") == []


def test_check_duplicate_keys_detects_duplicates():
    lines = ["host: a", "port: 1", "host: b"]
    warnings = check_duplicate_keys(lines, "test.yaml")
    assert len(warnings) == 1
    assert "duplicate key 'host'" in warnings[0].message
    assert warnings[0].line == 3


def test_check_duplicate_keys_no_duplicates():
    lines = ["host: a", "port: 1"]
    assert check_duplicate_keys(lines, "test.yaml") == []


def test_check_empty_values_detects_nulls():
    data = {"host": None, "port": 5432}
    warnings = check_empty_values(data, "test.yaml")
    assert len(warnings) == 1
    assert "null value" in warnings[0].message


def test_check_empty_values_non_mapping_returns_empty():
    assert check_empty_values(["a", "b"], "test.yaml") == []


def test_lint_config_clean_file_no_warnings(clean_yaml):
    warnings = lint_config(clean_yaml)
    assert warnings == []


def test_lint_config_dirty_file_has_warnings(dirty_yaml):
    warnings = lint_config(dirty_yaml)
    messages = [str(w) for w in warnings]
    assert any("trailing whitespace" in m for m in messages)
    assert any("duplicate key" in m for m in messages)


def test_lint_warning_str_includes_line():
    w = LintWarning("cfg.yaml", 5, "some issue")
    assert "cfg.yaml:5" in str(w)
    assert "some issue" in str(w)


def test_lint_warning_str_no_line():
    w = LintWarning("cfg.yaml", None, "some issue")
    assert ":" not in str(w).split("cfg.yaml")[1].split("some")[0]
