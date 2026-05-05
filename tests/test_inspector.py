"""Tests for confctl.inspector and confctl.cli_inspect."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from confctl.inspector import (
    InspectError,
    load_yaml_for_inspect,
    inspect_config,
    format_inspection,
)
from confctl.cli_inspect import build_parser, run


@pytest.fixture()
def yaml_config(tmp_path: Path) -> Path:
    f = tmp_path / "config.yaml"
    f.write_text(
        "database:\n"
        "  host: localhost\n"
        "  port: 5432\n"
        "  password: null\n"
        "app:\n"
        "  debug: true\n"
        "  workers: 4\n"
    )
    return f


@pytest.fixture()
def empty_yaml(tmp_path: Path) -> Path:
    f = tmp_path / "empty.yaml"
    f.write_text("")
    return f


def test_load_yaml_for_inspect_returns_dict(yaml_config):
    data = load_yaml_for_inspect(str(yaml_config))
    assert isinstance(data, dict)
    assert "database" in data


def test_load_yaml_for_inspect_missing_raises(tmp_path):
    with pytest.raises(InspectError, match="File not found"):
        load_yaml_for_inspect(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_inspect_empty_returns_empty(empty_yaml):
    data = load_yaml_for_inspect(str(empty_yaml))
    assert data == {}


def test_load_yaml_for_inspect_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(InspectError, match="Expected a YAML mapping"):
        load_yaml_for_inspect(str(f))


def test_inspect_config_top_level_keys(yaml_config):
    report = inspect_config(str(yaml_config))
    assert set(report["top_level_keys"]) == {"database", "app"}


def test_inspect_config_total_keys(yaml_config):
    report = inspect_config(str(yaml_config))
    # database(1) + host(1) + port(1) + password(1) + app(1) + debug(1) + workers(1) = 7
    assert report["total_keys"] == 7


def test_inspect_config_max_depth(yaml_config):
    report = inspect_config(str(yaml_config))
    assert report["max_depth"] == 2


def test_inspect_config_null_keys(yaml_config):
    report = inspect_config(str(yaml_config))
    assert "password" in report["null_keys"]


def test_inspect_config_value_types(yaml_config):
    report = inspect_config(str(yaml_config))
    assert "str" in report["value_types"]
    assert "int" in report["value_types"]
    assert "bool" in report["value_types"]


def test_format_inspection_contains_path(yaml_config):
    report = inspect_config(str(yaml_config))
    output = format_inspection(report)
    assert str(yaml_config) in output


def test_format_inspection_contains_total_keys(yaml_config):
    report = inspect_config(str(yaml_config))
    output = format_inspection(report)
    assert "Total keys" in output


def test_build_parser_registers_inspect():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_parser(sub)
    args = root.parse_args(["inspect", "a.yaml"])
    assert args.files == ["a.yaml"]


def test_build_parser_accepts_json_flag():
    parser = build_parser()
    args = parser.parse_args(["--json", "a.yaml"])
    assert args.json is True


def test_run_prints_report(yaml_config, capsys):
    parser = build_parser()
    args = parser.parse_args([str(yaml_config)])
    code = run(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "Total keys" in out


def test_run_json_output(yaml_config, capsys):
    parser = build_parser()
    args = parser.parse_args(["--json", str(yaml_config)])
    code = run(args)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["total_keys"] == 7


def test_run_missing_file_returns_nonzero(tmp_path, capsys):
    parser = build_parser()
    args = parser.parse_args([str(tmp_path / "nope.yaml")])
    code = run(args)
    assert code == 1
    err = capsys.readouterr().err
    assert "ERROR" in err
