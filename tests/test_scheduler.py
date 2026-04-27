"""Tests for confctl.scheduler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from confctl.scheduler import (
    ScheduleError,
    create_job,
    list_pending,
    load_schedule,
    mark_done,
    save_schedule,
)

VALID_TS = "2025-06-01T12:00:00+00:00"


# ---------------------------------------------------------------------------
# create_job
# ---------------------------------------------------------------------------

def test_create_job_returns_dict():
    job = create_job("merge", ["a.yaml"], VALID_TS)
    assert isinstance(job, dict)


def test_create_job_required_fields():
    job = create_job("validate", ["cfg.yaml"], VALID_TS, note="nightly")
    assert job["action"] == "validate"
    assert job["files"] == ["cfg.yaml"]
    assert job["run_at"] == VALID_TS
    assert job["status"] == "pending"
    assert job["note"] == "nightly"
    assert "created_at" in job


def test_create_job_empty_action_raises():
    with pytest.raises(ScheduleError, match="action"):
        create_job("", ["a.yaml"], VALID_TS)


def test_create_job_empty_files_raises():
    with pytest.raises(ScheduleError, match="files"):
        create_job("merge", [], VALID_TS)


def test_create_job_invalid_timestamp_raises():
    with pytest.raises(ScheduleError, match="run_at"):
        create_job("merge", ["a.yaml"], "not-a-date")


def test_create_job_args_defaults_to_empty_dict():
    job = create_job("diff", ["x.yaml"], VALID_TS)
    assert job["args"] == {}


# ---------------------------------------------------------------------------
# save_schedule / load_schedule
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path: Path):
    schedule_file = tmp_path / "sched.json"
    jobs = [create_job("merge", ["a.yaml"], VALID_TS)]
    save_schedule(jobs, schedule_file)
    loaded = load_schedule(schedule_file)
    assert len(loaded) == 1
    assert loaded[0]["action"] == "merge"


def test_load_schedule_missing_returns_empty(tmp_path: Path):
    result = load_schedule(tmp_path / "ghost.json")
    assert result == []


def test_load_schedule_corrupt_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(ScheduleError, match="corrupt"):
        load_schedule(bad)


def test_load_schedule_non_array_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    with pytest.raises(ScheduleError, match="array"):
        load_schedule(bad)


# ---------------------------------------------------------------------------
# list_pending / mark_done
# ---------------------------------------------------------------------------

def test_list_pending_filters_correctly():
    jobs = [
        {"status": "pending", "action": "a"},
        {"status": "done", "action": "b"},
        {"status": "pending", "action": "c"},
    ]
    pending = list_pending(jobs)
    assert len(pending) == 2
    assert all(j["status"] == "pending" for j in pending)


def test_mark_done_updates_status():
    jobs = [create_job("merge", ["a.yaml"], VALID_TS)]
    updated = mark_done(jobs, 0)
    assert updated[0]["status"] == "done"


def test_mark_done_does_not_mutate_original():
    jobs = [create_job("merge", ["a.yaml"], VALID_TS)]
    mark_done(jobs, 0)
    assert jobs[0]["status"] == "pending"


def test_mark_done_out_of_range_raises():
    jobs = [create_job("merge", ["a.yaml"], VALID_TS)]
    with pytest.raises(ScheduleError, match="out of range"):
        mark_done(jobs, 5)
