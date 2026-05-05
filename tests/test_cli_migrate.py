"""Tests for confctl.cli_migrate"""

from __future__ import annotations

import argparse

import pytest
import yaml

from confctl.cli_migrate import build_parser, run


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    return root


@pytest.fixture()
def config_and_rules(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("host: localhost\nport: 5432\ndebug: true\n")
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        "- action: rename\n  from: host\n  to: db_host\n"
        "- action: delete\n  key: debug\n"
    )
    return cfg, rules


def test_build_parser_registers_migrate(parser):
    args = parser.parse_args(["migrate", "cfg.yaml", "rules.yaml"])
    assert args.command == "migrate"


def test_build_parser_accepts_output_flag(parser):
    args = parser.parse_args(["migrate", "cfg.yaml", "rules.yaml", "-o", "out.yaml"])
    assert args.output == "out.yaml"


def test_build_parser_accepts_in_place_flag(parser):
    args = parser.parse_args(["migrate", "cfg.yaml", "rules.yaml", "--in-place"])
    assert args.in_place is True


def test_build_parser_default_no_in_place(parser):
    args = parser.parse_args(["migrate", "cfg.yaml", "rules.yaml"])
    assert args.in_place is False


def test_run_prints_migrated_to_stdout(config_and_rules, capsys):
    cfg, rules = config_and_rules
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["migrate", str(cfg), str(rules)])
    rc = run(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = yaml.safe_load(out)
    assert "db_host" in data
    assert "host" not in data
    assert "debug" not in data


def test_run_writes_output_file(config_and_rules, tmp_path):
    cfg, rules = config_and_rules
    out_file = tmp_path / "migrated.yaml"
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["migrate", str(cfg), str(rules), "-o", str(out_file)])
    rc = run(args)
    assert rc == 0
    assert out_file.exists()
    data = yaml.safe_load(out_file.read_text())
    assert "db_host" in data


def test_run_in_place_overwrites_config(config_and_rules):
    cfg, rules = config_and_rules
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["migrate", str(cfg), str(rules), "--in-place"])
    rc = run(args)
    assert rc == 0
    data = yaml.safe_load(cfg.read_text())
    assert "db_host" in data


def test_run_returns_1_on_missing_config(tmp_path, capsys):
    rules = tmp_path / "rules.yaml"
    rules.write_text("[]")
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    args = root.parse_args(["migrate", str(tmp_path / "nope.yaml"), str(rules)])
    rc = run(args)
    assert rc == 1
    assert "migrate error" in capsys.readouterr().err
