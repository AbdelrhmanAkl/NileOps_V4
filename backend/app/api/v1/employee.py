"""Employee & Operations Workspace Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, log_audit_event, require_employee, require_roles
from app.models.audit import AuditLog
from app.models.banking import Account
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.policy import PolicyDocument
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.schemas.auth import UserOut
from app.schemas.complaint import ComplaintOut, ComplaintStatusUpdate
from app.schemas.kyc import KycReviewRequest, KycVerificationOut

router = APIRouter(prefix="/employee", tags=["Employee & Operations Portal"])


@router.get("/dashboard")
async def get_operations_dashboard_metrics(
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated operational metrics for staff dashboard."""
    # Count open complaints
    open_cmps = await db.scalar(
        select(func.count(Complaint.id)).where(Complaint.status.in_(["OPEN", "IN_PROGRESS"]))
    )
    # Count pending policies
    pending_pols = await db.scalar(
        select(func.count(PolicyDocument.id)).where(PolicyDocument.status == "PENDING_APPROVAL")
    )
    # Count pending KYC reviews
    pending_kyc = await db.scalar(
        select(func.count(KycVerification.id)).where(KycVerification.status == "PENDING_REVIEW")
    )
    # Count total customers
    total_customers = await db.scalar(
        select(func.count(User.id)).where(User.user_type == "customer")
    )
    # Total accounts
    total_accounts = await db.scalar(
        select(func.count(Account.id)).where(Account.status == "ACTIVE")
    )

    return {
        "metrics": {
            "open_complaints": open_cmps or 0,
            "pending_policies": pending_pols or 0,
            "pending_kyc_reviews": pending_kyc or 0,
            "total_customers": total_customers or 0,
            "active_accounts": total_accounts or 0,
        },
        "officer": {
            "name": current_user.full_name,
            "role": current_user.role,
            "email": current_user.email,
        },
    }


@router.get("/customers", response_model=List[UserOut])
async def search_customers(
    q: Optional[str] = Query(None, description="Search term by name or email"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """Authorized customer search for operations and customer service staff."""
    stmt = select(User).where(User.user_type == "customer")
    if q:
        search_fmt = f"%{q.strip()}%"
        stmt = stmt.where((User.full_name.ilike(search_fmt)) | (User.email.ilike(search_fmt)))
    stmt = stmt.order_by(User.full_name.asc()).limit(limit)

    result = await db.execute(stmt)
    customers = result.scalars().all()
    return [UserOut.model_validate(c) for c in customers]


@router.get("/complaints", response_model=List[ComplaintOut])
async def list_all_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """List operational complaints with optional status filter."""
    stmt = select(Complaint)
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    stmt = stmt.order_by(desc(Complaint.created_at))

    result = await db.execute(stmt)
    complaints = result.scalars().all()
    return [ComplaintOut.model_validate(c) for c in complaints]


@router.patch("/complaints/{complaint_id}", response_model=ComplaintOut)
async def update_complaint_status(
    complaint_id: str,
    update_data: ComplaintStatusUpdate,
    current_user: User = Depends(
        require_roles(["customer_service", "operations_officer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update complaint status, assign staff notes, or finalize resolution."""
    stmt = select(Complaint).where(Complaint.id == complaint_id)
    result = await db.execute(stmt)
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found.")

    complaint.status = update_data.status
    complaint.assigned_to_id = current_user.id
    if update_data.staff_notes is not None:
        complaint.staff_notes = update_data.staff_notes
    if update_data.resolution_notes is not None:
        complaint.resolution_notes = update_data.resolution_notes

    await db.commit()
    await db.refresh(complaint)

    await log_audit_event(
        db,
        action="UPDATE_COMPLAINT_STATUS",
        resource_type="COMPLAINT",
        resource_id=complaint.id,
        user=current_user,
        details={"new_status": update_data.status, "ticket_number": complaint.ticket_number},
    )

    return ComplaintOut.model_validate(complaint)


@router.get("/audit-logs", response_model=List[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(
        require_roles(["admin", "compliance_reviewer", "branch_manager"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """View immutable system audit logs (Admin, Compliance, Branch Manager)."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [AuditLogOut.model_validate(log) for log in logs]


@router.get("/kyc-verifications", response_model=List[KycVerificationOut])
async def list_kyc_verifications(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "operations_officer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """List synthetic KYC verification queues."""
    stmt = select(KycVerification)
    if status_filter:
        stmt = stmt.where(KycVerification.status == status_filter)
    stmt = stmt.order_by(desc(KycVerification.created_at))

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [KycVerificationOut.model_validate(k) for k in records]


@router.patch("/kyc-verifications/{kyc_id}", response_model=KycVerificationOut)
async def review_kyc_verification(
    kyc_id: str,
    review_data: KycReviewRequest,
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Review and update synthetic KYC document verification status."""
    stmt = select(KycVerification).where(KycVerification.id == kyc_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC record not found.")

    record.status = review_data.status
    record.reviewer_id = current_user.id
    if review_data.reviewer_notes:
        record.reviewer_notes = review_data.reviewer_notes

    await db.commit()
    await db.refresh(record)

    await log_audit_event(
        db,
        action="REVIEW_KYC",
        resource_type="KYC",
        resource_id=record.id,
        user=current_user,
        details={"status": review_data.status, "tracking_number": record.tracking_number},
    )

    return KycVerificationOut.model_validate(record)

