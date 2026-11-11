"""Employee & Operations Workspace Endpoints."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, log_audit_event, require_employee, require_roles
from app.models.audit import AuditLog
from app.models.banking import Account
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.policy import PolicyDocument
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.schemas.auth import UserOut
from app.schemas.complaint import ComplaintOut, ComplaintStatusUpdate, PaginatedComplaintsOut
from app.services.complaint_sla import calculate_sla_due_at, evaluate_sla
from app.services.complaint_intelligence import (
    classify_complaint_deterministically,
    AdvisoryClassificationResult,
)
from app.services.complaint_workflow import (
    validate_complaint_transition,
    VALID_COMPLAINT_TEAMS,
    VALID_COMPLAINT_PRIORITIES,
    VALID_COMPLAINT_CATEGORIES,
)
from app.schemas.kyc import KycReviewRequest, KycVerificationOut
from app.schemas.requests import (
    AccountOpeningRequestOut,
    CardRequestOut,
    RequestReviewAction,
    RequestRuleEvaluationResult,
)
from app.services.kyc_checks import kyc_check_service
from app.services.request_rules import (
    evaluate_account_opening_rules,
    validate_transition,
)
from app.services.image_pipeline import (
    MAX_UPLOAD_SIZE,
    image_ocr_pipeline,
    is_valid_image_header,
)

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "kyc_uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    # Count pending policies (excluding POL-TEST-*)
    pending_pols = await db.scalar(
        select(func.count(PolicyDocument.id))
        .where(PolicyDocument.status == "PENDING_APPROVAL")
        .where(~PolicyDocument.code.startswith("POL-TEST-"))
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


async def serialize_complaint_out(
    c: Complaint, db: AsyncSession, now: Optional[datetime] = None
) -> ComplaintOut:
    """Serialize full operational ComplaintOut with resolved customer name and live SLA metrics."""
    # Look up customer full name
    cust_res = await db.execute(select(User.full_name).where(User.id == c.customer_id))
    cust_name = cust_res.scalar_one_or_none() or "Demo Customer"

    # Look up assignee full name
    assignee_name = None
    if c.assigned_to_id:
        ass_res = await db.execute(select(User.full_name).where(User.id == c.assigned_to_id))
        assignee_name = ass_res.scalar_one_or_none()

    # Calculate SLA status
    sla_eval = evaluate_sla(
        created_at=c.created_at,
        priority=c.priority,
        status=c.status,
        due_at=c.sla_due_at,
        now=now,
        resolved_at=c.updated_at if c.status in ("RESOLVED", "REJECTED") else None,
    )

    # Populate advisory classification if missing
    ai_cat = c.ai_suggested_category
    ai_team = c.ai_suggested_team
    ai_prio = c.ai_suggested_priority
    ai_kws = c.ai_matched_keywords
    ai_draft = c.ai_draft_reply
    if not ai_cat or not ai_draft:
        adv = classify_complaint_deterministically(
            subject=c.subject,
            details=c.details,
            customer_name=cust_name,
            ticket_number=c.ticket_number,
        )
        ai_cat = adv.suggested_category
        ai_team = adv.suggested_team
        ai_prio = adv.suggested_priority
        ai_kws = ", ".join(adv.matched_keywords) if adv.matched_keywords else ""
        ai_draft = adv.draft_reply

    return ComplaintOut(
        id=c.id,
        ticket_number=c.ticket_number,
        customer_id=c.customer_id,
        customer_name=cust_name,
        category=c.category,
        category_ar=c.category_ar,
        subject=c.subject,
        details=c.details,
        status=c.status,
        priority=c.priority,
        assigned_to_id=c.assigned_to_id,
        assigned_to_name=assignee_name,
        assigned_team=c.assigned_team or ai_team,
        staff_notes=c.staff_notes,
        resolution_notes=c.resolution_notes,
        is_test=c.is_test or False,
        sla_due_at=sla_eval.due_at,
        sla_breached=sla_eval.is_breached,
        sla_remaining_hours=sla_eval.remaining_hours,
        sla_status_label=sla_eval.status_label,
        ai_suggested_category=ai_cat,
        ai_suggested_team=ai_team,
        ai_suggested_priority=ai_prio,
        ai_matched_keywords=ai_kws,
        ai_draft_reply=ai_draft,
        ai_draft_status=c.ai_draft_status or "PENDING_REVIEW",
        customer_reply=c.customer_reply,
        customer_reply_at=c.customer_reply_at,
        customer_replied_by_id=c.customer_replied_by_id,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("/complaints", response_model=PaginatedComplaintsOut)
async def list_all_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    team_filter: Optional[str] = Query(None, alias="team"),
    search: Optional[str] = Query(None, alias="search"),
    include_test: bool = Query(False, alias="include_test"),
    sort_by: str = Query("created_at", alias="sort_by"),
    sort_order: str = Query("desc", alias="sort_order"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """List operational complaints with server-side pagination, search, filters, sorting, and SLA metrics."""
    stmt = select(Complaint)

    # 1. Filter by Status
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(Complaint.status == status_filter)

    # 2. Filter by Category
    if category_filter and category_filter != "ALL":
        stmt = stmt.where(Complaint.category == category_filter)

    # 3. Filter by Priority
    if priority_filter and priority_filter != "ALL":
        stmt = stmt.where(Complaint.priority == priority_filter)

    # 4. Filter by Team
    if team_filter and team_filter != "ALL":
        stmt = stmt.where(Complaint.assigned_team == team_filter)

    # 5. Default view hides duplicate test complaints (relying strictly on is_test)
    if not include_test:
        stmt = stmt.where(Complaint.is_test.is_(False) | Complaint.is_test.is_(None))

    # 6. Search across ticket number, subject, details, and customer name
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.outerjoin(User, Complaint.customer_id == User.id).where(
            Complaint.ticket_number.ilike(term) |
            Complaint.subject.ilike(term) |
            Complaint.details.ilike(term) |
            User.full_name.ilike(term)
        )

    # Total count for pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0
    total_pages = max(1, (total + page_size - 1) // page_size)

    # 7. Sorting
    order_col = Complaint.created_at
    if sort_by == "priority":
        order_col = Complaint.priority
    elif sort_by == "sla_due_at":
        order_col = Complaint.sla_due_at

    if sort_order.lower() == "asc":
        stmt = stmt.order_by(order_col.asc())
    else:
        stmt = stmt.order_by(order_col.desc())

    # Pagination slice
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    complaints = result.scalars().all()
    now_utc = datetime.now(timezone.utc)

    items = [await serialize_complaint_out(c, db, now_utc) for c in complaints]

    return PaginatedComplaintsOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/complaints/{complaint_id}", response_model=ComplaintOut)
async def update_complaint_status(
    complaint_id: str,
    update_data: ComplaintStatusUpdate,
    current_user: User = Depends(
        require_roles(["customer_service", "operations_officer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update complaint status, assign staff notes, or finalize resolution with strict transition checks."""
    stmt = select(Complaint).where(Complaint.id == complaint_id)
    result = await db.execute(stmt)
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found.")

    changes = {}

    # Strict state transition validation (409 Conflict if invalid)
    if update_data.status and update_data.status != complaint.status:
        validate_complaint_transition(complaint.status, update_data.status)
        changes["old_status"] = complaint.status
        changes["new_status"] = update_data.status
        complaint.status = update_data.status

    if update_data.priority and update_data.priority in VALID_COMPLAINT_PRIORITIES:
        changes["priority"] = update_data.priority
        complaint.priority = update_data.priority
        complaint.sla_due_at = calculate_sla_due_at(complaint.created_at, complaint.priority)

    if update_data.assigned_team:
        changes["assigned_team"] = update_data.assigned_team
        complaint.assigned_team = update_data.assigned_team

    if update_data.assigned_to_id is not None:
        changes["assigned_to_id"] = update_data.assigned_to_id
        complaint.assigned_to_id = update_data.assigned_to_id
    elif not complaint.assigned_to_id:
        complaint.assigned_to_id = current_user.id

    if update_data.staff_notes is not None:
        complaint.staff_notes = update_data.staff_notes

    if update_data.resolution_notes is not None:
        complaint.resolution_notes = update_data.resolution_notes

    # Human-Approved customer reply
    if update_data.customer_reply is not None:
        changes["customer_reply_updated"] = True
        complaint.customer_reply = update_data.customer_reply
        complaint.customer_reply_at = datetime.now(timezone.utc)
        complaint.customer_replied_by_id = current_user.id

    if update_data.ai_draft_status:
        complaint.ai_draft_status = update_data.ai_draft_status

    await db.commit()
    await db.refresh(complaint)

    await log_audit_event(
        db,
        action="UPDATE_COMPLAINT_STATUS",
        resource_type="COMPLAINT",
        resource_id=complaint.id,
        user=current_user,
        details={
            "ticket_number": complaint.ticket_number,
            "status": complaint.status,
            **changes,
        },
    )

    return await serialize_complaint_out(complaint, db)


