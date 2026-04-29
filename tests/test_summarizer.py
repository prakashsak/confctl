"""Tests for confctl.summarizer and confctl.cli_summarize."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from confctl.summarizer import (
    SummaryError,
    format_summary,
    load_yaml_for_summary,
    summarize,
)


@pytest.fixture()
def yaml_config(tmp_path: Path) -> Path:
    f = tmp_path / "config.yaml"
    f.write_text(
        "database:\n"
        "  host: localhost\n"
        "  port: 5432\n"
        "  password: null\n"
        "app:\n"
        "  debug: true\n"
        "  name: myapp\n"
    )
    return f


@pytest.fixture()
def empty_yaml(tmp_path: Path) -> Path:
    f = tmp_path / "empty.yaml"
    f.write_text("")
    return f


def test_load_yaml_for_summary_returns_dict(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_summary_missing_raises() -> None:
    with pytest.raises(SummaryError, match="File not found"):
        load_yaml_for_summary("/nonexistent/path/config.yaml")


def test_load_yaml_for_summary_empty_returns_empty(empty_yaml: Path) -> None:
    data = load_yaml_for_summary(str(empty_yaml))
    assert data == {}


def test_load_yaml_for_summary_non_mapping_raises(tmp_path: Path) -> None:
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(SummaryError, match="Expected a YAML mapping"):
        load_yaml_for_summary(str(f))


def test_summarize_top_level_sections(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    summary = summarize(data)
    assert set(summary["top_level_sections"]) == {"database", "app"}
    assert summary["top_level_count"] == 2


def test_summarize_null_values(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    summary = summarize(data)
    assert summary["null_values"] == 1


def test_summarize_max_depth(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    summary = summarize(data)
    assert summary["max_depth"] >= 1


def test_summarize_empty_dict() -> None:
    summary = summarize({})
    assert summary["total_keys"] == 0
    assert summary["null_values"] == 0
    assert summary["top_level_count"] == 0


def test_format_summary_contains_path(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    summary = summarize(data)
    output = format_summary(str(yaml_config), summary)
    assert str(yaml_config) in output
    assert "null_values" not in output  # human-readable labels used instead
    assert "Null values" in output


def test_format_summary_lists_sections(yaml_config: Path) -> None:
    data = load_yaml_for_summary(str(yaml_config))
    summary = summarize(data)
    output = format_summary(str(yaml_config), summary)
    assert "database" in output
    assert "app" in output
