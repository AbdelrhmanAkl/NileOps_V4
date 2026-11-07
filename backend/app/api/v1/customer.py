"""Customer Portal Endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, log_audit_event, require_customer
from app.models.banking import Account, Transaction
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.banking import AccountOut, TransactionOut
from app.schemas.complaint import ComplaintCreate, ComplaintOut

router = APIRouter(prefix="/customer", tags=["Customer Portal"])

CATEGORY_AR_MAP = {
    "ATM_CARD": "بطاقات الصراف الآلي",
    "TRANSFER": "التحويلات والمدفوعات",
    "ACCOUNT_FEES": "رسوم ومصاريف الحسابات",
    "MOBILE_BANKING": "الخدمات المصرفية عبر الهاتف",
    "GENERAL_INQUIRY": "استفسارات عامة",
}


@router.get("/profile", response_model=UserOut)
async def get_customer_profile(current_user: User = Depends(require_customer)):
    """Retrieve verified customer profile."""
    return UserOut.model_validate(current_user)


@router.get("/accounts", response_model=List[AccountOut])
async def list_customer_accounts(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List all synthetic accounts owned by the authenticated customer."""
    stmt = (
        select(Account)
        .where(Account.user_id == current_user.id)
        .order_by(Account.created_at.asc())
    )
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [AccountOut.model_validate(a) for a in accounts]


@router.get("/transactions", response_model=List[TransactionOut])
async def list_customer_transactions(
    account_id: Optional[str] = Query(None, description="Filter by customer account ID"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List transaction history for customer's accounts (Strict ownership check)."""
    # 1. Fetch customer's valid account IDs
    acc_stmt = select(Account.id).where(Account.user_id == current_user.id)
    acc_result = await db.execute(acc_stmt)
    owned_account_ids = acc_result.scalars().all()

    if not owned_account_ids:
        return []

    if account_id:
        if account_id not in owned_account_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Account does not belong to your customer profile.",
            )
        target_account_ids = [account_id]
    else:
        target_account_ids = owned_account_ids

    # 2. Query transactions
    txn_stmt = (
        select(Transaction)
        .where(Transaction.account_id.in_(target_account_ids))
        .order_by(desc(Transaction.timestamp))
        .limit(limit)
    )
    result = await db.execute(txn_stmt)
    transactions = result.scalars().all()
    return [TransactionOut.model_validate(t) for t in transactions]


@router.get("/complaints", response_model=List[ComplaintOut])
async def list_customer_complaints(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List complaints submitted by the authenticated customer."""
    stmt = (
        select(Complaint)
        .where(Complaint.customer_id == current_user.id)
        .order_by(desc(Complaint.created_at))
    )
    result = await db.execute(stmt)
    complaints = result.scalars().all()
    return [ComplaintOut.model_validate(c) for c in complaints]


@router.post("/complaints", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    complaint_in: ComplaintCreate,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Submit a simulated operational banking complaint."""
    # Generate unique ticket number
    ticket_num = f"CMP-2026-{uuid.uuid4().hex[:6].upper()}"
    cat_ar = CATEGORY_AR_MAP.get(complaint_in.category, "شكوى مصرفية")

    complaint = Complaint(
        ticket_number=ticket_num,
        customer_id=current_user.id,
        category=complaint_in.category,
        category_ar=cat_ar,
        subject=complaint_in.subject,
        details=complaint_in.details,
        status="OPEN",
        priority="MEDIUM",
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    await log_audit_event(
        db,
        action="SUBMIT_COMPLAINT",
        resource_type="COMPLAINT",
        resource_id=complaint.id,
        user=current_user,
        details={"ticket_number": ticket_num, "category": complaint_in.category},
    )

    return ComplaintOut.model_validate(complaint)

