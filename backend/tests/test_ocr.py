"""Comprehensive Tests for Egyptian National ID Validation & OCR Service.

Evaluates character normalization, leap year calendar math, governorate allowlists,
Decision Tables 7.1.1 & 7.1.2, profile resolution, and permanent identity boundary invariants.
Strict synthetic data fixtures only — zero authentic Egyptian IDs.
"""

import pytest
from starlette.testclient import TestClient
from app.services.ocr import (
    CompoundStatus,
    FormatValidationStatus,
    GovernorateReferenceStatus,
    IdentityVerificationStatus,
    NormalizationStatus,
    OCRExtractionStatus,
    ReviewRoutingStatus,
    WorkflowContext,
    ocr_service,
)


def test_valid_synthetic_national_id_western(client: TestClient):
    """Test valid synthetic 1995 Cairo male ID with Western Arabic digits."""
    payload = {
        "raw_national_id": "29505140101234",
        "workflow_context": "STRUCTURED_INTAKE",
    }
    resp = client.post("/api/v1/ocr/validate-national-id", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["normalization_status"] == NormalizationStatus.NORMALIZATION_PASSED
    assert data["format_status"] == FormatValidationStatus.FORMAT_VALID
    assert data["governorate_status"] == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED
    assert data["derived_governorate"] == "القاهرة"
    assert data["derived_gender"] == "Male"
    assert data["derived_birth_date"] == "1995-05-14"
    assert data["masked_national_id"] == "2950****1234"
    assert data["review_status"] == ReviewRoutingStatus.NO_REVIEW_REQUIRED
    assert data["identity_verification_status"] == IdentityVerificationStatus.NOT_VERIFIED


def test_eastern_arabic_digit_normalization(client: TestClient):
    """Test normalization of Eastern Arabic-Indic digits (٢٩٥٠٥١٤٠١٠١٢٣٤)."""
    payload = {
        "raw_national_id": "٢٩٥٠٥١٤٠١٠١٢٣٤",
        "workflow_context": "STRUCTURED_INTAKE",
    }
    resp = client.post("/api/v1/ocr/validate-national-id", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["normalization_status"] == NormalizationStatus.NORMALIZATION_PASSED
    assert data["format_status"] == FormatValidationStatus.FORMAT_VALID
    assert data["masked_national_id"] == "2950****1234"
    assert data["derived_birth_date"] == "1995-05-14"


def test_leap_year_validation():
    """Test leap year calendar validation (Feb 29 on leap vs non-leap years)."""
    # 2000 is a valid leap year (Century 3, YY=00, MM=02, DD=29)
    res_leap = ocr_service.process_national_id(
        case_id="case-leap",
        raw_id_input="30002290101234",
        workflow_context=WorkflowContext.STRUCTURED_INTAKE,
    )
    assert res_leap.format_status == FormatValidationStatus.FORMAT_VALID
    assert res_leap.derived_birth_date == "2000-02-29"

    # 1901 is NOT a leap year (Century 2, YY=01, MM=02, DD=29)
    res_non_leap = ocr_service.process_national_id(
        case_id="case-nonleap",
        raw_id_input="20102290101234",
        workflow_context=WorkflowContext.STRUCTURED_INTAKE,
    )
    assert res_non_leap.format_status == FormatValidationStatus.INVALID_DATE


def test_unmatched_governorate_triggers_human_review(client: TestClient):
    """Test invalid governorate code (e.g. 99) mandates human review."""
    payload = {
        "raw_national_id": "29505149901234",  # Gov code 99 is invalid
        "workflow_context": "STRUCTURED_INTAKE",
    }
    resp = client.post("/api/v1/ocr/validate-national-id", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["governorate_status"] == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED
    assert data["review_status"] == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW


def test_document_ai_dai02_compound_status():
    """Test DAI-02: Format and OCR pass, consistency unchecked -> PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED."""
    res = ocr_service.process_national_id(
        case_id="case-dai-02",
        raw_id_input="29505140101234",
        workflow_context=WorkflowContext.DOCUMENT_AI,
        document_profile="EGY_NID_FRONT_V1",
        ocr_confidence=0.95,
        comparison_id=None,  # No comparable field available
    )
    assert res.ocr_status == OCRExtractionStatus.OCR_SUCCESS
    assert res.compound_status == CompoundStatus.PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED
    assert res.review_status == ReviewRoutingStatus.NO_REVIEW_REQUIRED


def test_document_ai_low_confidence_forces_review():
    """Test DAI-07: OCR low confidence (<0.80) forces human review."""
    res = ocr_service.process_national_id(
        case_id="case-low-conf",
        raw_id_input="29505140101234",
        workflow_context=WorkflowContext.DOCUMENT_AI,
        document_profile="EGY_NID_FRONT_V1",
        ocr_confidence=0.65,  # Below 0.80 threshold
    )
    assert res.ocr_status == OCRExtractionStatus.OCR_LOW_CONFIDENCE
    assert res.compound_status == CompoundStatus.NONE
    assert res.review_status == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW


def test_unsupported_document_profile():
    """Test submission outside EGY_NID_FRONT_V1 emits DOCUMENT_PROFILE_UNSUPPORTED."""
    res = ocr_service.process_national_id(
        case_id="case-passport",
        raw_id_input="29505140101234",
        workflow_context=WorkflowContext.DOCUMENT_AI,
        document_profile="EGY_PASSPORT_V1",
    )
    assert res.ocr_status == OCRExtractionStatus.DOCUMENT_PROFILE_UNSUPPORTED
    assert res.review_status == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW


def test_disallowed_characters_rejected(client: TestClient):
    """Test alphabetic or symbol characters trigger NORMALIZATION_REJECTED."""
    payload = {
        "raw_national_id": "2950514010123A",  # Letter A
        "workflow_context": "STRUCTURED_INTAKE",
    }
    resp = client.post("/api/v1/ocr/validate-national-id", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["normalization_status"] == NormalizationStatus.NORMALIZATION_REJECTED
    assert data["masked_national_id"] == "****"
    assert data["review_status"] == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW


def test_identity_verification_permanent_invariant():
    """Verify identity_verification_status is ALWAYS NOT_VERIFIED across all tests."""
    res1 = ocr_service.process_national_id(
        case_id="inv-1",
        raw_id_input="29505140101234",
        workflow_context=WorkflowContext.DOCUMENT_AI,
        ocr_confidence=1.0,
    )
    assert res1.identity_verification_status == IdentityVerificationStatus.NOT_VERIFIED

    res2 = ocr_service.process_national_id(
        case_id="inv-2",
        raw_id_input="29505140101234",
        workflow_context=WorkflowContext.STRUCTURED_INTAKE,
    )
    assert res2.identity_verification_status == IdentityVerificationStatus.NOT_VERIFIED

