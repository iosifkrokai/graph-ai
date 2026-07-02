"""Encryption utility and settings tests."""

import pytest
from pydantic import ValidationError

from settings.encryption import EncryptionSettings
from utils.encryption import decrypt, encrypt


def test_encrypt_roundtrip() -> None:
    """Encryption produces a different token that decrypts back."""
    plaintext = "sk-secret-value"
    token = encrypt(plaintext)
    if token == plaintext:
        pytest.fail("Encrypted token must differ from the plaintext")
    if decrypt(token) != plaintext:
        pytest.fail("Decrypt must recover the original plaintext")


def test_default_key_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default encryption key is rejected when ENVIRONMENT=production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValidationError, match="ENCRYPTION_SECRET_KEY"):
        EncryptionSettings()
