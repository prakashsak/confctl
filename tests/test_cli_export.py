"""Tests for confctl.cli_export."""

import argparse
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from confctl.cli_export import build_parser, run


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return build_parser()


@pytest.fixture()
def yaml_config(tmp_path) -> Path:
    cfg = tmp_path / "app.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            service:
              name: myapp
              port: 8080
            debug: false
        """)
    )
    return cfg


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_registers_export(parser):
    assert parser.prog == "confctl export"


def test_build_parser_default_format(parser, yaml_config):
    args = parser.parse_args([str(yaml_config)])
    assert args.fmt == "json"


def test_build_parser_accepts_format_flag(parser, yaml_config):
    args = parser.parse_args([str(yaml_config), "--format", "env"])
    assert args.fmt == "env"


def test_build_parser_short_format_flag(parser, yaml_config):
    args = parser.parse_args([str(yaml_config), "-f", "yaml"])
    assert args.fmt == "yaml"


def test_build_parser_accepts_output_flag(parser, yaml_config, tmp_path):
    out = str(tmp_path / "result.json")
    args = parser.parse_args([str(yaml_config), "--output", out])
    assert args.output == out


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def test_run_prints_json_to_stdout(parser, yaml_config, capsys):
    args = parser.parse_args([str(yaml_config), "-f", "json"])
    rc = run(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert '"name": "myapp"' in captured.out


def test_run_prints_env_to_stdout(parser, yaml_config, capsys):
    args = parser.parse_args([str(yaml_config), "-f", "env"])
    rc = run(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "SERVICE_NAME=myapp" in captured.out


def test_run_writes_output_file(parser, yaml_config, tmp_path):
    out = tmp_path / "exported.json"
    args = parser.parse_args([str(yaml_config), "-f", "json", "-o", str(out)])
    rc = run(args)
    assert rc == 0
    assert out.exists()
    assert "myapp" in out.read_text()


def test_run_missing_file_returns_error(parser, tmp_path, capsys):
    args = parser.parse_args([str(tmp_path / "ghost.yaml")])
    rc = run(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err.lower()


def test_run_registers_as_subcommand():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_parser(subs)
    args = root.parse_args(["export", "some.yaml", "-f", "env"])
    assert args.fmt == "env"
