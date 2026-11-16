"""Banking Policy Document ORM Model."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PolicyDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Banking knowledge base policy document with 4-eyes approval workflow."""

    __tablename__ = "policy_documents"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    content_en: Mapped[str] = mapped_column(Text, nullable=False)
    content_ar: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True, nullable=False)
    # DRAFT -> PENDING_APPROVAL -> APPROVED -> INDEXED (or REJECTED)

    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str] = mapped_column(Text, default="", nullable=True)

    rejected_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, default="", nullable=True)

