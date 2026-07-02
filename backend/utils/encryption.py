"""Symmetric encryption for provider secrets (Fernet)."""

from cryptography.fernet import Fernet

from settings import encryption_settings

_fernet = Fernet(encryption_settings.secret_key.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext secret for storage at rest.

    Args:
        plaintext: The value to encrypt.

    Returns:
        The encrypted token as a string.

    """
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a token previously produced by :func:`encrypt`.

    Args:
        token: The encrypted token.

    Returns:
        The decrypted plaintext.

    """
    return _fernet.decrypt(token.encode()).decode()
