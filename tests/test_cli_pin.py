"""Tests for confctl.cli_pin."""

from __future__ import annotations

import argparse
import json
import sys

import pytest

from confctl.cli_pin import build_parser, run


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    build_parser(subs)
    return root


@pytest.fixture()
def config_pair(tmp_path):
    a = tmp_path / "cfg_a.yaml"
    b = tmp_path / "cfg_b.yaml"
    a.write_text("x: 1\n")
    b.write_text("y: 2\n")
    return str(a), str(b), tmp_path


def test_build_parser_registers_pin(parser):
    args = parser.parse_args(["pin", "create", "--output", "out.json", "f.yaml"])
    assert args.command == "pin"


def test_build_parser_create_subcommand(parser):
    args = parser.parse_args(["pin", "create", "--output", "out.json", "f.yaml"])
    assert args.pin_cmd == "create"
    assert args.output == "out.json"
    assert "f.yaml" in args.files


def test_build_parser_verify_subcommand(parser):
    args = parser.parse_args(["pin", "verify", "pins.json"])
    assert args.pin_cmd == "verify"
    assert args.pin_file == "pins.json"
    assert args.exit_code is False


def test_build_parser_verify_exit_code_flag(parser):
    args = parser.parse_args(["pin", "verify", "--exit-code", "pins.json"])
    assert args.exit_code is True


def test_run_create_writes_pin_file(config_pair, capsys):
    a, b, tmp = config_pair
    out = str(tmp / "pins.json")
    args = argparse.Namespace(pin_cmd="create", files=[a, b], output=out)
    run(args)
    with open(out) as fh:
        data = json.load(fh)
    assert len(data) == 2
    captured = capsys.readouterr()
    assert "Pinned 2" in captured.out


def test_run_verify_prints_summary(config_pair, capsys):
    a, b, tmp = config_pair
    out = str(tmp / "pins.json")
    create_args = argparse.Namespace(pin_cmd="create", files=[a, b], output=out)
    run(create_args)
    verify_args = argparse.Namespace(pin_cmd="verify", pin_file=out, exit_code=False)
    run(verify_args)
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_run_verify_exits_1_on_change(config_pair):
    a, b, tmp = config_pair
    out = str(tmp / "pins.json")
    create_args = argparse.Namespace(pin_cmd="create", files=[a, b], output=out)
    run(create_args)
    with open(a, "a") as fh:
        fh.write("changed: true\n")
    verify_args = argparse.Namespace(pin_cmd="verify", pin_file=out, exit_code=True)
    with pytest.raises(SystemExit) as exc_info:
        run(verify_args)
    assert exc_info.value.code == 1


def test_run_create_missing_file_exits(tmp_path):
    args = argparse.Namespace(
        pin_cmd="create",
        files=[str(tmp_path / "ghost.yaml")],
        output=str(tmp_path / "out.json"),
    )
    with pytest.raises(SystemExit) as exc_info:
        run(args)
    assert exc_info.value.code == 1
