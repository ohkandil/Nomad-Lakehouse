from __future__ import annotations

import hashlib

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception:
            return False
    # Fallback to SHA256
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    # Fallback to SHA256
    return hashlib.sha256(password.encode()).hexdigest()
