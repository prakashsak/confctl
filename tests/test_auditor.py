"""Tests for confctl.auditor."""

from __future__ import annotations

import json
import os

import pytest

from confctl.auditor import (
    AuditError,
    append_audit_log,
    load_audit_log,
    record_entry,
    summarize_audit_log,
)


# ---------------------------------------------------------------------------
# record_entry
# ---------------------------------------------------------------------------

def test_record_entry_returns_dict():
    entry = record_entry("deploy", ["prod.yaml"])
    assert isinstance(entry, dict)


def test_record_entry_contains_required_keys():
    entry = record_entry("merge", ["a.yaml", "b.yaml"])
    assert "timestamp" in entry
    assert entry["action"] == "merge"
    assert entry["files"] == ["a.yaml", "b.yaml"]


def test_record_entry_optional_user_and_note():
    entry = record_entry("validate", ["cfg.yaml"], user="alice", note="pre-release")
    assert entry["user"] == "alice"
    assert entry["note"] == "pre-release"


def test_record_entry_empty_action_raises():
    with pytest.raises(AuditError, match="action"):
        record_entry("", ["cfg.yaml"])


def test_record_entry_empty_files_raises():
    with pytest.raises(AuditError, match="files"):
        record_entry("deploy", [])


# ---------------------------------------------------------------------------
# append_audit_log / load_audit_log
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_file(tmp_path):
    return str(tmp_path / "audit.log")


def test_append_and_load_roundtrip(log_file):
    entry = record_entry("deploy", ["prod.yaml"], user="bob")
    append_audit_log(log_file, entry)
    loaded = load_audit_log(log_file)
    assert len(loaded) == 1
    assert loaded[0]["action"] == "deploy"
    assert loaded[0]["user"] == "bob"


def test_append_multiple_entries(log_file):
    for action in ("merge", "validate", "deploy"):
        append_audit_log(log_file, record_entry(action, ["x.yaml"]))
    entries = load_audit_log(log_file)
    assert len(entries) == 3
    assert [e["action"] for e in entries] == ["merge", "validate", "deploy"]


def test_load_audit_log_missing_raises(log_file):
    with pytest.raises(AuditError, match="not found"):
        load_audit_log(log_file)


def test_load_audit_log_malformed_json(log_file):
    with open(log_file, "w") as fh:
        fh.write("not-json\n")
    with pytest.raises(AuditError, match="malformed JSON"):
        load_audit_log(log_file)


def test_load_audit_log_skips_blank_lines(log_file):
    entry = record_entry("lint", ["cfg.yaml"])
    with open(log_file, "w") as fh:
        fh.write("\n")
        fh.write(json.dumps(entry) + "\n")
        fh.write("\n")
    entries = load_audit_log(log_file)
    assert len(entries) == 1


# ---------------------------------------------------------------------------
# summarize_audit_log
# ---------------------------------------------------------------------------

def test_summarize_empty_entries():
    result = summarize_audit_log([])
    assert "No audit entries" in result


def test_summarize_contains_action_and_file():
    entries = [record_entry("deploy", ["prod.yaml"])]
    summary = summarize_audit_log(entries)
    assert "deploy" in summary
    assert "prod.yaml" in summary
