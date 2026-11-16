"""Simulated Account Opening & Card Requests ORM Models.

Strictly for digital banking operations simulation.
NO real bank accounts or payment cards are created.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AccountOpeningRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simulated retail customer account opening request."""

    __tablename__ = "account_opening_requests"

    reference_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # current, savings, certificate
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    initial_deposit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_income: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    employment_status: Mapped[str] = mapped_column(String(50), default="EMPLOYED", nullable=False)
    branch_code: Mapped[str] = mapped_column(String(20), default="CAI-01", nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", index=True, nullable=False)
    # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED_SIMULATED, REJECTED, MORE_INFO_REQUIRED, SIMULATED_COMPLETED

    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=True)
    submitted_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str] = mapped_column(Text, default="", nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, default="", nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class CardRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simulated debit/credit/prepaid card issuance request."""

    __tablename__ = "card_requests"

    reference_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    linked_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    card_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # DEBIT_VISA_CLASSIC, DEBIT_MASTERCARD_TITANIUM, CREDIT_VISA_PLATINUM, PREPAID_MEEZA
    embossed_name: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_branch: Mapped[str] = mapped_column(String(50), default="CAI-01", nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", index=True, nullable=False)
    # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED_SIMULATED, REJECTED, MORE_INFO_REQUIRED, SIMULATED_COMPLETED

    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=True)
    submitted_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str] = mapped_column(Text, default="", nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, default="", nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

