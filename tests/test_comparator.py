"""Tests for confctl.comparator."""

from __future__ import annotations

import pytest

from confctl.comparator import (
    CompareError,
    CompareResult,
    _flatten,
    compare_dirs,
    format_compare_result,
)


@pytest.fixture()
def config_dirs(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()

    (left / "app.yaml").write_text("host: localhost\nport: 8080\n")
    (right / "app.yaml").write_text("host: prod.example.com\nport: 443\ntimeout: 30\n")

    (left / "db.yaml").write_text("name: mydb\nuser: admin\n")
    (right / "extra.yaml").write_text("key: value\n")

    return left, right


def test_compare_dirs_returns_compare_result(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert isinstance(result, CompareResult)


def test_compare_dirs_only_in_left(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert "db.yaml" in result.only_in_left


def test_compare_dirs_only_in_right(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert "extra.yaml" in result.only_in_right


def test_compare_dirs_common_files(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert "app.yaml" in result.common


def test_compare_dirs_key_diffs_changed(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert "app.yaml" in result.key_diffs
    assert "host" in result.key_diffs["app.yaml"]["changed"]
    assert "port" in result.key_diffs["app.yaml"]["changed"]


def test_compare_dirs_key_diffs_only_right(config_dirs):
    left, right = config_dirs
    result = compare_dirs(str(left), str(right))
    assert "timeout" in result.key_diffs["app.yaml"]["only_right"]


def test_compare_dirs_identical_files(tmp_path):
    left = tmp_path / "l"
    right = tmp_path / "r"
    left.mkdir()
    right.mkdir()
    content = "key: value\n"
    (left / "cfg.yaml").write_text(content)
    (right / "cfg.yaml").write_text(content)
    result = compare_dirs(str(left), str(right))
    assert "cfg.yaml" not in result.key_diffs


def test_compare_dirs_missing_left_raises(tmp_path):
    with pytest.raises(CompareError, match="Directory not found"):
        compare_dirs(str(tmp_path / "nope"), str(tmp_path))


def test_compare_dirs_missing_right_raises(tmp_path):
    left = tmp_path / "l"
    left.mkdir()
    with pytest.raises(CompareError, match="Directory not found"):
        compare_dirs(str(left), str(tmp_path / "nope"))


def test_flatten_nested():
    data = {"a": {"b": {"c": 1}}, "d": 2}
    flat = _flatten(data)
    assert flat == {"a.b.c": 1, "d": 2}


def test_format_compare_result_no_diff():
    result = CompareResult([], [], ["f.yaml"], {})
    out = format_compare_result(result, "l", "r")
    assert "No differences" in out


def test_format_compare_result_shows_only_left():
    result = CompareResult(["only.yaml"], [], [], {})
    out = format_compare_result(result, "left", "right")
    assert "only.yaml" in out
    assert "left" in out
