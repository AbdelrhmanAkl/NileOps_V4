"""Synthetic KYC Document Verification Model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KycVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Simulated KYC National ID verification record."""

    __tablename__ = "kyc_verifications"

    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    synthetic_national_id: Mapped[str] = mapped_column(String(14), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), default="EGYPTIAN_NATIONAL_ID_SYNTHETIC", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_REVIEW", nullable=False)
    # PENDING_REVIEW, VERIFIED_SYNTHETIC, REJECTED, FLAGGED
    extracted_data_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    mismatch_reasons_json: Mapped[str] = mapped_column(Text, default="[]", nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str] = mapped_column(Text, default="", nullable=True)

