"""Password hashing utilities."""

from passlib.hash import pbkdf2_sha256


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pbkdf2_sha256.verify(password, hashed_password)
