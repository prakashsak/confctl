"""Tests for confctl.cli_render module."""

import argparse

import pytest

from confctl.cli_render import _parse_variables, build_parser, run


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_parser(sub)
    return root


@pytest.fixture
def template_file(tmp_path):
    t = tmp_path / "app.tmpl"
    t.write_text("host={{ host }}\nport={{ port }}\n")
    return t


def test_build_parser_registers_render(parser):
    args = parser.parse_args(["render", "config.tmpl"])
    assert args.command == "render"


def test_build_parser_accepts_set_flag(parser):
    args = parser.parse_args(["render", "t.tmpl", "--set", "host=localhost"])
    assert args.variables == ["host=localhost"]


def test_build_parser_accepts_output_flag(parser):
    args = parser.parse_args(["render", "t.tmpl", "-o", "out.conf"])
    assert args.output == "out.conf"


def test_build_parser_default_output_is_none(parser):
    args = parser.parse_args(["render", "t.tmpl"])
    assert args.output is None


def test_parse_variables_returns_dict():
    result = _parse_variables(["host=localhost", "port=5432"])
    assert result == {"host": "localhost", "port": "5432"}


def test_parse_variables_invalid_format_raises():
    with pytest.raises(ValueError, match="KEY=VALUE"):
        _parse_variables(["badvalue"])


def test_run_prints_to_stdout(template_file, capsys):
    args = argparse.Namespace(
        template=str(template_file),
        variables=["host=db.local", "port=3306"],
        output=None,
    )
    run(args)
    captured = capsys.readouterr()
    assert "host=db.local" in captured.out
    assert "port=3306" in captured.out


def test_run_writes_output_file(template_file, tmp_path):
    out_file = tmp_path / "result.conf"
    args = argparse.Namespace(
        template=str(template_file),
        variables=["host=srv", "port=80"],
        output=str(out_file),
    )
    run(args)
    content = out_file.read_text()
    assert "host=srv" in content


def test_run_missing_variable_exits(template_file):
    args = argparse.Namespace(
        template=str(template_file),
        variables=["host=only"],
        output=None,
    )
    with pytest.raises(SystemExit) as exc_info:
        run(args)
    assert exc_info.value.code == 1
