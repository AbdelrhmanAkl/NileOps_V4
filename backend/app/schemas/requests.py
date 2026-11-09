"""Pydantic Schemas for Simulated Account Opening & Card Requests."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AccountOpeningRequestCreate(BaseModel):
    product_id: str
    account_type: str = "current"
    currency: str = "EGP"
    initial_deposit: float = Field(0.0, ge=0.0)
    monthly_income: float = Field(0.0, ge=0.0)
    employment_status: str = "EMPLOYED"
    branch_code: str = "CAI-01"
    idempotency_key: Optional[str] = None


class AccountOpeningRequestOut(BaseModel):
    id: str
    reference_number: str
    customer_id: str
    customer_name: Optional[str] = None
    product_id: str
    product_name: Optional[str] = None
    account_type: str
    currency: str
    initial_deposit: float
    monthly_income: float
    employment_status: str
    branch_code: str
    status: str
    idempotency_key: Optional[str] = None
    submitted_by_id: str
    submitted_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardRequestCreate(BaseModel):
    linked_account_id: str
    card_type: str
    embossed_name: str
    delivery_branch: str = "CAI-01"
    idempotency_key: Optional[str] = None


class CardRequestOut(BaseModel):
    id: str
    reference_number: str
    customer_id: str
    customer_name: Optional[str] = None
    linked_account_id: str
    card_type: str
    card_name: Optional[str] = None
    embossed_name: str
    delivery_branch: str
    status: str
    idempotency_key: Optional[str] = None
    submitted_by_id: str
    submitted_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequestReviewAction(BaseModel):
    status: str
    notes: Optional[str] = ""
    rejection_reason: Optional[str] = ""


class RuleDetail(BaseModel):
    code: str
    name: str
    passed: bool
    message: str


class RequestRuleEvaluationResult(BaseModel):
    eligible: bool
    recommendation: str  # APPROVE_SIMULATED | MORE_INFO_REQUIRED | REJECT
    rules: List[RuleDetail]

