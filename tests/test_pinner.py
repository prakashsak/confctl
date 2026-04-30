"""Tests for confctl.pinner."""

from __future__ import annotations

import json
import os

import pytest

from confctl.pinner import (
    PinError,
    create_pin,
    format_verify_summary,
    load_pin,
    save_pin,
    verify_pin,
)


@pytest.fixture()
def config_files(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("key: value\n")
    b.write_text("other: 123\n")
    return [str(a), str(b)]


def test_create_pin_returns_dict(config_files):
    pin = create_pin(config_files)
    assert isinstance(pin, dict)
    assert len(pin) == 2


def test_create_pin_values_are_hex_strings(config_files):
    pin = create_pin(config_files)
    for v in pin.values():
        assert len(v) == 64
        int(v, 16)  # raises if not valid hex


def test_create_pin_empty_list_raises():
    with pytest.raises(PinError, match="No files"):
        create_pin([])


def test_create_pin_missing_file_raises(tmp_path):
    with pytest.raises(PinError, match="File not found"):
        create_pin([str(tmp_path / "missing.yaml")])


def test_save_and_load_pin_roundtrip(tmp_path, config_files):
    pin = create_pin(config_files)
    out = str(tmp_path / "pins.json")
    save_pin(pin, out)
    loaded = load_pin(out)
    assert loaded == pin


def test_save_pin_writes_valid_json(tmp_path, config_files):
    pin = create_pin(config_files)
    out = str(tmp_path / "pins.json")
    save_pin(pin, out)
    with open(out) as fh:
        data = json.load(fh)
    assert isinstance(data, dict)


def test_load_pin_missing_file_raises(tmp_path):
    with pytest.raises(PinError, match="Pin file not found"):
        load_pin(str(tmp_path / "nope.json"))


def test_load_pin_non_object_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]\n")
    with pytest.raises(PinError, match="JSON object"):
        load_pin(str(bad))


def test_verify_pin_all_ok(config_files):
    pin = create_pin(config_files)
    results = verify_pin(pin)
    assert all(results.values())


def test_verify_pin_detects_change(config_files):
    pin = create_pin(config_files)
    # Mutate one file after pinning
    with open(config_files[0], "a") as fh:
        fh.write("extra: line\n")
    results = verify_pin(pin)
    assert results[config_files[0]] is False
    assert results[config_files[1]] is True


def test_verify_pin_missing_file_is_false(tmp_path):
    pin = {str(tmp_path / "ghost.yaml"): "a" * 64}
    results = verify_pin(pin)
    assert results[str(tmp_path / "ghost.yaml")] is False


def test_format_verify_summary_contains_status(config_files):
    pin = create_pin(config_files)
    results = verify_pin(pin)
    summary = format_verify_summary(results)
    assert "OK" in summary
    assert "2/2" in summary
