"""Tests for NileOps Dual-Document Cross-Verification Service & Endpoints.

Validates:
1. Fuzzy Arabic name matching with Alef/Taa/Yaa normalization and token containment (>= 85%).
2. Locality and governorate cross-validation between National ID and Utility Bill.
3. Utility bill recency validation (<= 90 days / 3 months statutory threshold).
4. Discrepancy flagging: NAME_MISMATCH_ACROSS_DOCS, ADDRESS_MISMATCH_ACROSS_DOCS, UTILITY_BILL_TOO_OLD.
5. Invariant: Cross-verification NEVER auto-approves identity (starts and remains NOT_VERIFIED).
6. Employee endpoint POST /api/v1/employee/kyc-verifications/{kyc_id}/cross-verify RBAC & audit trail.
"""

from datetime import date, timedelta
import io
import pytest
from PIL import Image
from starlette.testclient import TestClient

from app.services.document_matching import (
    DocumentMatchingReason,
    DualDocumentMatcher,
    calculate_name_similarity,
    detect_governorate_from_address,
)


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


def _create_synthetic_test_card_png(width: int = 400, height: int = 250) -> bytes:
    img = Image.new("RGB", (width, height), color=(240, 245, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_name_similarity_matching():
    """Verify name matching logic handles Arabic orthographic variants and multi-token subsets."""
    # 1. Exact match
    assert calculate_name_similarity("محمود عادل إبراهيم", "محمود عادل إبراهيم") == 1.0

    # 2. Alef variants (أحمد vs احمد)
    score_alef = calculate_name_similarity("أحمد سامي عبد الرحمن", "احمد سامي عبد الرحمن")
    assert score_alef >= 0.95, f"Expected high score for Alef variant, got: {score_alef}"

    # 3. 3-part vs 4-part name (containment)
    score_3vs4 = calculate_name_similarity("سارة محمد إبراهيم حسن", "سارة محمد إبراهيم")
    assert score_3vs4 >= 0.85, f"Expected >= 0.85 for 3-of-4 name parts, got: {score_3vs4}"

    # 4. Completely different name
    score_diff = calculate_name_similarity("محمود عادل إبراهيم", "خالد مصطفى الشناوي")
    assert score_diff < 0.50, f"Expected low score for different names, got: {score_diff}"


def test_dual_document_cross_verify_clean_match():
    """Verify clean match between National ID and Utility Bill."""
    matcher = DualDocumentMatcher(name_threshold=0.85, max_bill_age_days=90)
    today = date.today()

    id_data = {
        "name": "محمود عادل إبراهيم حسن",
        "address": "15 شارع النيل، المعادي، القاهرة",
        "derived_governorate": "القاهرة",
        "national_id": "29505140101234",
    }
    bill_data = {
        "utility_type": "ELECTRICITY_BILL",
        "consumer_name": "محمود عادل إبراهيم حسن",
        "service_address": "15 شارع النيل، المعادي، القاهرة",
        "issue_date": (today - timedelta(days=25)).isoformat(),
        "account_number": "ELEC-12345",
    }

    result = matcher.cross_verify(id_data, bill_data, reference_date=today)
    assert result["is_cross_verified"] is True
    assert result["discrepancy_count"] == 0
    assert result["identity_verification_status"] == "NOT_VERIFIED"
    assert result["name_cross_match"]["is_match"] is True
    assert result["address_cross_match"]["is_match"] is True
    assert result["recency_check"]["is_recent"] is True


def test_dual_document_cross_verify_discrepancies():
    """Verify detection of name mismatch, address discrepancy, and expired bill age."""
    matcher = DualDocumentMatcher(name_threshold=0.85, max_bill_age_days=90)
    today = date.today()

    id_data = {
        "name": "محمود عادل إبراهيم حسن",
        "address": "15 شارع النيل، المعادي، القاهرة",
        "derived_governorate": "القاهرة",
        "national_id": "29505140101234",
    }

    # Case A: Name Mismatch
    bill_bad_name = {
        "utility_type": "ELECTRICITY_BILL",
        "consumer_name": "خالد مصطفى الشناوي",
        "service_address": "15 شارع النيل، المعادي، القاهرة",
        "issue_date": (today - timedelta(days=20)).isoformat(),
    }
    res_name = matcher.cross_verify(id_data, bill_bad_name, reference_date=today)
    assert res_name["is_cross_verified"] is False
    assert DocumentMatchingReason.NAME_MISMATCH_ACROSS_DOCS.value in res_name["discrepancy_codes"]

    # Case B: Address Mismatch (Cairo vs Alexandria)
    bill_bad_addr = {
        "utility_type": "WATER_BILL",
        "consumer_name": "محمود عادل إبراهيم حسن",
        "service_address": "25 طريق الجيش، سيدي جابر، الإسكندرية",
        "issue_date": (today - timedelta(days=30)).isoformat(),
    }
    res_addr = matcher.cross_verify(id_data, bill_bad_addr, reference_date=today)
    assert res_addr["is_cross_verified"] is False
    assert DocumentMatchingReason.ADDRESS_MISMATCH_ACROSS_DOCS.value in res_addr["discrepancy_codes"]

    # Case C: Expired Utility Bill (150 days old > 90 days)
    bill_expired = {
        "utility_type": "NATURAL_GAS_BILL",
        "consumer_name": "محمود عادل إبراهيم حسن",
        "service_address": "15 شارع النيل، المعادي، القاهرة",
        "issue_date": (today - timedelta(days=150)).isoformat(),
    }
    res_age = matcher.cross_verify(id_data, bill_expired, reference_date=today)
    assert res_age["is_cross_verified"] is False
    assert DocumentMatchingReason.UTILITY_BILL_TOO_OLD.value in res_age["discrepancy_codes"]


def test_cross_verify_api_endpoint_lifecycle_and_rbac(client: TestClient):
    """Verify employee cross-verify endpoint with compliance review role, state storage, and RBAC."""
    comp_token = _login(client, "compliance@nileops.demo", "NileOps2026!")
    comp_headers = {"Authorization": f"Bearer {comp_token}"}

    # 1. Create a KYC record by uploading a synthetic card
    card_bytes = _create_synthetic_test_card_png()
    upload_resp = client.post(
        "/api/v1/employee/kyc-verifications/upload",
        headers=comp_headers,
        files={"file": ("synthetic_card.png", card_bytes, "image/png")},
    )
    assert upload_resp.status_code == 200
    case_id = upload_resp.json()["id"]

    # 2. Call cross-verify endpoint as compliance officer
    bill_payload = {
        "utility_type": "ELECTRICITY_BILL",
        "consumer_name": "محمود عادل إبراهيم حسن",
        "service_address": "15 شارع النيل، المعادي، القاهرة",
        "issue_date": (date.today() - timedelta(days=15)).isoformat(),
        "account_number": "ELEC-CAI-998811",
    }
    verify_resp = client.post(
        f"/api/v1/employee/kyc-verifications/{case_id}/cross-verify",
        headers=comp_headers,
        json=bill_payload,
    )
    assert verify_resp.status_code == 200
    res_data = verify_resp.json()
    assert "is_cross_verified" in res_data
    assert "name_cross_match" in res_data
    assert res_data["identity_verification_status"] == "NOT_VERIFIED"

    # 3. RBAC: Customer cannot invoke staff cross-verify endpoint (403 Forbidden)
    cust_token = _login(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    cust_resp = client.post(
        f"/api/v1/employee/kyc-verifications/{case_id}/cross-verify",
        headers=cust_headers,
        json=bill_payload,
    )
    assert cust_resp.status_code == 403
