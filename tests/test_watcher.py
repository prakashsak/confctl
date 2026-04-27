"""Tests for confctl.watcher."""

import pytest
from pathlib import Path

from confctl.watcher import (
    WatchError,
    _file_hash,
    build_snapshot,
    detect_changes,
    watch,
)


@pytest.fixture
def config_files(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("key: value\n")
    b.write_text("other: 1\n")
    return {"a": a, "b": b}


def test_file_hash_returns_string(config_files):
    h = _file_hash(config_files["a"])
    assert isinstance(h, str) and len(h) == 32


def test_file_hash_missing_raises(tmp_path):
    with pytest.raises(WatchError, match="Cannot read file"):
        _file_hash(tmp_path / "missing.yaml")


def test_file_hash_changes_on_content_change(config_files):
    p = config_files["a"]
    h1 = _file_hash(p)
    p.write_text("key: changed\n")
    h2 = _file_hash(p)
    assert h1 != h2


def test_build_snapshot_returns_dict(config_files):
    snap = build_snapshot(list(config_files.values()))
    assert len(snap) == 2
    for v in snap.values():
        assert isinstance(v, str)


def test_build_snapshot_missing_file_raises(tmp_path):
    with pytest.raises(WatchError, match="File not found"):
        build_snapshot([tmp_path / "ghost.yaml"])


def test_detect_changes_modified(config_files):
    p = config_files["a"]
    old = {str(p): "aaa"}
    new = {str(p): "bbb"}
    changes = detect_changes(old, new)
    assert changes[str(p)] == "modified"


def test_detect_changes_added(config_files):
    p = config_files["a"]
    old = {}
    new = {str(p): "aaa"}
    changes = detect_changes(old, new)
    assert changes[str(p)] == "added"


def test_detect_changes_removed(config_files):
    p = config_files["a"]
    old = {str(p): "aaa"}
    new = {}
    changes = detect_changes(old, new)
    assert changes[str(p)] == "removed"


def test_detect_changes_no_diff(config_files):
    p = config_files["a"]
    snap = {str(p): "abc"}
    assert detect_changes(snap, snap) == {}


def test_watch_invokes_callback_on_change(config_files):
    p = config_files["a"]
    events = []

    def fake_callback(changes):
        events.append(changes)

    original_content = p.read_text()

    import confctl.watcher as wmod
    original_sleep = wmod.time.sleep
    call_count = [0]

    def fake_sleep(s):
        call_count[0] += 1
        if call_count[0] == 1:
            p.write_text("key: updated\n")

    wmod.time.sleep = fake_sleep
    try:
        watch(paths=[str(p)], callback=fake_callback, interval=0.01, max_cycles=2)
    finally:
        wmod.time.sleep = original_sleep
        p.write_text(original_content)

    assert len(events) >= 1
    assert str(p) in events[0]
