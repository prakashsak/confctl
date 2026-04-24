"""Tests for confctl.cli_diff."""

import argparse
import textwrap
from io import StringIO
from pathlib import Path

import pytest

from confctl.cli_diff import build_parser, run


@pytest.fixture()
def parser():
    return build_parser()


@pytest.fixture()
def config_pair(tmp_path):
    file_a = tmp_path / "base.conf"
    file_b = tmp_path / "prod.conf"
    file_a.write_text("host: localhost\nport: 5432\n")
    file_b.write_text("host: db.prod.example.com\nport: 5432\n")
    return str(file_a), str(file_b)


def test_build_parser_registers_diff(parser):
    assert parser.prog in ("confctl diff", "diff")


def test_build_parser_accepts_two_files(parser):
    args = parser.parse_args(["a.conf", "b.conf"])
    assert args.file_a == "a.conf"
    assert args.file_b == "b.conf"


def test_build_parser_accepts_no_color_flag(parser):
    args = parser.parse_args(["a.conf", "b.conf", "--no-color"])
    assert args.no_color is True


def test_build_parser_accepts_label_overrides(parser):
    args = parser.parse_args(
        ["a.conf", "b.conf", "--label-a", "base", "--label-b", "prod"]
    )
    assert args.label_a == "base"
    assert args.label_b == "prod"


def test_run_prints_diff_when_files_differ(config_pair, parser):
    file_a, file_b = config_pair
    args = parser.parse_args([file_a, file_b, "--no-color"])
    out = StringIO()
    exit_code = run(args, stdout=out)
    output = out.getvalue()
    assert "-host: localhost" in output or "host: localhost" in output
    assert exit_code == 1


def test_run_reports_identical_files(tmp_path, parser):
    file_a = tmp_path / "a.conf"
    file_b = tmp_path / "b.conf"
    content = "host: localhost\nport: 5432\n"
    file_a.write_text(content)
    file_b.write_text(content)
    args = parser.parse_args([str(file_a), str(file_b), "--no-color"])
    out = StringIO()
    exit_code = run(args, stdout=out)
    assert "identical" in out.getvalue().lower()
    assert exit_code == 0


def test_run_uses_label_overrides_in_output(config_pair, parser):
    file_a, file_b = config_pair
    args = parser.parse_args(
        [file_a, file_b, "--no-color", "--label-a", "base", "--label-b", "prod"]
    )
    out = StringIO()
    run(args, stdout=out)
    output = out.getvalue()
    assert "base" in output
    assert "prod" in output
