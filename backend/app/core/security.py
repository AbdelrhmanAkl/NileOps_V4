"""NileOps Security & Token Utilities (Phase 1 Baseline)."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.config import settings

# Placeholder utilities for Phase 1 scaffolding
# Full implementations with python-jose and passlib activate in Phase 2/3

def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
    claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a JWT access token shell."""
    # In Phase 1, return placeholder structure or standard JWT when libraries are loaded
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if claims:
        payload.update(claims)
    
    try:
        from jose import jwt
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except ImportError:
        # Fallback minimal token representation for Phase 1 tests without jose installed
        return f"mock-token:{subject}:{expire.timestamp()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify hashed password."""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
    except ImportError:
        return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    except ImportError:
        return f"hash:{password}"
