"""Tests for confctl.cli_validate module."""

from __future__ import annotations

import argparse
import io

import pytest

from confctl.cli_validate import build_parser, run


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser(prog="confctl")
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    return root


@pytest.fixture()
def valid_configs(tmp_path):
    f1 = tmp_path / "base.yaml"
    f1.write_text("env: base\nservice: api\n")
    f2 = tmp_path / "prod.yaml"
    f2.write_text("env: prod\nservice: api\n")
    return [str(f1), str(f2)]


def test_build_parser_registers_validate(parser):
    args = parser.parse_args(["validate", "some.yaml"])
    assert args.command == "validate"


def test_build_parser_accepts_multiple_files(parser, valid_configs):
    args = parser.parse_args(["validate"] + valid_configs)
    assert len(args.configs) == 2


def test_build_parser_accepts_require_flag(parser, valid_configs):
    args = parser.parse_args(["validate", valid_configs[0], "--require", "env", "service"])
    assert args.required_keys == ["env", "service"]


def test_run_prints_ok_for_valid_files(valid_configs):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["validate"] + valid_configs)
    out = io.StringIO()
    code = run(args, stdout=out)
    assert code == 0
    output = out.getvalue()
    for path in valid_configs:
        assert f"OK  {path}" in output


def test_run_returns_1_for_missing_file(tmp_path):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    ghost = str(tmp_path / "ghost.yaml")
    args = root.parse_args(["validate", ghost])
    err = io.StringIO()
    code = run(args, stderr=err)
    assert code == 1


def test_run_returns_1_for_invalid_structure(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- a\n- b\n")
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["validate", str(bad)])
    err = io.StringIO()
    code = run(args, stderr=err)
    assert code == 1
    assert "Validation failed" in err.getvalue()


def test_run_validates_required_keys(valid_configs):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["validate"] + valid_configs + ["--require", "env", "service"])
    out = io.StringIO()
    code = run(args, stdout=out)
    assert code == 0


def test_run_fails_missing_required_key(valid_configs):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["validate"] + valid_configs + ["--require", "nonexistent_key"])
    err = io.StringIO()
    code = run(args, stderr=err)
    assert code == 1
