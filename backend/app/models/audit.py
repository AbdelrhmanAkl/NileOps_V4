"""Audit Log Model."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail for security, compliance, and governance actions."""

    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(String(36), default="", nullable=True)
    user_email: Mapped[str] = mapped_column(String(255), default="", nullable=True)
    user_role: Mapped[str] = mapped_column(String(50), default="", nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), default="", nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), default="", nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

