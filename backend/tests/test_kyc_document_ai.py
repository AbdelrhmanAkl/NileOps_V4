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
