"""Banking Accounts & Transactions ORM Models."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Account(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Synthetic customer bank account."""

    __tablename__ = "accounts"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(34), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # current, savings, certificate
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, FROZEN, CLOSED


class Transaction(Base, UUIDPrimaryKeyMixin):
    """Synthetic account transaction."""

    __tablename__ = "transactions"

    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, BILL_PAYMENT, INTEREST_CREDIT
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    description_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    counterparty: Mapped[str] = mapped_column(String(255), default="", nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

