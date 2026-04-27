"""Encrypt and decrypt sensitive values in config files."""

import base64
import os
import re
from pathlib import Path

import yaml

ENCRYPTED_PREFIX = "ENC:"
_VAR_RE = re.compile(r"^" + re.escape(ENCRYPTED_PREFIX))


class EncryptError(Exception):
    pass


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte key from an arbitrary secret string."""
    import hashlib
    return hashlib.sha256(secret.encode()).digest()


def encrypt_value(plaintext: str, secret: str) -> str:
    """Return an ENC:-prefixed base64 encoded encrypted string."""
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise EncryptError("cryptography package is required for encryption") from exc
    key = base64.urlsafe_b64encode(_derive_key(secret))
    token = Fernet(key).encrypt(plaintext.encode()).decode()
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_value(ciphertext: str, secret: str) -> str:
    """Decrypt an ENC:-prefixed value and return the plaintext."""
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError as exc:
        raise EncryptError("cryptography package is required for decryption") from exc
    if not ciphertext.startswith(ENCRYPTED_PREFIX):
        raise EncryptError(f"Value does not start with '{ENCRYPTED_PREFIX}': {ciphertext!r}")
    token = ciphertext[len(ENCRYPTED_PREFIX):]
    key = base64.urlsafe_b64encode(_derive_key(secret))
    try:
        return Fernet(key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise EncryptError("Decryption failed: invalid token or wrong secret") from exc


def _walk_and_transform(obj, fn):
    """Recursively apply fn to every string leaf in a nested dict/list."""
    if isinstance(obj, dict):
        return {k: _walk_and_transform(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_transform(item, fn) for item in obj]
    if isinstance(obj, str):
        return fn(obj)
    return obj


def encrypt_config(path: Path, secret: str, keys: list[str] | None = None) -> dict:
    """Load a YAML config and encrypt specified keys (or all string values)."""
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise EncryptError(f"{path} does not contain a YAML mapping")

    def maybe_encrypt(val: str) -> str:
        if val.startswith(ENCRYPTED_PREFIX):
            return val
        return encrypt_value(val, secret)

    if keys:
        for k in keys:
            if k in data and isinstance(data[k], str):
                data[k] = maybe_encrypt(data[k])
    else:
        data = _walk_and_transform(data, maybe_encrypt)
    return data


def decrypt_config(path: Path, secret: str) -> dict:
    """Load a YAML config and decrypt all ENC:-prefixed values."""
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise EncryptError(f"{path} does not contain a YAML mapping")

    def maybe_decrypt(val: str) -> str:
        if val.startswith(ENCRYPTED_PREFIX):
            return decrypt_value(val, secret)
        return val

    return _walk_and_transform(data, maybe_decrypt)
