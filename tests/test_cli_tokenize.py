"""Tests for confctl.cli_tokenize."""

from __future__ import annotations

import json
import pytest

from confctl.cli_tokenize import build_parser, run


@pytest.fixture
def parser():
    return build_parser()


@pytest.fixture
def yaml_config(tmp_path):
    cfg = tmp_path / "app.yaml"
    cfg.write_text(
        "server:\n"
        "  host: ${HOST}\n"
        "  port: 8080\n"
        "  url: https://example.com\n"
    )
    return str(cfg)


def test_build_parser_registers_tokenize(parser):
    assert parser.prog == "confctl tokenize"


def test_build_parser_accepts_multiple_files(parser):
    args = parser.parse_args(["a.yaml", "b.yaml"])
    assert args.files == ["a.yaml", "b.yaml"]


def test_build_parser_default_format(parser):
    args = parser.parse_args(["a.yaml"])
    assert args.format == "summary"


def test_build_parser_accepts_json_format(parser):
    args = parser.parse_args(["--format", "json", "a.yaml"])
    assert args.format == "json"


def test_build_parser_accepts_key_flag(parser):
    args = parser.parse_args(["--key", "server.host", "a.yaml"])
    assert args.key == "server.host"


def test_run_summary_output(yaml_config, capsys):
    parser = build_parser()
    args = parser.parse_args([yaml_config])
    code = run(args)
    captured = capsys.readouterr()
    assert code == 0
    assert "server.port" in captured.out


def test_run_json_output(yaml_config, capsys):
    parser = build_parser()
    args = parser.parse_args(["--format", "json", yaml_config])
    code = run(args)
    captured = capsys.readouterr()
    assert code == 0
    lines = captured.out.split("\n")
    json_start = next(i for i, l in enumerate(lines) if l.strip().startswith("{"))
    parsed = json.loads("\n".join(lines[json_start:]))
    assert "server.port" in parsed


def test_run_missing_file_returns_nonzero(tmp_path, capsys):
    parser = build_parser()
    args = parser.parse_args([str(tmp_path / "missing.yaml")])
    code = run(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.err


def test_run_key_filter(yaml_config, capsys):
    parser = build_parser()
    args = parser.parse_args(["--key", "server.port", yaml_config])
    code = run(args)
    captured = capsys.readouterr()
    assert code == 0
    assert "server.port" in captured.out
    assert "server.host" not in captured.out
