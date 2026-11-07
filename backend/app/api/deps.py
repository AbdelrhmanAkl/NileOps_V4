"""NileOps Shared API Dependencies & Authentication Guards."""

import json
from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, PermissionDeniedException
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.audit import AuditLog
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

# Re-export get_db
get_db = get_db_session


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT and retrieve active User entity."""
    if not auth or not auth.credentials:
        raise AuthenticationException("Authentication required. Please provide a valid Bearer token.")

    payload = decode_access_token(auth.credentials)
    if not payload:
        raise AuthenticationException("Invalid or expired session token.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Malformed token: missing subject.")

    stmt = select(User).where(User.id == str(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationException("User account not found.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """Enforce server-side Role-Based Access Control."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"Role '{current_user.role}' is not authorized. Required: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def require_employee(current_user: User = Depends(get_current_user)) -> User:
    """Ensure session belongs to an employee (rejects customer sessions)."""
    if current_user.user_type != "employee":
        raise PermissionDeniedException("Access restricted to authorized bank staff only.")
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """Ensure session belongs to a retail customer."""
    if current_user.user_type != "customer":
        raise PermissionDeniedException("Access restricted to retail customer sessions.")
    return current_user


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str = "",
    user: Optional[User] = None,
    details: Optional[dict] = None,
    ip_address: str = "127.0.0.1",
) -> None:
    """Record an audit trail event."""
    log = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_role=user.role if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details or {}),
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
