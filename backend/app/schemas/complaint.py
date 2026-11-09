"""Complaint Schemas for NileOps Digital Banking Platform.

Enforces strict segregation between customer-facing data and internal operational details.
Customer views never expose staff notes, team routing, or unapproved AI drafts.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ComplaintCreate(BaseModel):
    category: str = Field(..., description="ATM_CARD, TRANSFER, ACCOUNT_FEES, MOBILE_BANKING, GENERAL_INQUIRY")
    subject: str = Field(..., min_length=5, max_length=255)
    details: str = Field(..., min_length=10)


class ComplaintStatusUpdate(BaseModel):
    status: Optional[str] = Field(None, description="OPEN, IN_PROGRESS, RESOLVED, REJECTED")
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    assigned_to_id: Optional[str] = None
    staff_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    customer_reply: Optional[str] = None
    ai_draft_status: Optional[str] = None


class CustomerComplaintOut(BaseModel):
    """Customer-facing complaint schema: human-approved reply only, NEVER internal notes or AI drafts."""
    id: str
    ticket_number: str
    category: str
    category_ar: str
    subject: str
    details: str
    status: str
    priority: str
    customer_reply: Optional[str] = None
    customer_reply_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintOut(BaseModel):
    """Full operational employee view of a complaint."""
    id: str
    ticket_number: str
    customer_id: str
    customer_name: Optional[str] = None
    category: str
    category_ar: str
    subject: str
    details: str
    status: str
    priority: str
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_team: Optional[str] = None
    staff_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    is_test: Optional[bool] = False
    sla_due_at: Optional[datetime] = None
    sla_breached: Optional[bool] = False
    sla_remaining_hours: Optional[float] = None
    sla_status_label: Optional[str] = None
    ai_suggested_category: Optional[str] = None
    ai_suggested_team: Optional[str] = None
    ai_suggested_priority: Optional[str] = None
    ai_matched_keywords: Optional[str] = None
    ai_draft_reply: Optional[str] = None
    ai_draft_status: Optional[str] = None
    customer_reply: Optional[str] = None
    customer_reply_at: Optional[datetime] = None
    customer_replied_by_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedComplaintsOut(BaseModel):
    """Paginated complaint list response for server-side tables."""
    items: List[ComplaintOut]
    total: int
    page: int
    page_size: int
    total_pages: int
