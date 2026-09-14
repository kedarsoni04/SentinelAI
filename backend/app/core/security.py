from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Use bcrypt directly instead of passlib to avoid the incompatibility
# between passlib 1.7.4 and bcrypt>=4.0 (strict 72-byte error).
# bcrypt silently truncates passwords > 72 bytes — standard behaviour.


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    password_bytes = plain_password.encode("utf-8")[:72]  # explicit safe truncation
    hashed = _bcrypt.hashpw(password_bytes, _bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")[:72]  # match truncation in hash
    try:
        return _bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The token subject — typically the user's ID as a string.
        expires_delta: Custom expiry duration. Defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT access token.

    Returns:
        The subject (user ID) if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject: Optional[str] = payload.get("sub")
        return subject
    except JWTError:
        return None
