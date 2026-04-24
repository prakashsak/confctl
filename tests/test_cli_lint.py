"""Tests for confctl.cli_lint module."""

from __future__ import annotations

import argparse
import io

import pytest

from confctl.cli_lint import build_parser, run


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    build_parser(subs)
    return root


@pytest.fixture()
def clean_config(tmp_path):
    f = tmp_path / "clean.yaml"
    f.write_text("host: localhost\nport: 5432\n")
    return str(f)


@pytest.fixture()
def dirty_config(tmp_path):
    f = tmp_path / "dirty.yaml"
    f.write_text("host: localhost  \nport: 5432\n")
    return str(f)


def test_build_parser_registers_lint(parser):
    args = parser.parse_args(["lint", "a.yaml"])
    assert args.command == "lint"


def test_build_parser_accepts_multiple_files(parser):
    args = parser.parse_args(["lint", "a.yaml", "b.yaml"])
    assert args.files == ["a.yaml", "b.yaml"]


def test_build_parser_strict_flag_default_false(parser):
    args = parser.parse_args(["lint", "a.yaml"])
    assert args.strict is False


def test_build_parser_strict_flag_can_be_set(parser):
    args = parser.parse_args(["lint", "--strict", "a.yaml"])
    assert args.strict is True


def test_run_clean_file_returns_zero_and_no_output(clean_config):
    args = argparse.Namespace(files=[clean_config], strict=False)
    out, err = io.StringIO(), io.StringIO()
    code = run(args, stdout=out, stderr=err)
    assert code == 0
    assert out.getvalue() == ""


def test_run_dirty_file_prints_warnings(dirty_config):
    args = argparse.Namespace(files=[dirty_config], strict=False)
    out, err = io.StringIO(), io.StringIO()
    code = run(args, stdout=out, stderr=err)
    assert code == 0
    assert "trailing whitespace" in out.getvalue()


def test_run_strict_with_warnings_returns_one(dirty_config):
    args = argparse.Namespace(files=[dirty_config], strict=True)
    out, err = io.StringIO(), io.StringIO()
    code = run(args, stdout=out, stderr=err)
    assert code == 1


def test_run_missing_file_returns_two():
    args = argparse.Namespace(files=["/no/such/file.yaml"], strict=False)
    out, err = io.StringIO(), io.StringIO()
    code = run(args, stdout=out, stderr=err)
    assert code == 2
    assert "ERROR" in err.getvalue()


def test_run_multiple_files_all_clean(clean_config):
    args = argparse.Namespace(files=[clean_config, clean_config], strict=True)
    out, err = io.StringIO(), io.StringIO()
    code = run(args, stdout=out, stderr=err)
    assert code == 0
