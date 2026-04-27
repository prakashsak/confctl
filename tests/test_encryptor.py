"""Tests for confctl.encryptor."""

import pytest
import yaml

from confctl.encryptor import (
    ENCRYPTED_PREFIX,
    EncryptError,
    decrypt_config,
    decrypt_value,
    encrypt_config,
    encrypt_value,
)


@pytest.fixture()
def secret():
    return "test-secret-key"


@pytest.fixture()
def yaml_config(tmp_path, secret):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("db_password: hunter2\ndb_host: localhost\n")
    return cfg


@pytest.fixture()
def encrypted_yaml(tmp_path, secret):
    token = encrypt_value("hunter2", secret)
    cfg = tmp_path / "enc_config.yaml"
    cfg.write_text(f"db_password: '{token}'\ndb_host: localhost\n")
    return cfg


def test_encrypt_value_returns_enc_prefix(secret):
    result = encrypt_value("mysecret", secret)
    assert result.startswith(ENCRYPTED_PREFIX)


def test_decrypt_value_roundtrip(secret):
    plaintext = "super-secret-value"
    encrypted = encrypt_value(plaintext, secret)
    assert decrypt_value(encrypted, secret) == plaintext


def test_decrypt_value_wrong_secret_raises(secret):
    encrypted = encrypt_value("value", secret)
    with pytest.raises(EncryptError, match="Decryption failed"):
        decrypt_value(encrypted, "wrong-secret")


def test_decrypt_value_missing_prefix_raises(secret):
    with pytest.raises(EncryptError, match="does not start with"):
        decrypt_value("plaintext", secret)


def test_encrypt_config_encrypts_all_strings(yaml_config, secret):
    result = encrypt_config(yaml_config, secret)
    assert result["db_password"].startswith(ENCRYPTED_PREFIX)
    assert result["db_host"].startswith(ENCRYPTED_PREFIX)


def test_encrypt_config_selective_keys(yaml_config, secret):
    result = encrypt_config(yaml_config, secret, keys=["db_password"])
    assert result["db_password"].startswith(ENCRYPTED_PREFIX)
    assert result["db_host"] == "localhost"


def test_encrypt_config_skips_already_encrypted(encrypted_yaml, secret):
    result = encrypt_config(encrypted_yaml, secret)
    # Should still be a single ENC: prefix, not double-encrypted
    assert result["db_password"].startswith(ENCRYPTED_PREFIX)
    assert result["db_password"].count(ENCRYPTED_PREFIX) == 1


def test_decrypt_config_decrypts_enc_values(encrypted_yaml, secret):
    result = decrypt_config(encrypted_yaml, secret)
    assert result["db_password"] == "hunter2"
    assert result["db_host"] == "localhost"


def test_encrypt_config_missing_file_raises(tmp_path, secret):
    with pytest.raises(FileNotFoundError):
        encrypt_config(tmp_path / "nonexistent.yaml", secret)


def test_decrypt_config_missing_file_raises(tmp_path, secret):
    with pytest.raises(FileNotFoundError):
        decrypt_config(tmp_path / "nonexistent.yaml", secret)


def test_encrypt_config_non_mapping_raises(tmp_path, secret):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("- item1\n- item2\n")
    with pytest.raises(EncryptError, match="does not contain a YAML mapping"):
        encrypt_config(cfg, secret)
