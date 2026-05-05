"""Tests for confctl.deduplicator."""

import pytest

from confctl.deduplicator import (
    DeduplicateError,
    find_duplicates,
    format_duplicates,
    load_yaml_for_dedup,
    _flatten,
)


@pytest.fixture()
def yaml_files(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("db:\n  host: localhost\n  port: 5432\napp:\n  debug: true\n")
    b.write_text("db:\n  host: prod-db\ncache:\n  ttl: 60\n")
    return str(a), str(b)


def test_load_yaml_for_dedup_returns_dict(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text("key: value\n")
    result = load_yaml_for_dedup(str(f))
    assert isinstance(result, dict)
    assert result["key"] == "value"


def test_load_yaml_for_dedup_missing_raises(tmp_path):
    with pytest.raises(DeduplicateError, match="File not found"):
        load_yaml_for_dedup(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_dedup_empty_returns_empty(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    assert load_yaml_for_dedup(str(f)) == {}


def test_load_yaml_for_dedup_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(DeduplicateError, match="Expected a YAML mapping"):
        load_yaml_for_dedup(str(f))


def test_flatten_returns_dotted_keys():
    data = {"a": {"b": {"c": 1}}, "x": 2}
    keys = _flatten(data)
    assert "a" in keys
    assert "a.b" in keys
    assert "a.b.c" in keys
    assert "x" in keys


def test_flatten_empty_dict():
    assert _flatten({}) == []


def test_find_duplicates_detects_shared_keys(yaml_files):
    a, b = yaml_files
    dupes = find_duplicates([a, b])
    assert "db" in dupes
    assert "db.host" in dupes
    assert len(dupes["db"]) == 2


def test_find_duplicates_no_overlap(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("alpha: 1\n")
    b.write_text("beta: 2\n")
    assert find_duplicates([str(a), str(b)]) == {}


def test_find_duplicates_empty_list_raises():
    with pytest.raises(DeduplicateError, match="No files provided"):
        find_duplicates([])


def test_find_duplicates_single_file_no_dupes(tmp_path):
    f = tmp_path / "only.yaml"
    f.write_text("x: 1\ny: 2\n")
    assert find_duplicates([str(f)]) == {}


def test_format_duplicates_no_dupes():
    assert format_duplicates({}) == "No duplicate keys found."


def test_format_duplicates_lists_keys(yaml_files):
    a, b = yaml_files
    dupes = find_duplicates([a, b])
    report = format_duplicates(dupes)
    assert "Duplicate keys detected:" in report
    assert "db" in report
    assert "db.host" in report
