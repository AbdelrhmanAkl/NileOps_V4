"""Customer Portal Endpoints."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, log_audit_event, require_customer
from app.models.banking import Account, Transaction
from app.models.complaint import Complaint
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.banking import AccountOut, TransactionOut
from app.schemas.complaint import ComplaintCreate, ComplaintOut, CustomerComplaintOut
from app.services.complaint_sla import calculate_sla_due_at
from app.services.complaint_intelligence import classify_complaint_deterministically
import json
import os
from app.core.rate_limit import limiter
from app.models.kyc import KycVerification
from app.schemas.kyc import CustomerKycOut
from app.schemas.requests import (
    AccountOpeningRequestCreate,
    AccountOpeningRequestOut,
    CardRequestCreate,
    CardRequestOut,
)
from app.services.image_pipeline import ImageOCRPipeline, is_valid_image_header
from app.services.kyc_checks import KycCheckService
from fastapi import File, Request, UploadFile

router = APIRouter(prefix="/customer", tags=["Customer Portal"])

image_ocr_pipeline = ImageOCRPipeline()
kyc_check_service = KycCheckService()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "kyc_uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

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


@router.get("/complaints", response_model=List[CustomerComplaintOut])
async def list_customer_complaints(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List complaints submitted by the authenticated customer (human-approved reply only, no internal notes)."""
    stmt = (
        select(Complaint)
        .where(
            Complaint.customer_id == current_user.id,
            (Complaint.is_test.is_(False) | Complaint.is_test.is_(None)),
        )
        .order_by(desc(Complaint.created_at))
    )
    result = await db.execute(stmt)
    complaints = result.scalars().all()
    return [CustomerComplaintOut.model_validate(c) for c in complaints]


