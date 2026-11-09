"""Targeted Deep OCR Testing Script for NileOps.

Tests Eastern/Western Arabic digits, leap-year boundary math, governorate allowlists,
decision tables 7.1.1 and 7.1.2, and permanent identity invariants.
Strictly synthetic data only.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.ocr import (
    ocr_service,
    WorkflowContext,
    NormalizationStatus,
    FormatValidationStatus,
    GovernorateReferenceStatus,
    OCRExtractionStatus,
    ReviewRoutingStatus,
    IdentityVerificationStatus,
    CompoundStatus,
)

def test_ocr_deep_scenarios():
    print("=== Testing Real OCR & National ID Scenarios ===")

    # Scenario 1: Western Arabic Digits (Valid Cairo Male, Born 1995-05-14)
    r1 = ocr_service.process_national_id("case-w1", "29505140101234", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 1 - Western Digits Valid]")
    print(f"  Masked: {r1.masked_national_id}, Format: {r1.format_status.value}, Gov: {r1.derived_governorate}, Gender: {r1.derived_gender}, Review: {r1.review_status.value}")
    assert r1.format_status == FormatValidationStatus.FORMAT_VALID
    assert r1.derived_governorate == "القاهرة"
    assert r1.derived_gender == "Male"
    assert r1.review_status == ReviewRoutingStatus.NO_REVIEW_REQUIRED

    # Scenario 2: Eastern Arabic-Indic Digits (٢٩٥٠٥١٤٠١٠١٢٣٤)
    r2 = ocr_service.process_national_id("case-e1", "٢٩٥٠٥١٤٠١٠١٢٣٤", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 2 - Eastern Arabic Normalization]")
    print(f"  Norm: {r2.normalization_status.value}, Masked: {r2.masked_national_id}, DOB: {r2.derived_birth_date}")
    assert r2.normalization_status == NormalizationStatus.NORMALIZATION_PASSED
    assert r2.masked_national_id == "2950****1234"
    assert r2.derived_birth_date == "1995-05-14"

    # Scenario 3: Leap Year Boundary Validation (Feb 29)
    # A. 2000 is a valid leap year (Century 3, YY=00, MM=02, DD=29)
    r3_valid = ocr_service.process_national_id("case-leap-val", "30002290101234", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 3A - Leap Year Feb 29 (Year 2000 - Valid)]")
    print(f"  Format: {r3_valid.format_status.value}, DOB: {r3_valid.derived_birth_date}")
    assert r3_valid.format_status == FormatValidationStatus.FORMAT_VALID
    assert r3_valid.derived_birth_date == "2000-02-29"

    # B. 1901 is NOT a leap year (Century 2, YY=01, MM=02, DD=29)
    r3_inv = ocr_service.process_national_id("case-leap-inv", "20102290101234", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 3B - Non-Leap Year Feb 29 (Year 1901 - Invalid Date)]")
    print(f"  Format: {r3_inv.format_status.value}, DOB: {r3_inv.derived_birth_date}")
    assert r3_inv.format_status == FormatValidationStatus.INVALID_DATE

    # Scenario 4: Date of Birth in the Future (relative to as_of_date)
    # Born 2028-01-01 when as_of_date is 2026-11-08 -> INVALID_DATE
    r4_future = ocr_service.process_national_id("case-future", "32801010101234", WorkflowContext.STRUCTURED_INTAKE, as_of_date=datetime.date(2026, 11, 8))
    print("\n[Scenario 4 - Future Birth Date]")
    print(f"  Format: {r4_future.format_status.value}")
    assert r4_future.format_status == FormatValidationStatus.INVALID_DATE

    # Scenario 5: Invalid Governorate Code (99)
    r5_gov = ocr_service.process_national_id("case-bad-gov", "29505149901234", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 5 - Invalid Governorate Code (99)]")
    print(f"  Gov Status: {r5_gov.governorate_status.value}, Review: {r5_gov.review_status.value}")
    assert r5_gov.governorate_status == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED
    assert r5_gov.review_status == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW

    # Scenario 6: Table 7.1.1 Document AI Workflow (DAI-01 & DAI-02)
    # DAI-02: Format valid + high confidence OCR + no comparable input -> PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED
    r6_dai2 = ocr_service.process_national_id("case-dai2", "29505140101234", WorkflowContext.DOCUMENT_AI, ocr_confidence=0.96)
    print("\n[Scenario 6 - Document AI Workflow DAI-02]")
    print(f"  Compound: {r6_dai2.compound_status.value}, Review: {r6_dai2.review_status.value}")
    assert r6_dai2.compound_status == CompoundStatus.PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED
    assert r6_dai2.review_status == ReviewRoutingStatus.NO_REVIEW_REQUIRED

    # Scenario 7: Low OCR Confidence (< 0.80) -> DAI-07 (Review Required)
    r7_low = ocr_service.process_national_id("case-low", "29505140101234", WorkflowContext.DOCUMENT_AI, ocr_confidence=0.68)
    print("\n[Scenario 7 - Low OCR Confidence (<0.80)]")
    print(f"  OCR Status: {r7_low.ocr_status.value}, Review: {r7_low.review_status.value}")
    assert r7_low.ocr_status == OCRExtractionStatus.OCR_LOW_CONFIDENCE
    assert r7_low.review_status == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW

    # Scenario 8: Unsupported Document Profile (e.g. Passport)
    r8_prof = ocr_service.process_national_id("case-prof", "29505140101234", WorkflowContext.DOCUMENT_AI, document_profile="EGY_PASSPORT_V1")
    print("\n[Scenario 8 - Unsupported Document Profile]")
    print(f"  OCR Status: {r8_prof.ocr_status.value}, Review: {r8_prof.review_status.value}")
    assert r8_prof.ocr_status == OCRExtractionStatus.DOCUMENT_PROFILE_UNSUPPORTED
    assert r8_prof.review_status == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW

    # Scenario 9: Disallowed Characters (e.g. 2950514010123A)
    r9_dis = ocr_service.process_national_id("case-dis", "2950514010123A", WorkflowContext.STRUCTURED_INTAKE)
    print("\n[Scenario 9 - Disallowed Alphabetical Characters]")
    print(f"  Norm: {r9_dis.normalization_status.value}, Masked: {r9_dis.masked_national_id}")
    assert r9_dis.normalization_status == NormalizationStatus.NORMALIZATION_REJECTED
    assert r9_dis.masked_national_id == "****"

    # Scenario 10: Permanent Identity Boundary Invariant
    print("\n[Scenario 10 - Identity Verification Permanent Invariant]")
    print(f"  Identity Verification Status: {r1.identity_verification_status.value}")
    assert r1.identity_verification_status == IdentityVerificationStatus.NOT_VERIFIED
    assert r6_dai2.identity_verification_status == IdentityVerificationStatus.NOT_VERIFIED

    print("\n=== All OCR deep test scenarios verified successfully! ===")

if __name__ == "__main__":
    test_ocr_deep_scenarios()

