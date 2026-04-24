"""Tests for the confctl.differ module."""

import textwrap
from pathlib import Path

import pytest

from confctl.differ import colorize_diff, compute_diff, diff_configs, load_file


@pytest.fixture()
def tmp_configs(tmp_path: Path):
    """Create temporary config files for testing."""
    base = tmp_path / "base.env"
    modified = tmp_path / "modified.env"

    base.write_text(
        textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        DEBUG=false
        """)
    )
    modified.write_text(
        textwrap.dedent("""\
        DB_HOST=prod.db.example.com
        DB_PORT=5432
        DEBUG=false
        LOG_LEVEL=info
        """)
    )
    return str(base), str(modified)


def test_load_file_returns_lines(tmp_path: Path):
    cfg = tmp_path / "app.conf"
    cfg.write_text("KEY=value\nOTHER=123\n")
    lines = load_file(str(cfg))
    assert lines == ["KEY=value\n", "OTHER=123\n"]


def test_load_file_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_file(str(tmp_path / "nonexistent.conf"))


def test_compute_diff_detects_changes(tmp_configs):
    source, target = tmp_configs
    diff = compute_diff(source, target)
    assert "-DB_HOST=localhost" in diff
    assert "+DB_HOST=prod.db.example.com" in diff
    assert "+LOG_LEVEL=info" in diff


def test_compute_diff_identical_files(tmp_path: Path):
    cfg = tmp_path / "same.env"
    cfg.write_text("KEY=value\n")
    diff = compute_diff(str(cfg), str(cfg))
    assert diff == ""


def test_colorize_diff_adds_ansi_codes(tmp_configs):
    source, target = tmp_configs
    raw_diff = compute_diff(source, target)
    colored = colorize_diff(raw_diff)
    assert "\033[31m" in colored  # red for removals
    assert "\033[32m" in colored  # green for additions
    assert "\033[36m" in colored  # cyan for hunk headers


def test_diff_configs_returns_none_for_identical(tmp_path: Path):
    cfg = tmp_path / "app.env"
    cfg.write_text("PORT=8080\n")
    result = diff_configs(str(cfg), str(cfg))
    assert result is None


def test_diff_configs_no_color(tmp_configs):
    source, target = tmp_configs
    result = diff_configs(source, target, colorize=False)
    assert result is not None
    assert "\033[" not in result
    assert "-DB_HOST=localhost" in result
