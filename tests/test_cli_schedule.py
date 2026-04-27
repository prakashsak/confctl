"""Tests for confctl.cli_schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from confctl.cli_schedule import build_parser, run

VALID_TS = "2025-06-01T12:00:00+00:00"


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    return root


@pytest.fixture()
def schedule_file(tmp_path: Path) -> Path:
    return tmp_path / "schedule.json"


def test_build_parser_registers_schedule(parser: argparse.ArgumentParser):
    args = parser.parse_args([
        "schedule", "add", "merge", "a.yaml",
        "--run-at", VALID_TS, "--schedule-file", "/tmp/s.json",
    ])
    assert args.command == "schedule"
    assert args.schedule_cmd == "add"


def test_run_add_creates_job(parser: argparse.ArgumentParser, schedule_file: Path):
    args = parser.parse_args([
        "schedule", "add", "merge", "a.yaml", "b.yaml",
        "--run-at", VALID_TS,
        "--schedule-file", str(schedule_file),
    ])
    rc = run(args)
    assert rc == 0
    data = json.loads(schedule_file.read_text())
    assert len(data) == 1
    assert data[0]["action"] == "merge"


def test_run_list_pending(parser: argparse.ArgumentParser, schedule_file: Path, capsys):
    # add a job first
    add_args = parser.parse_args([
        "schedule", "add", "validate", "cfg.yaml",
        "--run-at", VALID_TS,
        "--schedule-file", str(schedule_file),
    ])
    run(add_args)

    list_args = parser.parse_args([
        "schedule", "list",
        "--schedule-file", str(schedule_file),
    ])
    rc = run(list_args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "validate" in captured.out


def test_run_list_empty(parser: argparse.ArgumentParser, schedule_file: Path, capsys):
    args = parser.parse_args([
        "schedule", "list",
        "--schedule-file", str(schedule_file),
    ])
    rc = run(args)
    assert rc == 0
    assert "No jobs" in capsys.readouterr().out


def test_run_done_marks_job(parser: argparse.ArgumentParser, schedule_file: Path):
    add_args = parser.parse_args([
        "schedule", "add", "diff", "x.yaml",
        "--run-at", VALID_TS,
        "--schedule-file", str(schedule_file),
    ])
    run(add_args)

    done_args = parser.parse_args([
        "schedule", "done", "0",
        "--schedule-file", str(schedule_file),
    ])
    rc = run(done_args)
    assert rc == 0
    data = json.loads(schedule_file.read_text())
    assert data[0]["status"] == "done"


def test_run_done_bad_index_returns_1(parser: argparse.ArgumentParser, schedule_file: Path):
    add_args = parser.parse_args([
        "schedule", "add", "diff", "x.yaml",
        "--run-at", VALID_TS,
        "--schedule-file", str(schedule_file),
    ])
    run(add_args)

    done_args = parser.parse_args([
        "schedule", "done", "99",
        "--schedule-file", str(schedule_file),
    ])
    assert run(done_args) == 1
