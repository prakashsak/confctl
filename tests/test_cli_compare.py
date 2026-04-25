"""Tests for confctl.cli_compare."""

from __future__ import annotations

import argparse

import pytest

from confctl.cli_compare import build_parser, run


@pytest.fixture()
def parser():
    return build_parser()


@pytest.fixture()
def config_dirs(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "app.yaml").write_text("host: localhost\n")
    (right / "app.yaml").write_text("host: prod.example.com\n")
    return left, right


def test_build_parser_registers_compare(parser):
    assert parser.prog == "confctl compare"


def test_build_parser_accepts_two_dirs(parser):
    args = parser.parse_args(["left_dir", "right_dir"])
    assert args.left == "left_dir"
    assert args.right == "right_dir"


def test_build_parser_exit_code_default_false(parser):
    args = parser.parse_args(["l", "r"])
    assert args.exit_code is False


def test_build_parser_accepts_exit_code_flag(parser):
    args = parser.parse_args(["l", "r", "--exit-code"])
    assert args.exit_code is True


def test_build_parser_accepts_quiet_flag(parser):
    args = parser.parse_args(["l", "r", "--quiet"])
    assert args.quiet is True


def test_run_returns_zero_no_diff(tmp_path, capsys):
    left = tmp_path / "l"
    right = tmp_path / "r"
    left.mkdir()
    right.mkdir()
    content = "key: value\n"
    (left / "cfg.yaml").write_text(content)
    (right / "cfg.yaml").write_text(content)
    args = argparse.Namespace(left=str(left), right=str(right), exit_code=True, quiet=False)
    assert run(args) == 0


def test_run_returns_one_with_diff_and_exit_code(config_dirs):
    left, right = config_dirs
    args = argparse.Namespace(left=str(left), right=str(right), exit_code=True, quiet=False)
    assert run(args) == 1


def test_run_returns_zero_with_diff_no_exit_code(config_dirs):
    left, right = config_dirs
    args = argparse.Namespace(left=str(left), right=str(right), exit_code=False, quiet=False)
    assert run(args) == 0


def test_run_prints_output(config_dirs, capsys):
    left, right = config_dirs
    args = argparse.Namespace(left=str(left), right=str(right), exit_code=False, quiet=False)
    run(args)
    captured = capsys.readouterr()
    assert "app.yaml" in captured.out


def test_run_quiet_suppresses_output(config_dirs, capsys):
    left, right = config_dirs
    args = argparse.Namespace(left=str(left), right=str(right), exit_code=False, quiet=True)
    run(args)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_run_missing_dir_returns_two(tmp_path, capsys):
    args = argparse.Namespace(
        left=str(tmp_path / "nope"), right=str(tmp_path), exit_code=False, quiet=False
    )
    assert run(args) == 2
