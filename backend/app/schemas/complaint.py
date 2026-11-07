"""Complaint Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ComplaintCreate(BaseModel):
    category: str = Field(..., description="ATM_CARD, TRANSFER, ACCOUNT_FEES, MOBILE_BANKING, GENERAL_INQUIRY")
    subject: str = Field(..., min_length=5, max_length=255)
    details: str = Field(..., min_length=10)


class ComplaintStatusUpdate(BaseModel):
    status: str = Field(..., description="OPEN, IN_PROGRESS, RESOLVED, REJECTED")
    staff_notes: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplaintOut(BaseModel):
    id: str
    ticket_number: str
    customer_id: str
    category: str
    category_ar: str
    subject: str
    details: str
    status: str
    priority: str
    assigned_to_id: Optional[str] = None
    staff_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

