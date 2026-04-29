"""Tests for confctl/cli_trace.py"""

import pytest

from confctl.cli_trace import build_parser, run


@pytest.fixture()
def parser():
    return build_parser()


@pytest.fixture()
def config_pair(tmp_path):
    a = tmp_path / "prod.yaml"
    a.write_text("db:\n  host: prod-db\n  port: 5432\napp: myapp\n")
    b = tmp_path / "staging.yaml"
    b.write_text("db:\n  host: staging-db\napp: myapp\n")
    return str(a), str(b)


def test_build_parser_registers_trace(parser):
    assert parser.prog == "confctl trace"


def test_build_parser_accepts_multiple_files(parser):
    args = parser.parse_args(["a.yaml", "b.yaml"])
    assert args.files == ["a.yaml", "b.yaml"]


def test_build_parser_accepts_key_flag(parser):
    args = parser.parse_args(["--key", "db.host", "a.yaml"])
    assert args.key == "db.host"


def test_build_parser_accepts_k_shorthand(parser):
    args = parser.parse_args(["-k", "app", "a.yaml"])
    assert args.key == "app"


def test_build_parser_default_key_is_none(parser):
    args = parser.parse_args(["a.yaml"])
    assert args.key is None


def test_build_parser_accepts_duplicates_only(parser):
    args = parser.parse_args(["--duplicates-only", "a.yaml"])
    assert args.duplicates_only is True


def test_run_returns_zero_on_found_key(config_pair, capsys):
    p = build_parser()
    args = p.parse_args(["--key", "db.host", config_pair[0], config_pair[1]])
    code = run(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "db.host" in out


def test_run_returns_one_on_missing_key(config_pair, capsys):
    p = build_parser()
    args = p.parse_args(["--key", "no.such.key", config_pair[0]])
    code = run(args)
    assert code == 1


def test_run_all_keys_no_key_flag(config_pair, capsys):
    p = build_parser()
    args = p.parse_args([config_pair[0], config_pair[1]])
    code = run(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "db.host" in out


def test_run_duplicates_only_filters(config_pair, capsys):
    p = build_parser()
    args = p.parse_args(["--duplicates-only", config_pair[0], config_pair[1]])
    code = run(args)
    assert code == 0
    out = capsys.readouterr().out
    # db.host and app appear in both; db.port only in prod
    assert "app" in out
    assert "db.port" not in out


def test_run_returns_one_on_missing_file(tmp_path, capsys):
    p = build_parser()
    args = p.parse_args(["--key", "foo", str(tmp_path / "ghost.yaml")])
    code = run(args)
    assert code == 1