@router.post("/complaints/{complaint_id}/advisory", response_model=AdvisoryClassificationResult)
async def get_complaint_advisory(
    complaint_id: str,
    current_user: User = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """Generate on-demand advisory classification and draft reply suggestions."""
    stmt = select(Complaint).where(Complaint.id == complaint_id)
    result = await db.execute(stmt)
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint ticket not found.")

    cust_res = await db.execute(select(User.full_name).where(User.id == complaint.customer_id))
    cust_name = cust_res.scalar_one_or_none() or "Customer"

    return classify_complaint_deterministically(
        subject=complaint.subject,
        details=complaint.details,
        customer_name=cust_name,
        ticket_number=complaint.ticket_number,
    )


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
    """List synthetic KYC verification queues with status filter and image URLs."""
    stmt = select(KycVerification)
    if status_filter and status_filter.upper() != "ALL":
        target = status_filter.upper()
        if target == "APPROVED_SIMULATED":
            stmt = stmt.where(KycVerification.status.in_(["APPROVED_SIMULATED", "VERIFIED_SYNTHETIC"]))
        else:
            stmt = stmt.where(KycVerification.status == target)
    stmt = stmt.order_by(desc(KycVerification.created_at))

    result = await db.execute(stmt)
    records = result.scalars().all()
    
    out_list = []
    for k in records:
        out = KycVerificationOut.model_validate(k)
        for ext in ["png", "jpg", "jpeg", "webp"]:
            if os.path.exists(os.path.join(UPLOAD_DIR, f"{k.id}.{ext}")):
                out.image_url = f"/api/v1/employee/kyc-verifications/{k.id}/image"
                break
        out_list.append(out)
    return out_list


@router.get("/kyc-verifications/{kyc_id}/image")
async def get_kyc_verification_image(
    kyc_id: str,
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "operations_officer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Serve uploaded synthetic card image to authorized staff members."""
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = os.path.join(UPLOAD_DIR, f"{kyc_id}.{ext}")
        if os.path.exists(path):
            media_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
            return FileResponse(path, media_type=media_type)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document image not found for this case.")


@router.post("/kyc-verifications/upload", response_model=KycVerificationOut)
async def upload_kyc_verification(
    file: UploadFile = File(..., description="Synthetic Egyptian National ID image (JPEG, PNG, WebP)"),
    customer_id: Optional[str] = Form(None, description="Optional target customer user ID"),
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "operations_officer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Ingest synthetic National ID card, run Document AI OCR, persist image, and queue for compliance review."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum permitted limit of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    if len(content) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is too small to be a valid image.",
        )

    if not is_valid_image_header(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Expected verified JPEG, PNG, or WebP magic bytes.",
        )

    record_id = str(uuid.uuid4())
    img_ext = "png"
    if content.startswith(b"\xFF\xD8\xFF"):
        img_ext = "jpg"
    elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        img_ext = "webp"

    img_path = os.path.join(UPLOAD_DIR, f"{record_id}.{img_ext}")
    with open(img_path, "wb") as f:
        f.write(content)

    case_id = f"case-{uuid.uuid4().hex[:8]}"
    ocr_result = image_ocr_pipeline.process_image(
        image_input=content,
        case_id=case_id,
    )

    if ocr_result.get("ingestion_status") == "FAIL":
        err_msg = ocr_result.get("error", "Image decoding failed.")
        if "dimensions" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Deterministic KYC Cross-Field & Quality Mismatch Evaluation
    mismatch_eval = kyc_check_service.evaluate_case(ocr_result)
    ocr_result["mismatch_evaluation"] = mismatch_eval
    reasons_list = mismatch_eval.get("reasons", [])
    mismatch_reasons_json_str = json.dumps(reasons_list, ensure_ascii=False)

    # Invariant: OCR extraction NEVER auto-approves identity.
    # Case is escalated to FLAGGED if critical issues exist, otherwise PENDING_REVIEW
    initial_status = mismatch_eval.get("recommended_status", "PENDING_REVIEW")
    tracking_num = f"KYC-{uuid.uuid4().hex[:8].upper()}"
    extracted_nid_val = ocr_result.get("masked_national_id", "****")

    # Record uploader identity for genuine four-eyes segregation of duties
    ocr_result["uploader_id"] = current_user.id
    ocr_result["image_url"] = f"/api/v1/employee/kyc-verifications/{record_id}/image"

    record = KycVerification(
        id=record_id,
        tracking_number=tracking_num,
        customer_id=customer_id or current_user.id,
        synthetic_national_id=extracted_nid_val if extracted_nid_val != "****" else "29500000000000",
        document_type="EGYPTIAN_NATIONAL_ID_SYNTHETIC",
        status="PENDING_REVIEW",
        extracted_data_json=json.dumps(ocr_result, ensure_ascii=False),
        mismatch_reasons_json=mismatch_reasons_json_str,
        reviewer_id=None,
        reviewer_notes=None,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    await log_audit_event(
        db,
        action="UPLOAD_KYC_DOCUMENT",
        resource_type="KYC",
        resource_id=record.id,
        user=current_user,
        details={
            "tracking_number": record.tracking_number,
            "ocr_status": ocr_result.get("ocr_status"),
            "compound_status": ocr_result.get("compound_status"),
            "review_status": ocr_result.get("review_status"),
            "mismatch_reasons": mismatch_eval.get("reason_codes", []),
            "is_escalated": mismatch_eval.get("is_escalated", False),
            "uploader_id": current_user.id,
        },
    )

    out = KycVerificationOut.model_validate(record)
    out.image_url = f"/api/v1/employee/kyc-verifications/{record.id}/image"
    return out


@router.patch("/kyc-verifications/{kyc_id}", response_model=KycVerificationOut)
async def review_kyc_verification(
    kyc_id: str,
    review_data: KycReviewRequest,
    current_user: User = Depends(
        require_roles(["compliance_reviewer", "branch_manager", "admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Review and update synthetic KYC document verification status with four-eyes and state transition guards."""
    stmt = select(KycVerification).where(KycVerification.id == kyc_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC record not found.")

    # 1. Four-Eyes Segregation of Duties Enforcement (403 Forbidden on self-review)
    uploader_id = None
    try:
        parsed_data = json.loads(record.extracted_data_json or "{}")
        uploader_id = parsed_data.get("uploader_id")
    except Exception:
        pass

    if current_user.id == uploader_id or (uploader_id is None and current_user.id == record.customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Four-eyes segregation of duties violation: The staff member who uploaded this document cannot review or approve it.",
        )

    # 2. Strict State Transition Validation (409 Conflict)
    current_status = record.status
    if current_status == "VERIFIED_SYNTHETIC":
        current_status = "APPROVED_SIMULATED"

    target_status = review_data.status
    if target_status == "VERIFIED_SYNTHETIC":
        target_status = "APPROVED_SIMULATED"

    ALLOWED_TRANSITIONS = {
        "PENDING_REVIEW": {"APPROVED_SIMULATED", "REJECTED", "INFO_REQUESTED"},
        "INFO_REQUESTED": {"APPROVED_SIMULATED", "REJECTED"},
        "APPROVED_SIMULATED": set(),  # Terminal state
        "REJECTED": set(),            # Terminal state
    }

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Illegal state transition: Case in status '{current_status}' cannot transition to '{target_status}'.",
        )

    old_status = record.status
    record.status = target_status
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
        details={
            "previous_status": old_status,
            "new_status": target_status,
            "reviewer_notes": review_data.reviewer_notes or "",
            "tracking_number": record.tracking_number,
        },
    )

    out = KycVerificationOut.model_validate(record)
    for ext in ["png", "jpg", "jpeg", "webp"]:
        if os.path.exists(os.path.join(UPLOAD_DIR, f"{record.id}.{ext}")):
            out.image_url = f"/api/v1/employee/kyc-verifications/{record.id}/image"
            break
    return out


# --- 7. Simulated Account Opening Requests Review ---

REVIEWER_ROLES = ["operations_officer", "branch_manager", "compliance_reviewer", "admin"]

PRODUCT_NAME_MAP = {
    "prod-01": "Classic Current Account",
    "prod-02": "High-Yield Monthly Savings Account",
    "prod-03": "Nile Platinum 3-Year Certificate of Deposit",
}

CARD_NAME_MAP = {
    "DEBIT_VISA_CLASSIC": "Nile Classic Visa Debit Card",
    "DEBIT_MASTERCARD_TITANIUM": "Nile Titanium Mastercard Debit Card",
    "CREDIT_VISA_PLATINUM": "Nile Platinum Visa Credit Card",
    "PREPAID_MEEZA": "Nile Meeza National Prepaid Card",
}

async def serialize_emp_account_request(record: AccountOpeningRequest, db: AsyncSession) -> AccountOpeningRequestOut:
    data = AccountOpeningRequestOut.model_validate(record)
    data.product_name = PRODUCT_NAME_MAP.get(record.product_id, record.product_id)
    cust_stmt = select(User.full_name).where(User.id == record.customer_id)
    cust_name = (await db.execute(cust_stmt)).scalar_one_or_none()
    data.customer_name = cust_name or "Customer"
    return data

async def serialize_emp_card_request(record: CardRequest, db: AsyncSession) -> CardRequestOut:
    data = CardRequestOut.model_validate(record)
    data.card_name = CARD_NAME_MAP.get(record.card_type, record.card_type)
    cust_stmt = select(User.full_name).where(User.id == record.customer_id)
    cust_name = (await db.execute(cust_stmt)).scalar_one_or_none()
    data.customer_name = cust_name or "Customer"
    return data


@router.get("/account-requests", response_model=List[AccountOpeningRequestOut])
async def list_all_account_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """List operational account opening requests with optional status filter."""
    stmt = select(AccountOpeningRequest)
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(AccountOpeningRequest.status == status_filter)
    stmt = stmt.order_by(desc(AccountOpeningRequest.created_at))

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [await serialize_emp_account_request(r, db) for r in records]


@router.get("/account-requests/{request_id}", response_model=AccountOpeningRequestOut)
async def get_account_request_detail(
    request_id: str,
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full detail of an account opening request."""
    stmt = select(AccountOpeningRequest).where(AccountOpeningRequest.id == request_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found.")
    return await serialize_emp_account_request(record, db)


@router.get("/account-requests/{request_id}/evaluate", response_model=RequestRuleEvaluationResult)
async def evaluate_account_request(
    request_id: str,
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Run deterministic business rules evaluation against customer profile & KYC status."""
    stmt = select(AccountOpeningRequest).where(AccountOpeningRequest.id == request_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found.")

    cust_stmt = select(User).where(User.id == record.customer_id)
    customer = (await db.execute(cust_stmt)).scalars().first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked customer profile not found.")

    return await evaluate_account_opening_rules(record, customer, db)


@router.patch("/account-requests/{request_id}/review", response_model=AccountOpeningRequestOut)
async def review_account_request(
    request_id: str,
    review_data: RequestReviewAction,
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Review and transition simulated account opening request status.
    
    Enforces four-eyes dual control, strict state machine transitions, and audit logging.
    """
    stmt = select(AccountOpeningRequest).where(AccountOpeningRequest.id == request_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found.")

    # 1. Four-eyes dual control: Submitter cannot review or approve own request
    if current_user.id == record.customer_id or current_user.id == record.submitted_by_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Four-eyes principle violation: You cannot review an account request you submitted.",
        )

    # 2. State machine validation
    old_status = record.status
    target_status = review_data.status
    if not validate_transition(old_status, target_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from '{old_status}' to '{target_status}'.",
        )

    # 3. Mandatory rejection reason check
    if target_status == "REJECTED":
        if not review_data.rejection_reason or not review_data.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A mandatory rejection reason is required when rejecting an account opening request.",
            )
        record.rejection_reason = review_data.rejection_reason.strip()

    # 4. Mandatory completion check
    now_utc = datetime.now(timezone.utc)
    if target_status == "SIMULATED_COMPLETED":
        if old_status != "APPROVED_SIMULATED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request must be in APPROVED_SIMULATED status before marking as completed.",
            )
        record.completed_at = now_utc

    record.status = target_status
    record.reviewer_id = current_user.id
    record.reviewer_notes = review_data.notes or record.reviewer_notes
    record.reviewed_at = now_utc

    await db.commit()
    await db.refresh(record)

    await log_audit_event(
        db,
        action=f"REVIEW_ACCOUNT_REQUEST_{target_status}",
        resource_type="ACCOUNT_REQUEST",
        resource_id=record.id,
        user=current_user,
        details={
            "reference_number": record.reference_number,
            "previous_status": old_status,
            "new_status": target_status,
            "reviewer_notes": review_data.notes or "",
            "rejection_reason": record.rejection_reason or "",
        },
    )

    return await serialize_emp_account_request(record, db)


# --- 8. Simulated Card Requests Review ---

@router.get("/card-requests", response_model=List[CardRequestOut])
async def list_all_card_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """List operational card issuance requests with optional status filter."""
    stmt = select(CardRequest)
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(CardRequest.status == status_filter)
    stmt = stmt.order_by(desc(CardRequest.created_at))

    result = await db.execute(stmt)
    records = result.scalars().all()
    return [await serialize_emp_card_request(r, db) for r in records]


@router.get("/card-requests/{request_id}", response_model=CardRequestOut)
async def get_card_request_detail(
    request_id: str,
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full detail of a card request."""
    stmt = select(CardRequest).where(CardRequest.id == request_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card request not found.")
    return await serialize_emp_card_request(record, db)


@router.patch("/card-requests/{request_id}/review", response_model=CardRequestOut)
async def review_card_request(
    request_id: str,
    review_data: RequestReviewAction,
    current_user: User = Depends(require_roles(REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Review and transition simulated card issuance request status."""
    stmt = select(CardRequest).where(CardRequest.id == request_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card request not found.")

    # 1. Four-eyes dual control
    if current_user.id == record.customer_id or current_user.id == record.submitted_by_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Four-eyes principle violation: You cannot review a card request you submitted.",
        )

    # 2. State machine validation
    old_status = record.status
    target_status = review_data.status
    if not validate_transition(old_status, target_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from '{old_status}' to '{target_status}'.",
        )

    # 3. Mandatory rejection reason check
    if target_status == "REJECTED":
        if not review_data.rejection_reason or not review_data.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A mandatory rejection reason is required when rejecting a card request.",
            )
        record.rejection_reason = review_data.rejection_reason.strip()

    # 4. Mandatory completion check
    now_utc = datetime.now(timezone.utc)
    if target_status == "SIMULATED_COMPLETED":
        if old_status != "APPROVED_SIMULATED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request must be in APPROVED_SIMULATED status before marking as completed.",
            )
        record.completed_at = now_utc

    record.status = target_status
    record.reviewer_id = current_user.id
    record.reviewer_notes = review_data.notes or record.reviewer_notes
    record.reviewed_at = now_utc

    await db.commit()
    await db.refresh(record)

    await log_audit_event(
        db,
        action=f"REVIEW_CARD_REQUEST_{target_status}",
        resource_type="CARD_REQUEST",
        resource_id=record.id,
        user=current_user,
        details={
            "reference_number": record.reference_number,
            "previous_status": old_status,
            "new_status": target_status,
            "reviewer_notes": review_data.notes or "",
            "rejection_reason": record.rejection_reason or "",
        },
    )

    return await serialize_emp_card_request(record, db)



