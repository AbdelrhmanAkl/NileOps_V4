"""NileOps Standard Application Exceptions."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class NileOpsException(HTTPException):
    """Base exception for all NileOps custom application errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "INTERNAL_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}


class EntityNotFoundException(NileOpsException):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with identifier '{identifier}' was not found.",
            error_code="ENTITY_NOT_FOUND",
            extra={"entity": entity, "identifier": str(identifier)},
        )


class PermissionDeniedException(NileOpsException):
    def __init__(self, detail: str = "Access denied."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


class AuthenticationException(NileOpsException):
    def __init__(self, detail: str = "Could not validate credentials."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_FAILED",
        )
