"""Tests for confctl.cli_merge (the 'merge' sub-command)."""

from __future__ import annotations

import argparse

import pytest
import yaml

from confctl.cli_merge import build_parser, run


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser(prog="confctl")
    sub = root.add_subparsers()
    build_parser(sub)
    return root


@pytest.fixture()
def config_pair(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text("service:\n  name: myapp\n  replicas: 1\n")
    env = tmp_path / "staging.yaml"
    env.write_text("service:\n  replicas: 3\n  env: staging\n")
    return base, env, tmp_path


def test_build_parser_registers_merge(parser):
    args = parser.parse_args(["merge", "base.yaml", "env.yaml"])
    assert hasattr(args, "func")
    assert args.func.__module__ == "confctl.cli_merge"


def test_run_prints_merged_to_stdout(config_pair, capsys):
    base, env, _ = config_pair
    args = argparse.Namespace(base=base, env=env, output=None)
    code = run(args)
    assert code == 0
    captured = capsys.readouterr()
    data = yaml.safe_load(captured.out)
    assert data["service"]["replicas"] == 3
    assert data["service"]["name"] == "myapp"
    assert data["service"]["env"] == "staging"


def test_run_writes_output_file(config_pair):
    base, env, tmp_path = config_pair
    out = tmp_path / "merged.yaml"
    args = argparse.Namespace(base=base, env=env, output=out)
    code = run(args)
    assert code == 0
    assert out.exists()
    data = yaml.safe_load(out.read_text())
    assert data["service"]["replicas"] == 3


def test_run_missing_base_returns_error(config_pair, capsys):
    _, env, tmp_path = config_pair
    args = argparse.Namespace(base=tmp_path / "ghost.yaml", env=env, output=None)
    code = run(args)
    assert code == 1
    assert "error" in capsys.readouterr().err.lower()


def test_run_missing_env_returns_error(config_pair, capsys):
    base, _, tmp_path = config_pair
    args = argparse.Namespace(base=base, env=tmp_path / "ghost.yaml", output=None)
    code = run(args)
    assert code == 1
