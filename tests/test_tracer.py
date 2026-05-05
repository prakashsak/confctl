"""Tests for confctl/tracer.py"""

import pytest

from confctl.tracer import (
    TraceError,
    _flatten,
    format_trace,
    load_yaml_for_trace,
    trace_all_keys,
    trace_key,
)


@pytest.fixture()
def yaml_files(tmp_path):
    a = tmp_path / "a.yaml"
    a.write_text("db:\n  host: localhost\n  port: 5432\napp: myapp\n")
    b = tmp_path / "b.yaml"
    b.write_text("db:\n  host: remotehost\nfeature: enabled\n")
    return {"a": str(a), "b": str(b), "dir": tmp_path}


def test_load_yaml_for_trace_returns_dict(yaml_files):
    data = load_yaml_for_trace(yaml_files["a"])
    assert isinstance(data, dict)
    assert "db" in data


def test_load_yaml_for_trace_missing_raises(tmp_path):
    with pytest.raises(TraceError, match="not found"):
        load_yaml_for_trace(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_trace_empty_returns_empty(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    assert load_yaml_for_trace(str(f)) == {}


def test_load_yaml_for_trace_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(TraceError, match="mapping"):
        load_yaml_for_trace(str(f))


def test_flatten_simple():
    data = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
    flat = _flatten(data)
    assert flat == {"a": 1, "b.c": 2, "b.d.e": 3}


def test_flatten_empty():
    assert _flatten({}) == {}


def test_flatten_preserves_non_dict_values():
    """Ensure _flatten does not recurse into lists or other non-dict values."""
    data = {"a": [1, 2, 3], "b": {"c": None}}
    flat = _flatten(data)
    assert flat == {"a": [1, 2, 3], "b.c": None}


def test_trace_key_finds_in_both_files(yaml_files):
    origins = trace_key("db.host", [yaml_files["a"], yaml_files["b"]])
    assert len(origins) == 2
    files_found = {r["file"] for r in origins}
    assert yaml_files["a"] in files_found
    assert yaml_files["b"] in files_found


def test_trace_key_finds_in_one_file(yaml_files):
    origins = trace_key("app", [yaml_files["a"], yaml_files["b"]])
    assert len(origins) == 1
    assert origins[0]["value"] == "myapp"


def test_trace_key_not_found_returns_empty(yaml_files):
    origins = trace_key("nonexistent.key", [yaml_files["a"], yaml_files["b"]])
    assert origins == []


def test_trace_all_keys_indexes_all(yaml_files):
    index = trace_all_keys([yaml_files["a"], yaml_files["b"]])
    assert "db.host" in index
    assert "app" in index
    assert "feature" in index
    assert len(index["db.host"]) == 2


def test_format_trace_empty():
    assert format_trace([]) == "(no origins found)"


def test_format_trace_shows_file_and_value(yaml_files):
    origins = trace_key("app", [yaml_files["a"]])
    output = format_trace(origins)
    assert yaml_files["a"] in output
    assert "myapp" in output
