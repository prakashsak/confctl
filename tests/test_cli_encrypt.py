"""Tests for confctl.cli_encrypt."""

import sys
from pathlib import Path

import pytest
import yaml

from confctl.cli_encrypt import build_parser, run
from confctl.encryptor import ENCRYPTED_PREFIX, encrypt_value


@pytest.fixture()
def parser():
    return build_parser()


@pytest.fixture()
def plain_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("api_key: secret123\nhost: example.com\n")
    return cfg


@pytest.fixture()
def encrypted_config(tmp_path):
    token = encrypt_value("secret123", "mysecret")
    cfg = tmp_path / "enc.yaml"
    cfg.write_text(f"api_key: '{token}'\nhost: example.com\n")
    return cfg


def test_build_parser_registers_encrypt(parser):
    args = parser.parse_args(["encrypt", "config.yaml", "--secret", "s"])
    assert args.encmode == "encrypt"


def test_build_parser_registers_decrypt(parser):
    args = parser.parse_args(["decrypt", "config.yaml", "--secret", "s"])
    assert args.encmode == "decrypt"


def test_build_parser_accepts_keys_flag(parser):
    args = parser.parse_args(["encrypt", "f.yaml", "--secret", "s", "--keys", "api_key"])
    assert args.keys == ["api_key"]


def test_build_parser_accepts_output_flag(parser, tmp_path):
    out = tmp_path / "out.yaml"
    args = parser.parse_args(["encrypt", "f.yaml", "--secret", "s", "--output", str(out)])
    assert args.output == out


def test_run_encrypt_prints_to_stdout(plain_config, capsys, parser):
    args = parser.parse_args(["encrypt", str(plain_config), "--secret", "mysecret"])
    run(args)
    out = capsys.readouterr().out
    assert ENCRYPTED_PREFIX in out


def test_run_encrypt_writes_output_file(plain_config, tmp_path, parser):
    out = tmp_path / "result.yaml"
    args = parser.parse_args(
        ["encrypt", str(plain_config), "--secret", "mysecret", "--output", str(out)]
    )
    run(args)
    content = out.read_text()
    assert ENCRYPTED_PREFIX in content


def test_run_decrypt_recovers_plaintext(encrypted_config, capsys, parser):
    args = parser.parse_args(["decrypt", str(encrypted_config), "--secret", "mysecret"])
    run(args)
    out = capsys.readouterr().out
    data = yaml.safe_load(out)
    assert data["api_key"] == "secret123"


def test_run_encrypt_missing_file_exits(tmp_path, parser):
    args = parser.parse_args(["encrypt", str(tmp_path / "nope.yaml"), "--secret", "s"])
    with pytest.raises(SystemExit) as exc_info:
        run(args)
    assert exc_info.value.code == 1


def test_run_no_subcommand_exits(parser):
    args = parser.parse_args([])
    with pytest.raises(SystemExit) as exc_info:
        run(args)
    assert exc_info.value.code == 1