@router.post("/complaints", response_model=CustomerComplaintOut, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    complaint_in: ComplaintCreate,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Submit a simulated operational banking complaint."""
    # Generate unique ticket number
    ticket_num = f"CMP-2026-{uuid.uuid4().hex[:6].upper()}"
    cat_ar = CATEGORY_AR_MAP.get(complaint_in.category, "شكوى مصرفية")

    # Run deterministic advisory classification and template generation
    advisory = classify_complaint_deterministically(
        subject=complaint_in.subject,
        details=complaint_in.details,
        customer_name=current_user.full_name,
        ticket_number=ticket_num,
    )
    now_utc = datetime.now(timezone.utc)
    sla_due = calculate_sla_due_at(now_utc, advisory.suggested_priority)

    complaint = Complaint(
        ticket_number=ticket_num,
        customer_id=current_user.id,
        category=complaint_in.category,
        category_ar=cat_ar,
        subject=complaint_in.subject,
        details=complaint_in.details,
        status="OPEN",
        priority=advisory.suggested_priority,
        assigned_team=advisory.suggested_team,
        sla_due_at=sla_due,
        sla_breached=False,
        ai_suggested_category=advisory.suggested_category,
        ai_suggested_team=advisory.suggested_team,
        ai_suggested_priority=advisory.suggested_priority,
        ai_matched_keywords=", ".join(advisory.matched_keywords) if advisory.matched_keywords else "",
        ai_draft_reply=advisory.draft_reply,
        ai_draft_status="PENDING_REVIEW",
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
        details={"ticket_number": ticket_num, "category": complaint_in.category, "priority": complaint.priority},
    )

    return CustomerComplaintOut.model_validate(complaint)


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

def serialize_account_request(record, customer_name: Optional[str] = None) -> AccountOpeningRequestOut:
    data = AccountOpeningRequestOut.model_validate(record)
    data.product_name = PRODUCT_NAME_MAP.get(record.product_id, record.product_id)
    if customer_name:
        data.customer_name = customer_name
    return data

def serialize_card_request(record, customer_name: Optional[str] = None) -> CardRequestOut:
    data = CardRequestOut.model_validate(record)
    data.card_name = CARD_NAME_MAP.get(record.card_type, record.card_type)
    if customer_name:
        data.customer_name = customer_name
    return data


# --- 4. Simulated Account Opening Requests ---

@router.post("/account-requests", response_model=AccountOpeningRequestOut, status_code=status.HTTP_201_CREATED)
async def submit_account_opening_request(
    req_in: AccountOpeningRequestCreate,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Submit a simulated retail account opening request.
    
    SIMULATION: No real bank account is created.
    """
    # 1. Idempotency Key check
    if req_in.idempotency_key:
        stmt = select(AccountOpeningRequest).where(
            AccountOpeningRequest.idempotency_key == req_in.idempotency_key
        )
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate submission: A request with idempotency key '{req_in.idempotency_key}' already exists.",
            )

    ref_num = f"REQ-ACC-{uuid.uuid4().hex[:8].upper()}"
    now_utc = datetime.now(timezone.utc)

    request = AccountOpeningRequest(
        reference_number=ref_num,
        customer_id=current_user.id,
        product_id=req_in.product_id,
        account_type=req_in.account_type,
        currency=req_in.currency,
        initial_deposit=req_in.initial_deposit,
        monthly_income=req_in.monthly_income,
        employment_status=req_in.employment_status,
        branch_code=req_in.branch_code,
        status="SUBMITTED",
        idempotency_key=req_in.idempotency_key,
        submitted_by_id=current_user.id,
        submitted_at=now_utc,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    await log_audit_event(
        db,
        action="SUBMIT_ACCOUNT_REQUEST",
        resource_type="ACCOUNT_REQUEST",
        resource_id=request.id,
        user=current_user,
        details={
            "reference_number": ref_num,
            "product_id": req_in.product_id,
            "initial_deposit": req_in.initial_deposit,
        },
    )

    return serialize_account_request(request, current_user.full_name)


@router.get("/account-requests", response_model=List[AccountOpeningRequestOut])
async def list_customer_account_requests(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List all account opening requests belonging to authenticated customer."""
    stmt = (
        select(AccountOpeningRequest)
        .where(AccountOpeningRequest.customer_id == current_user.id)
        .order_by(desc(AccountOpeningRequest.created_at))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [serialize_account_request(r, current_user.full_name) for r in records]


@router.get("/account-requests/{request_id}", response_model=AccountOpeningRequestOut)
async def get_customer_account_request(
    request_id: str,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get single account opening request (Strict customer ownership check)."""
    stmt = select(AccountOpeningRequest).where(AccountOpeningRequest.id == request_id)
    result = await db.execute(stmt)
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found.")
    if record.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Request does not belong to your customer profile.",
        )
    return serialize_account_request(record, current_user.full_name)


# --- 5. Simulated Card Issuance Requests ---

@router.post("/card-requests", response_model=CardRequestOut, status_code=status.HTTP_201_CREATED)
async def submit_card_request(
    req_in: CardRequestCreate,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Submit a simulated card issuance request against an existing customer account.
    
    SIMULATION: No real payment card is created.
    """
    # 1. Idempotency Key check
    if req_in.idempotency_key:
        stmt = select(CardRequest).where(CardRequest.idempotency_key == req_in.idempotency_key)
        existing = (await db.execute(stmt)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate submission: A card request with idempotency key '{req_in.idempotency_key}' already exists.",
            )

    # 2. Verify account belongs to customer
    acc_stmt = select(Account).where(
        Account.id == req_in.linked_account_id,
        Account.user_id == current_user.id,
    )
    acc = (await db.execute(acc_stmt)).scalars().first()
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected account does not belong to your customer profile or does not exist.",
        )

    ref_num = f"REQ-CRD-{uuid.uuid4().hex[:8].upper()}"
    now_utc = datetime.now(timezone.utc)

    card_req = CardRequest(
        reference_number=ref_num,
        customer_id=current_user.id,
        linked_account_id=req_in.linked_account_id,
        card_type=req_in.card_type,
        embossed_name=req_in.embossed_name.strip().upper(),
        delivery_branch=req_in.delivery_branch,
        status="SUBMITTED",
        idempotency_key=req_in.idempotency_key,
        submitted_by_id=current_user.id,
        submitted_at=now_utc,
    )
    db.add(card_req)
    await db.commit()
    await db.refresh(card_req)

    await log_audit_event(
        db,
        action="SUBMIT_CARD_REQUEST",
        resource_type="CARD_REQUEST",
        resource_id=card_req.id,
        user=current_user,
        details={
            "reference_number": ref_num,
            "card_type": req_in.card_type,
            "linked_account_id": req_in.linked_account_id,
        },
    )

    return serialize_card_request(card_req, current_user.full_name)


@router.get("/card-requests", response_model=List[CardRequestOut])
async def list_customer_card_requests(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """List all card requests belonging to authenticated customer."""
    stmt = (
        select(CardRequest)
        .where(CardRequest.customer_id == current_user.id)
        .order_by(desc(CardRequest.created_at))
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [serialize_card_request(r, current_user.full_name) for r in records]


@router.get("/card-requests/{request_id}", response_model=CardRequestOut)
async def get_customer_card_request(
    request_id: str,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get single card request (Strict customer ownership check)."""
    stmt = select(CardRequest).where(CardRequest.id == request_id)
    result = await db.execute(stmt)
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card request not found.")
    if record.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Request does not belong to your customer profile.",
        )
    return serialize_card_request(record, current_user.full_name)


@router.post("/kyc-update", response_model=CustomerKycOut)
async def submit_customer_kyc_update(
    request: Request,
    file: UploadFile = File(..., description="Synthetic Egyptian National ID image (JPEG, PNG, WebP)"),
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Customer self-service KYC document update flow.

    Validates document image, extracts fields via Document AI OCR, executes deterministic
    cross-field validation, and routes to compliance review queue.
    National ID is strictly masked in responses and audit logs.
    Identity verification status remains NOT_VERIFIED until explicit four-eyes compliance approval.
    """
    # 1. Rate Limiting (5 requests per 60 seconds per customer)
    await limiter.check_rate_limit(
        request,
        endpoint_tag="customer_kyc_update",
        max_requests=5,
        window_seconds=60,
        identifier_override=f"kyc_update_{current_user.id}",
    )

    # 2. File size and magic byte validation
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

    # 3. Secure disk storage
    record_id = str(uuid.uuid4())
    img_ext = "png"
    if content.startswith(b"\xFF\xD8\xFF"):
        img_ext = "jpg"
    elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        img_ext = "webp"

    img_path = os.path.join(UPLOAD_DIR, f"{record_id}.{img_ext}")
    with open(img_path, "wb") as f:
        f.write(content)

    # 4. OCR pipeline extraction
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

    # 5. Deterministic KYC Cross-Field Mismatch Evaluation
    mismatch_eval = kyc_check_service.evaluate_case(ocr_result)
    ocr_result["mismatch_evaluation"] = mismatch_eval
    reasons_list = mismatch_eval.get("reasons", [])
    mismatch_reasons_json_str = json.dumps(reasons_list, ensure_ascii=False)

    tracking_num = f"KYC-{uuid.uuid4().hex[:8].upper()}"
    extracted_nid_val = ocr_result.get("masked_national_id", "****")

    ocr_result["uploader_id"] = current_user.id
    ocr_result["image_url"] = f"/api/v1/employee/kyc-verifications/{record_id}/image"

    # 6. Database record persistence
    record = KycVerification(
        id=record_id,
        tracking_number=tracking_num,
        customer_id=current_user.id,
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

    # 7. Audit log
    await log_audit_event(
        db,
        action="CUSTOMER_KYC_UPDATE_SUBMITTED",
        resource_type="KYC",
        resource_id=record.id,
        user=current_user,
        details={
            "tracking_number": record.tracking_number,
            "status": record.status,
            "identity_verification_status": "NOT_VERIFIED",
            "is_escalated": mismatch_eval.get("is_escalated", False),
        },
    )

    return CustomerKycOut(
        id=record.id,
        tracking_number=record.tracking_number,
        synthetic_national_id=record.synthetic_national_id,
        document_type=record.document_type,
        status=record.status,
        identity_verification_status="NOT_VERIFIED",
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/kyc-status", response_model=Optional[CustomerKycOut])
async def get_customer_kyc_status(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current customer's latest KYC document verification status."""
    stmt = (
        select(KycVerification)
        .where(KycVerification.customer_id == current_user.id)
        .order_by(desc(KycVerification.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    record = result.scalars().first()
    if not record:
        return None
    return CustomerKycOut(
        id=record.id,
        tracking_number=record.tracking_number,
        synthetic_national_id=record.synthetic_national_id,
        document_type=record.document_type,
        status=record.status,
        identity_verification_status="NOT_VERIFIED",
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


