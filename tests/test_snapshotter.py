"""Tests for confctl.snapshotter."""

import json
import os
import textwrap

import pytest

from confctl.snapshotter import (
    SnapshotError,
    _flatten,
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def yaml_configs(tmp_path):
    a = tmp_path / "a.yaml"
    a.write_text(textwrap.dedent("""\
        database:
          host: localhost
          port: 5432
        debug: true
    """))
    b = tmp_path / "b.yaml"
    b.write_text(textwrap.dedent("""\
        database:
          host: prod-db
          port: 5432
        debug: false
    """))
    return a, b


def test_capture_snapshot_returns_dict(yaml_configs):
    a, b = yaml_configs
    snap = capture_snapshot([str(a), str(b)])
    assert "captured_at" in snap
    assert str(a) in snap["configs"]
    assert str(b) in snap["configs"]


def test_capture_snapshot_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        capture_snapshot([str(tmp_path / "ghost.yaml")])


def test_capture_snapshot_invalid_yaml_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("key: [unclosed")
    with pytest.raises(SnapshotError, match="Failed to parse"):
        capture_snapshot([str(bad)])


def test_save_and_load_snapshot_roundtrip(tmp_path, yaml_configs):
    a, _ = yaml_configs
    snap = capture_snapshot([str(a)])
    out = tmp_path / "snap.json"
    save_snapshot(snap, str(out))
    loaded = load_snapshot(str(out))
    assert loaded["configs"] == snap["configs"]


def test_load_snapshot_missing_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(str(tmp_path / "missing.json"))


def test_load_snapshot_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(SnapshotError, match="Invalid snapshot JSON"):
        load_snapshot(str(bad))


def test_diff_snapshots_detects_changed_values(yaml_configs):
    a, b = yaml_configs
    old = capture_snapshot([str(a)])
    new_snap = capture_snapshot([str(a)])
    # mutate new snapshot in memory
    new_snap["configs"][str(a)]["debug"] = False
    diff = diff_snapshots(old, new_snap)
    assert diff[str(a)]["status"] == "changed"
    assert "debug" in diff[str(a)]["changed"]


def test_diff_snapshots_unchanged(yaml_configs):
    a, _ = yaml_configs
    snap = capture_snapshot([str(a)])
    diff = diff_snapshots(snap, snap)
    assert diff[str(a)]["status"] == "unchanged"


def test_diff_snapshots_added_file(yaml_configs):
    a, b = yaml_configs
    old = capture_snapshot([str(a)])
    new_snap = capture_snapshot([str(a), str(b)])
    diff = diff_snapshots(old, new_snap)
    assert diff[str(b)]["status"] == "added"


def test_flatten_nested_dict():
    data = {"a": {"b": {"c": 1}, "d": 2}, "e": 3}
    flat = _flatten(data)
    assert flat == {"a.b.c": 1, "a.d": 2, "e": 3}


def test_flatten_empty_dict():
    assert _flatten({}) == {}
