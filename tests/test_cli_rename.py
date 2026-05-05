"""Tests for confctl.cli_rename."""

from __future__ import annotations

import argparse

import pytest
import yaml

from confctl.cli_rename import _parse_renames, build_parser, run


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    return root


@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text("old_host: localhost\nport: 5432\n")
    return f


def test_build_parser_registers_rename(parser):
    args = parser.parse_args(["rename", "cfg.yaml", "--rename", "a=b"])
    assert args.command == "rename"


def test_build_parser_accepts_rename_flag(parser):
    args = parser.parse_args(["rename", "f.yaml", "--rename", "old=new"])
    assert args.renames == ["old=new"]


def test_build_parser_accepts_multiple_renames(parser):
    args = parser.parse_args(
        ["rename", "f.yaml", "--rename", "a=b", "--rename", "x=y"]
    )
    assert len(args.renames) == 2


def test_build_parser_accepts_output_flag(parser):
    args = parser.parse_args(["rename", "f.yaml", "--rename", "a=b", "--output", "out.yaml"])
    assert args.output == "out.yaml"


def test_build_parser_accepts_in_place_flag(parser):
    args = parser.parse_args(["rename", "f.yaml", "--rename", "a=b", "--in-place"])
    assert args.in_place is True


def test_parse_renames_valid():
    result = _parse_renames(["old=new", "x.y=a.b"])
    assert result == {"old": "new", "x.y": "a.b"}


def test_parse_renames_invalid_raises():
    with pytest.raises(ValueError, match="Invalid rename spec"):
        _parse_renames(["no_equals_sign"])


def test_run_prints_to_stdout(config_file, capsys):
    args = argparse.Namespace(
        file=str(config_file),
        renames=["old_host=hostname"],
        output=None,
        in_place=False,
    )
    rc = run(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = yaml.safe_load(out)
    assert "hostname" in data
    assert "old_host" not in data


def test_run_writes_output_file(config_file, tmp_path):
    out_file = tmp_path / "result.yaml"
    args = argparse.Namespace(
        file=str(config_file),
        renames=["old_host=hostname"],
        output=str(out_file),
        in_place=False,
    )
    rc = run(args)
    assert rc == 0
    assert out_file.exists()
    data = yaml.safe_load(out_file.read_text())
    assert "hostname" in data


def test_run_in_place(config_file):
    args = argparse.Namespace(
        file=str(config_file),
        renames=["old_host=hostname"],
        output=None,
        in_place=True,
    )
    rc = run(args)
    assert rc == 0
    data = yaml.safe_load(config_file.read_text())
    assert "hostname" in data


def test_run_returns_1_on_missing_key(config_file, capsys):
    args = argparse.Namespace(
        file=str(config_file),
        renames=["nonexistent=new_key"],
        output=None,
        in_place=False,
    )
    rc = run(args)
    assert rc == 1
    assert "rename error" in capsys.readouterr().err
