"""Policy Knowledge Base & 4-Eyes Approval Governance Endpoints."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    log_audit_event,
    require_employee,
    require_roles,
)
from app.models.policy import PolicyDocument
from app.models.user import User
from app.schemas.policy import (
    PolicyApprovalRequest,
    PolicyCreate,
    PolicyOut,
    PolicyRejectionRequest,
)

router = APIRouter(prefix="/policies", tags=["Policy Governance & Knowledge Base"])


@router.get("", response_model=List[PolicyOut])
async def list_or_search_policies(
    q: Optional[str] = Query(None, description="Keyword search across title, content, or domain"),
    domain: Optional[str] = Query(None, description="Filter by policy domain"),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List or keyword-search banking policy documents.

    Staff may view all document states. Customers only view APPROVED or INDEXED policies.
    """
    stmt = select(PolicyDocument)

    # Access control boundary: Retail customers only see active policies
    if current_user.user_type == "customer":
        stmt = stmt.where(PolicyDocument.status.in_(["APPROVED", "INDEXED"]))
    elif status_filter:
        stmt = stmt.where(PolicyDocument.status == status_filter)

    if domain:
        stmt = stmt.where(PolicyDocument.domain == domain)

    if q:
        search_fmt = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                PolicyDocument.title_en.ilike(search_fmt),
                PolicyDocument.title_ar.ilike(search_fmt),
                PolicyDocument.content_en.ilike(search_fmt),
                PolicyDocument.content_ar.ilike(search_fmt),
                PolicyDocument.domain.ilike(search_fmt),
                PolicyDocument.code.ilike(search_fmt),
            )
        )

    stmt = stmt.order_by(desc(PolicyDocument.updated_at))
    result = await db.execute(stmt)
    policies = result.scalars().all()
    return [PolicyOut.model_validate(p) for p in policies]


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy_detail(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full text of a specific policy document."""
    stmt = select(PolicyDocument).where(PolicyDocument.id == policy_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy document not found.")

    if current_user.user_type == "customer" and policy.status not in ["APPROVED", "INDEXED"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Policy document is not publicly active.")

    return PolicyOut.model_validate(policy)


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy_draft(
    policy_in: PolicyCreate,
    current_user: User = Depends(
        require_roles(["operations_officer", "compliance_reviewer", "admin", "branch_manager"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Author a new policy document in DRAFT state."""
    # Check duplicate code
    existing = await db.scalar(select(PolicyDocument).where(PolicyDocument.code == policy_in.code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy with code '{policy_in.code}' already exists.",
        )

    policy = PolicyDocument(
        code=policy_in.code,
        title_en=policy_in.title_en,
        title_ar=policy_in.title_ar,
        domain=policy_in.domain,
        content_en=policy_in.content_en,
        content_ar=policy_in.content_ar,
        version=policy_in.version,
        status="DRAFT",
        created_by_id=current_user.id,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    await log_audit_event(
        db,
        action="CREATE_POLICY_DRAFT",
        resource_type="POLICY",
        resource_id=policy.id,
        user=current_user,
        details={"code": policy.code, "domain": policy.domain},
    )

    return PolicyOut.model_validate(policy)


@router.post("/{policy_id}/submit", response_model=PolicyOut)
async def submit_policy_for_approval(
    policy_id: str,
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """Transition policy from DRAFT to PENDING_APPROVAL."""
    stmt = select(PolicyDocument).where(PolicyDocument.id == policy_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

    if policy.status not in ["DRAFT", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit policy with status '{policy.status}'. Only DRAFT or REJECTED policies can be submitted.",
        )

    policy.status = "PENDING_APPROVAL"
    await db.commit()
    await db.refresh(policy)

    await log_audit_event(
        db,
        action="SUBMIT_POLICY_APPROVAL",
        resource_type="POLICY",
        resource_id=policy.id,
        user=current_user,
        details={"code": policy.code, "status": "PENDING_APPROVAL"},
    )

    return PolicyOut.model_validate(policy)


@router.post("/{policy_id}/approve", response_model=PolicyOut)
async def approve_policy_document(
    policy_id: str,
    approval: PolicyApprovalRequest,
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Approve a policy document under strict 4-eyes separation of duties.

    Rule: Uploader CANNOT approve their own document version.
    """
    stmt = select(PolicyDocument).where(PolicyDocument.id == policy_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

    if policy.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve policy with status '{policy.status}'. Must be PENDING_APPROVAL.",
        )

    # 4-Eyes Separation of Duties Enforcement
    if policy.created_by_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Four-Eyes Governance Violation: The author/uploader cannot approve their own policy document.",
        )

    now = datetime.now(timezone.utc)
    policy.status = "INDEXED"  # Approved & Indexed into searchable knowledge base
    policy.approved_by_id = current_user.id
    policy.approved_at = now
    policy.approval_notes = approval.approval_notes

    await db.commit()
    await db.refresh(policy)

    await log_audit_event(
        db,
        action="APPROVE_POLICY",
        resource_type="POLICY",
        resource_id=policy.id,
        user=current_user,
        details={
            "code": policy.code,
            "status": "INDEXED",
            "approved_by": current_user.email,
        },
    )

    return PolicyOut.model_validate(policy)


@router.post("/{policy_id}/reject", response_model=PolicyOut)
async def reject_policy_document(
    policy_id: str,
    rejection: PolicyRejectionRequest,
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Reject a policy document with justification."""
    stmt = select(PolicyDocument).where(PolicyDocument.id == policy_id)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

    if policy.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject policy with status '{policy.status}'. Must be PENDING_APPROVAL.",
        )

    now = datetime.now(timezone.utc)
    policy.status = "REJECTED"
    policy.rejected_by_id = current_user.id
    policy.rejected_at = now
    policy.rejection_reason = rejection.rejection_reason

    await db.commit()
    await db.refresh(policy)

    await log_audit_event(
        db,
        action="REJECT_POLICY",
        resource_type="POLICY",
        resource_id=policy.id,
        user=current_user,
        details={"code": policy.code, "reason": rejection.rejection_reason},
    )

    return PolicyOut.model_validate(policy)

