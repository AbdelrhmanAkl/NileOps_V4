"""KYC Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class KycReviewRequest(BaseModel):
    status: str = Field(..., description="APPROVED_SIMULATED, REJECTED, INFO_REQUESTED, FLAGGED")
    reviewer_notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        # Migration-safe: map legacy VERIFIED_SYNTHETIC to APPROVED_SIMULATED
        if v == "VERIFIED_SYNTHETIC":
            v = "APPROVED_SIMULATED"
        allowed = {"APPROVED_SIMULATED", "REJECTED", "INFO_REQUESTED", "FLAGGED"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_rejection_reason(self):
        if self.status == "REJECTED" and not (self.reviewer_notes and self.reviewer_notes.strip()):
            raise ValueError("Rejection notes are mandatory when rejecting a KYC case.")
        return self


class KycVerificationOut(BaseModel):
    id: str
    tracking_number: str
    customer_id: str
    synthetic_national_id: str
    document_type: str
    status: str
    extracted_data_json: str
    mismatch_reasons_json: Optional[str] = "[]"
    image_url: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        # Migration-safe: render legacy VERIFIED_SYNTHETIC as APPROVED_SIMULATED
        if v == "VERIFIED_SYNTHETIC":
            return "APPROVED_SIMULATED"
        return v

    @field_validator("synthetic_national_id")
    @classmethod
    def mask_national_id(cls, v: str) -> str:
        """Mask synthetic Egyptian National ID to preserve privacy invariants (2950****1234)."""
        if not v:
            return v
        clean = str(v).strip()
        if len(clean) == 14:
            return f"{clean[:4]}****{clean[-4:]}"
        elif len(clean) > 8:
            return f"{clean[:4]}****{clean[-4:]}"
        return clean

    class Config:
        from_attributes = True


class CustomerKycOut(BaseModel):
    id: str
    tracking_number: str
    synthetic_national_id: str
    document_type: str = "EGYPTIAN_NATIONAL_ID_SYNTHETIC"
    status: str
    identity_verification_status: str = "NOT_VERIFIED"
    created_at: datetime
    updated_at: datetime

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        if v == "VERIFIED_SYNTHETIC":
            return "APPROVED_SIMULATED"
        return v

    @field_validator("synthetic_national_id")
    @classmethod
    def mask_national_id(cls, v: str) -> str:
        if not v:
            return v
        clean = str(v).strip()
        if len(clean) == 14:
            return f"{clean[:4]}****{clean[-4:]}"
        elif len(clean) > 8:
            return f"{clean[:4]}****{clean[-4:]}"
        return clean

    class Config:
        from_attributes = True




