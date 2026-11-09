"""Banking Schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


class AccountOut(BaseModel):
    id: str
    account_number: str
    account_type: str
    currency: str
    balance: float
    interest_rate: float
    status: str
    created_at: datetime

    @field_validator("account_number")
    @classmethod
    def mask_account_number(cls, v: str) -> str:
        """Mask account number / IBAN to preserve banking confidentiality (EG98••••••••••••2233)."""
        if not v:
            return v
        clean = str(v).strip()
        if len(clean) <= 8:
            return clean
        bullets = "•" * (len(clean) - 8)
        return f"{clean[:4]}{bullets}{clean[-4:]}"

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    id: str
    reference_number: str
    transaction_type: str
    amount: float
    currency: str
    description: str
    description_ar: str
    counterparty: Optional[str] = None
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ProductInfo(BaseModel):
    id: str
    category: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    interest_rate: float
    min_balance: float
    term_months: Optional[int] = None
    features_en: List[str]
    features_ar: List[str]


class BranchInfo(BaseModel):
    id: str
    code: str
    name_en: str
    name_ar: str
    city_en: str
    city_ar: str
    address_en: str
    address_ar: str
    working_hours: str
    phone: str
    has_atm: bool


class FAQItem(BaseModel):
    id: str
    category: str
    question_en: str
    question_ar: str
    answer_en: str
    answer_ar: str

