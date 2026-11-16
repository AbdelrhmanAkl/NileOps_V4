"""Comprehensive Unit, Security, and Governance Tests for KYC Document AI Workspace.

Validates:
1. Synthetic card image ingestion and processing.
2. Invariant: Extraction NEVER auto-approves identity (starts in PENDING_REVIEW).
3. Invariant: National ID is masked by default in schemas and API responses.
4. Human review actions (Approve simulated, Reject with mandatory reason, Request info).
5. True Four-Eyes segregation of duties: Uploader is strictly blocked from self-review (403 Forbidden).
6. State machine integrity: Invalid state transitions (e.g. from APPROVED_SIMULATED to REJECTED) are blocked (409 Conflict).
7. Four-eyes RBAC enforcement (customers and unauthorized staff denied).
8. Immutable audit trail logging for all upload and review actions.
"""

import io
from datetime import datetime, timezone
import pytest
from PIL import Image
from starlette.testclient import TestClient

from app.schemas.kyc import KycReviewRequest, KycVerificationOut


def _create_synthetic_test_card_png(width: int = 400, height: int = 250) -> bytes:
    """Generate in-memory synthetic ID card fixture in valid PNG format."""
    img = Image.new("RGB", (width, height), color=(240, 245, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _login(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and retrieve access token."""
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


def test_kyc_schema_masks_synthetic_national_id():
    """Verify KycVerificationOut schema strictly masks the middle digits of 14-digit IDs."""
    record = KycVerificationOut(
        id="kyc-test-uuid-001",
        tracking_number="KYC-TEST0001",
        customer_id="cust-uuid-001",
        synthetic_national_id="29505140101234",
        document_type="EGYPTIAN_NATIONAL_ID_SYNTHETIC",
        status="PENDING_REVIEW",
        extracted_data_json="{}",
        reviewer_id=None,
        reviewer_notes=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Must preserve first 4 and last 4 digits
    assert record.synthetic_national_id == "2950****1234"
    assert "0101" not in record.synthetic_national_id


def test_kyc_rejection_requires_mandatory_notes():
    """Verify KycReviewRequest schema requires reviewer notes when rejecting a case."""
    # Rejection without notes must fail validation
    with pytest.raises(Exception):
        KycReviewRequest(status="REJECTED", reviewer_notes="")

    with pytest.raises(Exception):
        KycReviewRequest(status="REJECTED", reviewer_notes=None)

    # Rejection with valid reason must pass
    req = KycReviewRequest(status="REJECTED", reviewer_notes="Card photo is blurry; national ID digits unreadable.")
    assert req.status == "REJECTED"
    assert "blurry" in req.reviewer_notes


def test_kyc_end_to_end_lifecycle_and_audit(client: TestClient):
    """Verify complete KYC document ingestion, four-eyes enforcement, transition validation, and audit trail."""
    # Person 1 (Uploader): Compliance Reviewer Nourhan
    comp_token = _login(client, "compliance@nileops.demo", "NileOps2026!")
    comp_headers = {"Authorization": f"Bearer {comp_token}"}

    # Person 2 (Independent Reviewer): Branch Manager Sherif
    mgr_token = _login(client, "manager@nileops.demo", "NileOps2026!")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # 1. Upload Synthetic Card Image as Compliance Reviewer Nourhan
    card_bytes = _create_synthetic_test_card_png()
    upload_resp = client.post(
        "/api/v1/employee/kyc-verifications/upload",
        headers=comp_headers,
        files={"file": ("synthetic_card.png", card_bytes, "image/png")},
    )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    case = upload_resp.json()
    case_id = case["id"]
    tracking_num = case["tracking_number"]

    # Invariant: Must start in PENDING_REVIEW; extraction NEVER auto-approves
    assert case["status"] == "PENDING_REVIEW"
    assert tracking_num.startswith("KYC-")
    assert "****" in case["synthetic_national_id"]
    assert case["image_url"] == f"/api/v1/employee/kyc-verifications/{case_id}/image"

    # 2. Verify Image Serving Endpoint returns 200 with image/png
    img_resp = client.get(f"/api/v1/employee/kyc-verifications/{case_id}/image", headers=mgr_headers)
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/png"
    assert len(img_resp.content) == len(card_bytes)

    # 3. FOUR-EYES ENFORCEMENT: Uploader (Nourhan) attempts to review her own case -> MUST FAIL (403 Forbidden)
    self_review_resp = client.patch(
        f"/api/v1/employee/kyc-verifications/{case_id}",
        headers=comp_headers,
        json={"status": "APPROVED_SIMULATED", "reviewer_notes": "Self-approval attempt"},
    )
    assert self_review_resp.status_code == 403
    assert "Four-eyes" in self_review_resp.json()["detail"]

    # 4. Authorized Independent Reviewer (Sherif) rejects without notes -> MUST FAIL (422)
    reject_fail_resp = client.patch(
        f"/api/v1/employee/kyc-verifications/{case_id}",
        headers=mgr_headers,
        json={"status": "REJECTED", "reviewer_notes": ""},
    )
    assert reject_fail_resp.status_code == 422

    # 5. Authorized Independent Reviewer requests more info -> SUCCESS (200)
    info_resp = client.patch(
        f"/api/v1/employee/kyc-verifications/{case_id}",
        headers=mgr_headers,
        json={"status": "INFO_REQUESTED", "reviewer_notes": "Please provide clearer card back."},
    )
    assert info_resp.status_code == 200
    assert info_resp.json()["status"] == "INFO_REQUESTED"
    assert info_resp.json()["reviewer_notes"] == "Please provide clearer card back."

    # 6. Authorized Independent Reviewer approves simulated -> SUCCESS (200, status APPROVED_SIMULATED)
    approve_resp = client.patch(
        f"/api/v1/employee/kyc-verifications/{case_id}",
        headers=mgr_headers,
        json={"status": "APPROVED_SIMULATED", "reviewer_notes": "Synthetic ID attributes verified against test fixture."},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED_SIMULATED"

    # 7. STATE TRANSITION ENFORCEMENT: Attempt to transition from terminal state APPROVED_SIMULATED -> MUST FAIL (409 Conflict)
    invalid_trans_resp = client.patch(
        f"/api/v1/employee/kyc-verifications/{case_id}",
        headers=mgr_headers,
        json={"status": "REJECTED", "reviewer_notes": "Attempt to reject already approved case."},
    )
    assert invalid_trans_resp.status_code == 409
    assert "Illegal state transition" in invalid_trans_resp.json()["detail"]

    # 8. Verify Audit Logs captured upload and review actions
    audit_resp = client.get("/api/v1/employee/audit-logs?limit=10", headers=mgr_headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    actions = [log["action"] for log in logs]
    assert "UPLOAD_KYC_DOCUMENT" in actions
    assert "REVIEW_KYC" in actions


def test_kyc_rbac_denials_for_unauthorized_users(client: TestClient):
    """Verify strict RBAC: customer cannot access or review KYC cases; CS cannot review."""
    cust_token = _login(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Customer cannot list KYC queue
    list_resp = client.get("/api/v1/employee/kyc-verifications", headers=cust_headers)
    assert list_resp.status_code == 403

    # Customer cannot upload to staff queue
    card_bytes = _create_synthetic_test_card_png()
    upload_resp = client.post(
        "/api/v1/employee/kyc-verifications/upload",
        headers=cust_headers,
        files={"file": ("test.png", card_bytes, "image/png")},
    )
    assert upload_resp.status_code == 403

    # Customer Service role cannot review KYC
    cs_token = _login(client, "cs@nileops.demo", "NileOps2026!")
    cs_headers = {"Authorization": f"Bearer {cs_token}"}
    review_resp = client.patch(
        "/api/v1/employee/kyc-verifications/kyc-fake-id",
        headers=cs_headers,
        json={"status": "APPROVED_SIMULATED", "reviewer_notes": "Attempt by CS"},
    )
    assert review_resp.status_code == 403


def test_kyc_noise_filter_rejects_card_header_as_name():
    """Verify OCR post-processing noise filter rejects card administrative headers as citizen names."""
    from app.services.image_pipeline import ImageOCRPipeline
    from app.services.kyc_checks import KycCheckService, KycReasonCode

    pipeline = ImageOCRPipeline()
    ocr_lines = [
        ("جمهورية مصر العربية", 0.95),
        ("وزارة الداخلية", 0.94),
        ("قطاع مصلحة الأحوال المدنية", 0.93),
        ("بطاقة تحقيق الشخصية", 0.92),
        ("29505140101234", 0.98),
        ("15 شارع النيل، المعادي، القاهرة", 0.91),
    ]
    texts = [line[0] for line in ocr_lines]
    scores = [line[1] for line in ocr_lines]
    extracted = pipeline.extract_fields_from_ocr(texts, scores)
    assert extracted["national_id"] == "29505140101234"
    assert extracted["name"] is None, f"Expected name to be None, got: {extracted['name']}"
    assert extracted["address"] is not None

    service = KycCheckService()
    eval_result = service.evaluate_case(extracted)
    assert eval_result["is_escalated"] is True
    reason_codes = [r["code"] for r in eval_result["reasons"]]
    assert KycReasonCode.MISSING_FIELD_NAME.value in reason_codes


def test_kyc_low_quality_underexposed_image_flags_low_confidence():
    """Verify severely degraded/underexposed images are flagged as LOW_OCR_CONFIDENCE."""
    from app.services.kyc_checks import KycCheckService, KycReasonCode

    extracted_data = {
        "national_id": "29505140101234",
        "national_id_conf": 0.95,
        "name": "محمود عادل إبراهيم حسن",
        "name_conf": 0.90,
        "address": "15 شارع النيل، المعادي، القاهرة",
        "address_conf": 0.90,
        "factory_code": "IS1234567",
        "factory_code_conf": 0.85,
        "quality_metrics": {
            "contrast_std": 6.9,
            "brightness_mean": 66.8,
            "sharpness_laplacian": 45.0,
            "is_blurry": True,
            "is_low_contrast": True,
            "is_underexposed": False,
        },
    }
    service = KycCheckService()
    eval_result = service.evaluate_case(extracted_data)
    assert eval_result["is_escalated"] is True
    reason_codes = [r["code"] for r in eval_result["reasons"]]
    assert KycReasonCode.LOW_OCR_CONFIDENCE.value in reason_codes


def test_kyc_governorate_mismatch_escalates():
    """Verify governorate discrepancy between National ID (Cairo=01) and Address (Alexandria) escalates."""
    from app.services.kyc_checks import KycCheckService, KycReasonCode

    extracted_data = {
        "national_id": "29505140101234",
        "national_id_conf": 0.95,
        "name": "محمود عادل إبراهيم حسن",
        "name_conf": 0.90,
        "address": "25 طريق الجيش، سيدي جابر، الإسكندرية",
        "address_conf": 0.90,
        "derived_birth_date": "1995-05-14",
        "derived_governorate": "القاهرة",
    }
    service = KycCheckService()
    eval_result = service.evaluate_case(extracted_data)
    assert eval_result["is_escalated"] is True
    reason_codes = [r["code"] for r in eval_result["reasons"]]
    assert KycReasonCode.GOVERNORATE_MISMATCH.value in reason_codes


def test_customer_kyc_self_service_update_and_status(client: TestClient):
    """Verify customer can submit KYC update, gets masked response, and status endpoint returns NOT_VERIFIED."""
    cust_token = _login(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 1. Invalid file format rejected
    invalid_file = io.BytesIO(b"Not an image at all but a plain text string")
    bad_resp = client.post(
        "/api/v1/customer/kyc-update",
        headers=cust_headers,
        files={"file": ("fake.png", invalid_file, "image/png")},
    )
    assert bad_resp.status_code == 400

    # 2. Valid synthetic image accepted
    card_bytes = _create_synthetic_test_card_png()
    upload_resp = client.post(
        "/api/v1/customer/kyc-update",
        headers=cust_headers,
        files={"file": ("my_id_synthetic.png", card_bytes, "image/png")},
    )
    assert upload_resp.status_code == 200, f"Customer KYC upload failed: {upload_resp.text}"
    data = upload_resp.json()
    assert data["status"] == "PENDING_REVIEW"
    assert data["identity_verification_status"] == "NOT_VERIFIED"
    assert "****" in data["synthetic_national_id"]
    assert "tracking_number" in data
    assert data["tracking_number"].startswith("KYC-")

    # 3. Retrieve status via GET /api/v1/customer/kyc-status
    status_resp = client.get("/api/v1/customer/kyc-status", headers=cust_headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data is not None
    assert status_data["tracking_number"] == data["tracking_number"]
    assert status_data["status"] == "PENDING_REVIEW"
    assert status_data["identity_verification_status"] == "NOT_VERIFIED"
    assert "****" in status_data["synthetic_national_id"]

    # 4. Staff cannot call customer KYC update endpoint
    mgr_token = _login(client, "manager@nileops.demo", "NileOps2026!")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    staff_resp = client.post(
        "/api/v1/customer/kyc-update",
        headers=mgr_headers,
        files={"file": ("staff.png", card_bytes, "image/png")},
    )
    assert staff_resp.status_code == 403


