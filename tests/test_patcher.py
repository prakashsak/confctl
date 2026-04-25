"""Tests for confctl.patcher and confctl.cli_patch."""

from __future__ import annotations

import argparse

import pytest
import yaml

from confctl.patcher import (
    PatchError,
    apply_patch,
    dump_patched,
    load_yaml_for_patch,
    patch_config,
)
from confctl.cli_patch import _parse_patches, build_parser, run


@pytest.fixture()
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("database:\n  host: localhost\n  port: 5432\napp:\n  debug: false\n")
    return str(cfg)


# --- load_yaml_for_patch ---

def test_load_yaml_for_patch_returns_dict(yaml_config):
    data = load_yaml_for_patch(yaml_config)
    assert isinstance(data, dict)
    assert data["database"]["host"] == "localhost"


def test_load_yaml_for_patch_missing_raises(tmp_path):
    with pytest.raises(PatchError, match="File not found"):
        load_yaml_for_patch(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_patch_empty_returns_empty(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    assert load_yaml_for_patch(str(f)) == {}


def test_load_yaml_for_patch_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(PatchError, match="Expected a YAML mapping"):
        load_yaml_for_patch(str(f))


# --- apply_patch ---

def test_apply_patch_sets_top_level_key():
    data = {"key": "old"}
    result = apply_patch(data, {"key": "new"})
    assert result["key"] == "new"


def test_apply_patch_sets_nested_key():
    data = {"database": {"host": "localhost"}}
    result = apply_patch(data, {"database.host": "remotehost"})
    assert result["database"]["host"] == "remotehost"


def test_apply_patch_creates_missing_nested_keys():
    data: dict = {}
    result = apply_patch(data, {"a.b.c": "value"})
    assert result["a"]["b"]["c"] == "value"


def test_apply_patch_does_not_mutate_original():
    data = {"x": 1}
    apply_patch(data, {"x": 2})
    assert data["x"] == 1


# --- dump_patched ---

def test_dump_patched_returns_valid_yaml():
    data = {"key": "value"}
    output = dump_patched(data)
    assert yaml.safe_load(output) == data


# --- patch_config integration ---

def test_patch_config_returns_yaml_string(yaml_config):
    result = patch_config(yaml_config, {"database.host": "newhost"})
    loaded = yaml.safe_load(result)
    assert loaded["database"]["host"] == "newhost"


def test_patch_config_writes_output_file(yaml_config, tmp_path):
    out = str(tmp_path / "out.yaml")
    patch_config(yaml_config, {"app.debug": "true"}, output=out)
    loaded = yaml.safe_load(open(out).read())
    assert loaded["app"]["debug"] == "true"


# --- CLI helpers ---

def test_parse_patches_returns_dict():
    assert _parse_patches(["key=value", "a.b=123"]) == {"key": "value", "a.b": "123"}


def test_parse_patches_invalid_raises():
    with pytest.raises(ValueError, match="Invalid patch spec"):
        _parse_patches(["noequals"])


def test_build_parser_registers_patch():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_parser(subs)
    args = root.parse_args(["patch", "cfg.yaml", "--set", "k=v"])
    assert args.file == "cfg.yaml"
    assert args.patches == ["k=v"]


def test_run_prints_to_stdout(yaml_config, capsys):
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_parser(subs)
    args = root.parse_args(["patch", yaml_config, "--set", "database.host=prod"])
    code = run(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "prod" in captured.out


def test_run_returns_1_on_missing_file(tmp_path, capsys):
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_parser(subs)
    args = root.parse_args(["patch", str(tmp_path / "nope.yaml")])
    code = run(args)
    assert code == 1
