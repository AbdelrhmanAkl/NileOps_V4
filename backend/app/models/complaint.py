"""Customer Complaint ORM Model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Customer operational complaint and resolution tracking."""

    __tablename__ = "complaints"

    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ATM_CARD, TRANSFER, ACCOUNT_FEES, MOBILE_BANKING, GENERAL_INQUIRY
    category_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, REJECTED
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text, default="", nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, default="", nullable=True)

    # Phase 4 Extensions: Team assignment, SLA metrics, Advisory intelligence, and Test segregation
    is_test: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True, index=True)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Advisory Classification & AI Drafts (Simulated & Rule-based)
    ai_suggested_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_suggested_team: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_suggested_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_matched_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_draft_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_draft_status: Mapped[Optional[str]] = mapped_column(String(30), default="PENDING_REVIEW", nullable=True)

    # Customer-Facing Human-Approved Reply (Strictly segregated from internal notes)
    customer_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_replied_by_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


