"""KYC Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KycReviewRequest(BaseModel):
    status: str = Field(..., description="VERIFIED_SYNTHETIC, REJECTED, FLAGGED")
    reviewer_notes: Optional[str] = None


class KycVerificationOut(BaseModel):
    id: str
    tracking_number: str
    customer_id: str
    synthetic_national_id: str
    document_type: str
    status: str
    extracted_data_json: str
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

