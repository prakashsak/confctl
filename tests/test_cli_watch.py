"""Tests for confctl.cli_watch."""

import sys
import pytest
from unittest.mock import patch, MagicMock

from confctl.cli_watch import build_parser, run


@pytest.fixture
def parser():
    return build_parser()


@pytest.fixture
def config_pair(tmp_path):
    a = tmp_path / "app.yaml"
    b = tmp_path / "db.yaml"
    a.write_text("env: prod\n")
    b.write_text("host: localhost\n")
    return str(a), str(b)


def test_build_parser_registers_watch(parser):
    assert parser.prog.endswith("watch")


def test_build_parser_accepts_multiple_files(parser, config_pair):
    args = parser.parse_args(list(config_pair))
    assert len(args.files) == 2


def test_build_parser_default_interval(parser, config_pair):
    args = parser.parse_args([config_pair[0]])
    assert args.interval == 1.0


def test_build_parser_custom_interval(parser, config_pair):
    args = parser.parse_args(["--interval", "0.5", config_pair[0]])
    assert args.interval == 0.5


def test_build_parser_max_cycles(parser, config_pair):
    args = parser.parse_args(["--max-cycles", "3", config_pair[0]])
    assert args.max_cycles == 3


def test_build_parser_default_max_cycles_is_none(parser, config_pair):
    args = parser.parse_args([config_pair[0]])
    assert args.max_cycles is None


def test_run_exits_on_missing_file(tmp_path, capsys):
    p = build_parser()
    args = p.parse_args([str(tmp_path / "missing.yaml")])
    with pytest.raises(SystemExit) as exc_info:
        run(args)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_calls_watch_with_correct_args(config_pair):
    p = build_parser()
    args = p.parse_args(["--interval", "0.1", "--max-cycles", "0", config_pair[0]])
    with patch("confctl.cli_watch.watch") as mock_watch:
        run(args)
        mock_watch.assert_called_once()
        call_kwargs = mock_watch.call_args
        assert call_kwargs.kwargs["interval"] == 0.1
        assert call_kwargs.kwargs["max_cycles"] == 0


def test_on_change_output(config_pair, capsys):
    from confctl.cli_watch import _on_change
    _on_change({config_pair[0]: "modified"})
    captured = capsys.readouterr()
    assert "MODIFIED" in captured.out
    assert config_pair[0] in captured.out
