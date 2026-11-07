"""Policy Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    title_en: str = Field(..., min_length=5, max_length=255)
    title_ar: str = Field(..., min_length=5, max_length=255)
    domain: str = Field(..., min_length=3, max_length=100)
    content_en: str = Field(..., min_length=10)
    content_ar: str = Field(..., min_length=10)
    version: str = "1.0.0"


class PolicyApprovalRequest(BaseModel):
    approval_notes: Optional[str] = "Approved after compliance verification."


class PolicyRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5)


class PolicyOut(BaseModel):
    id: str
    code: str
    title_en: str
    title_ar: str
    domain: str
    content_en: str
    content_ar: str
    version: str
    status: str
    created_by_id: str
    approved_by_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    rejected_by_id: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

