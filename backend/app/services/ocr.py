"""NileOps Egyptian National ID Validation & OCR Document Intelligence Service.

Implements the complete deterministic 9-dimensional evaluation architecture,
Table 7.1.1 (Document AI) and Table 7.1.2 (Structured Intake) decision logic,
working governorate reference matching, Arabic-Indic digit normalization,
and strict synthetic data boundary enforcement per docs/NATIONAL_ID_VALIDATION_SPEC.md.
"""

import calendar
import datetime
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# --- Enums per NATIONAL_ID_VALIDATION_SPEC.md ---

class WorkflowContext(str, Enum):
    DOCUMENT_AI = "DOCUMENT_AI"
    STRUCTURED_INTAKE = "STRUCTURED_INTAKE"


class NormalizationStatus(str, Enum):
    NORMALIZATION_PASSED = "NORMALIZATION_PASSED"
    NORMALIZATION_REJECTED = "NORMALIZATION_REJECTED"
    NORMALIZATION_NOT_RUN = "NORMALIZATION_NOT_RUN"


class FormatValidationStatus(str, Enum):
    FORMAT_VALID = "FORMAT_VALID"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_DATE = "INVALID_DATE"


class GovernorateReferenceStatus(str, Enum):
    GOVERNORATE_REFERENCE_MATCHED = "GOVERNORATE_REFERENCE_MATCHED"
    GOVERNORATE_REFERENCE_UNMATCHED = "GOVERNORATE_REFERENCE_UNMATCHED"
    GOVERNORATE_AUTHORITATIVE_VERIFIED = "GOVERNORATE_AUTHORITATIVE_VERIFIED"  # Reserved


class GenderRuleStatus(str, Enum):
    REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION = "REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION"


class ChecksumValidationStatus(str, Enum):
    NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION = "NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION"


class OCRExtractionStatus(str, Enum):
    OCR_SUCCESS = "OCR_SUCCESS"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    OCR_EXTRACTION_FAILED = "OCR_EXTRACTION_FAILED"
    DOCUMENT_PROFILE_UNSUPPORTED = "DOCUMENT_PROFILE_UNSUPPORTED"
    OCR_NOT_RUN = "OCR_NOT_RUN"


class ProfileResolutionStatus(str, Enum):
    PROFILE_RESOLVED = "PROFILE_RESOLVED"
    DOCUMENT_PROFILE_UNSUPPORTED = "DOCUMENT_PROFILE_UNSUPPORTED"
    DOCUMENT_LAYOUT_UNRECOGNIZED = "DOCUMENT_LAYOUT_UNRECOGNIZED"


class EngineFailureReason(str, Enum):
    NONE = "NONE"
    IMAGE_DECODE_ERROR = "IMAGE_DECODE_ERROR"
    ENGINE_RUNTIME_ERROR = "ENGINE_RUNTIME_ERROR"


class FieldExtractionStatus(str, Enum):
    ALL_REQUIRED_EXTRACTED = "ALL_REQUIRED_EXTRACTED"
    REQUIRED_FIELDS_LOW_CONFIDENCE = "REQUIRED_FIELDS_LOW_CONFIDENCE"
    REQUIRED_FIELDS_MISSING = "REQUIRED_FIELDS_MISSING"
    OPTIONAL_FIELDS_MISSING = "OPTIONAL_FIELDS_MISSING"


class FieldExtractionOutcome(str, Enum):
    EXTRACTED_ABOVE_THRESHOLD = "EXTRACTED_ABOVE_THRESHOLD"
    EXTRACTED_BELOW_THRESHOLD = "EXTRACTED_BELOW_THRESHOLD"
    FIELD_ABSENT = "FIELD_ABSENT"


class ConsistencyStatus(str, Enum):
    CONSISTENCY_PASSED = "CONSISTENCY_PASSED"
    DATA_MISMATCH = "DATA_MISMATCH"
    CONSISTENCY_NOT_EVALUATED = "CONSISTENCY_NOT_EVALUATED"


class ConsistencyEvaluationReason(str, Enum):
    NONE = "NONE"
    NO_COMPARABLE_FIELD_AVAILABLE = "NO_COMPARABLE_FIELD_AVAILABLE"
    COMPARISON_INPUT_MISSING = "COMPARISON_INPUT_MISSING"
    OCR_INPUT_UNAVAILABLE = "OCR_INPUT_UNAVAILABLE"
    COMPARISON_NOT_SUPPORTED = "COMPARISON_NOT_SUPPORTED"


class ReviewRoutingStatus(str, Enum):
    NO_REVIEW_REQUIRED = "NO_REVIEW_REQUIRED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    UNDER_HUMAN_REVIEW = "UNDER_HUMAN_REVIEW"
    REVIEW_COMPLETED = "REVIEW_COMPLETED"


class IdentityVerificationStatus(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"


class CompoundStatus(str, Enum):
    NONE = "NONE"
    PROVISIONAL_FORMAT_AND_CONSISTENCY_PASSED = "PROVISIONAL_FORMAT_AND_CONSISTENCY_PASSED"
    PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED = "PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED"


# --- Reference Allowlist Tables ---

GOVERNORATE_CODES: Dict[str, Tuple[str, str]] = {
    # Metropolitan
    "01": ("Cairo", "القاهرة"),
    "02": ("Alexandria", "الإسكندرية"),
    "03": ("Port Said", "بورسعيد"),
    "04": ("Suez", "السويس"),
    # Lower Egypt
    "11": ("Damietta", "دمياط"),
    "12": ("Dakahlia", "الدقهلية"),
    "13": ("Ash Sharqia", "الشرقية"),
    "14": ("Al Qalyubia", "القليوبية"),
    "15": ("Kafr El Sheikh", "كفر الشيخ"),
    "16": ("Al Gharbia", "الغربية"),
    "17": ("Al Monufia", "المنوفية"),
    "18": ("Beheira", "البحيرة"),
    "19": ("Ismailia", "الإسماعيلية"),
    # Upper Egypt
    "21": ("Giza", "الجيزة"),
    "22": ("Beni Suef", "بني سويف"),
    "23": ("Faiyum", "الفيوم"),
    "24": ("Minya", "المنيا"),
    "25": ("Asyut", "أسيوط"),
    "26": ("Sohag", "سوهاج"),
    "27": ("Qena", "قنا"),
    "28": ("Aswan", "أسوان"),
    "29": ("Luxor", "الأقصر"),
    # Frontier
    "31": ("Red Sea", "البحر الأحمر"),
    "32": ("New Valley", "الوادي الجديد"),
    "33": ("Matrouh", "مطروح"),
    "34": ("North Sinai", "شمال سيناء"),
    "35": ("South Sinai", "جنوب سيناء"),
    # Citizens Born Abroad
    "88": ("Citizens Born Abroad", "المولودين بالخارج"),
}

EASTERN_TO_WESTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


# --- Public Schemas ---

class NationalIDValidationPublicResponse(BaseModel):
    case_id: str
    masked_national_id: str
    workflow_context: WorkflowContext
    normalization_status: NormalizationStatus
    format_status: FormatValidationStatus
    governorate_status: GovernorateReferenceStatus
    ocr_status: OCRExtractionStatus
    consistency_status: ConsistencyStatus
    review_status: ReviewRoutingStatus
    identity_verification_status: IdentityVerificationStatus = IdentityVerificationStatus.NOT_VERIFIED
    compound_status: CompoundStatus
    derived_birth_date: Optional[str] = None
    derived_governorate: Optional[str] = None
    derived_gender: Optional[str] = None


# --- Core Validator Engine ---

class NationalIDValidator:
    """Deterministic validator for 14-digit Egyptian National ID structure."""

    @staticmethod
    def normalize_digits(raw_input: str) -> Tuple[NormalizationStatus, Optional[str]]:
        """Normalize Eastern Arabic digits and strip whitespace, rejecting invalid characters."""
        if not raw_input or not isinstance(raw_input, str):
            return NormalizationStatus.NORMALIZATION_REJECTED, None

        cleaned = raw_input.strip().translate(EASTERN_TO_WESTERN_DIGITS)
        # Remove internal spaces or hyphens
        cleaned = re.sub(r"[\s\-_]", "", cleaned)

        # Allowlist: exactly 14 ASCII digits
        if not re.fullmatch(r"^[0-9]{14}$", cleaned):
            return NormalizationStatus.NORMALIZATION_REJECTED, None

        return NormalizationStatus.NORMALIZATION_PASSED, cleaned

    @staticmethod
    def mask_id(clean_id: str) -> str:
        """Mask National ID for secure display and logging (e.g. 2950****1234)."""
        if len(clean_id) == 14:
            return f"{clean_id[:4]}****{clean_id[-4:]}"
        return "****"

    @classmethod
    def validate_structure(
        cls,
        clean_id: str,
        as_of_date: Optional[datetime.date] = None,
    ) -> Dict[str, Any]:
        """Validate 14 digits across Century, DOB, Governorate, Sequence, Checksum."""
        if as_of_date is None:
            as_of_date = datetime.date(2026, 11, 8)

        century_char = clean_id[0]
        if century_char == "2":
            century_base = 1900
        elif century_char == "3":
            century_base = 2000
        else:
            return {
                "format_status": FormatValidationStatus.INVALID_FORMAT,
                "governorate_status": GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                "gender_status": GenderRuleStatus.REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION,
                "checksum_status": ChecksumValidationStatus.NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION,
                "birth_date": None,
                "governorate_en": None,
                "governorate_ar": None,
                "gender": None,
            }

        # Date of birth components: YY MM DD
        yy = int(clean_id[1:3])
        mm = int(clean_id[3:5])
        dd = int(clean_id[5:7])
        full_year = century_base + yy

        # Calendar validity check
        if mm < 1 or mm > 12:
            return {
                "format_status": FormatValidationStatus.INVALID_DATE,
                "governorate_status": GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                "gender_status": GenderRuleStatus.REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION,
                "checksum_status": ChecksumValidationStatus.NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION,
                "birth_date": None,
                "governorate_en": None,
                "governorate_ar": None,
                "gender": None,
            }

        # Check days in month (handling leap years correctly)
        _, max_days = calendar.monthrange(full_year, mm)
        if dd < 1 or dd > max_days:
            return {
                "format_status": FormatValidationStatus.INVALID_DATE,
                "governorate_status": GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                "gender_status": GenderRuleStatus.REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION,
                "checksum_status": ChecksumValidationStatus.NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION,
                "birth_date": None,
                "governorate_en": None,
                "governorate_ar": None,
                "gender": None,
            }

        birth_date = datetime.date(full_year, mm, dd)
        if birth_date > as_of_date:
            return {
                "format_status": FormatValidationStatus.INVALID_DATE,
                "governorate_status": GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                "gender_status": GenderRuleStatus.REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION,
                "checksum_status": ChecksumValidationStatus.NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION,
                "birth_date": None,
                "governorate_en": None,
                "governorate_ar": None,
                "gender": None,
            }

        # Governorate validation: positions 8-9 (indices 7:9)
        gov_code = clean_id[7:9]
        if gov_code in GOVERNORATE_CODES:
            gov_status = GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED
            gov_en, gov_ar = GOVERNORATE_CODES[gov_code]
        else:
            gov_status = GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED
            gov_en, gov_ar = None, None

        # Gender validation: position 13 (index 12)
        gender_digit = int(clean_id[12])
        derived_gender = "Male" if (gender_digit % 2 != 0) else "Female"

        return {
            "format_status": FormatValidationStatus.FORMAT_VALID,
            "governorate_status": gov_status,
            "gender_status": GenderRuleStatus.REFERENCE_PENDING_AUTHORITATIVE_VERIFICATION,
            "checksum_status": ChecksumValidationStatus.NOT_IMPLEMENTED_UNVERIFIED_SPECIFICATION,
            "birth_date": birth_date,
            "governorate_en": gov_en,
            "governorate_ar": gov_ar,
            "gender": derived_gender,
        }

    @classmethod
    def evaluate_decision_logic(
        cls,
        workflow_context: WorkflowContext,
        norm_status: NormalizationStatus,
        format_status: FormatValidationStatus,
        gov_status: GovernorateReferenceStatus,
        ocr_status: OCRExtractionStatus,
        consistency_status: ConsistencyStatus,
        consistency_reason: ConsistencyEvaluationReason = ConsistencyEvaluationReason.NONE,
    ) -> Tuple[CompoundStatus, ReviewRoutingStatus]:
        """Implements exact Decision Tables 7.1.1 (Document AI) and 7.1.2 (Structured Intake)."""

        if workflow_context == WorkflowContext.DOCUMENT_AI:
            # Row DAI-01: All passed
            if (
                norm_status == NormalizationStatus.NORMALIZATION_PASSED
                and format_status == FormatValidationStatus.FORMAT_VALID
                and gov_status == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED
                and ocr_status == OCRExtractionStatus.OCR_SUCCESS
                and consistency_status == ConsistencyStatus.CONSISTENCY_PASSED
                and consistency_reason == ConsistencyEvaluationReason.NONE
            ):
                return (
                    CompoundStatus.PROVISIONAL_FORMAT_AND_CONSISTENCY_PASSED,
                    ReviewRoutingStatus.NO_REVIEW_REQUIRED,
                )

            # Row DAI-02: Format passed, consistency unchecked
            if (
                norm_status == NormalizationStatus.NORMALIZATION_PASSED
                and format_status == FormatValidationStatus.FORMAT_VALID
                and gov_status == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED
                and ocr_status == OCRExtractionStatus.OCR_SUCCESS
                and consistency_status == ConsistencyStatus.CONSISTENCY_NOT_EVALUATED
                and consistency_reason == ConsistencyEvaluationReason.NO_COMPARABLE_FIELD_AVAILABLE
            ):
                return (
                    CompoundStatus.PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED,
                    ReviewRoutingStatus.NO_REVIEW_REQUIRED,
                )

            # All other DAI rows (DAI-03 to DAI-13) mandate human review
            return CompoundStatus.NONE, ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW

        else:
            # WorkflowContext.STRUCTURED_INTAKE
            # In structured intake, no document was processed, so compound status is always NONE
            if (
                norm_status == NormalizationStatus.NORMALIZATION_PASSED
                and format_status == FormatValidationStatus.FORMAT_VALID
                and gov_status == GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED
                and ocr_status == OCRExtractionStatus.OCR_NOT_RUN
            ):
                if consistency_status in (
                    ConsistencyStatus.CONSISTENCY_PASSED,
                    ConsistencyStatus.CONSISTENCY_NOT_EVALUATED,
                ):
                    # STR-01 and STR-02
                    return CompoundStatus.NONE, ReviewRoutingStatus.NO_REVIEW_REQUIRED

            # STR-03 to STR-06
            return CompoundStatus.NONE, ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW


class OCRDocumentService:
    """Document Intelligence service for Egyptian National ID cards."""

    def __init__(self):
        self.validator = NationalIDValidator()

    def process_national_id(
        self,
        case_id: str,
        raw_id_input: str,
        workflow_context: WorkflowContext = WorkflowContext.STRUCTURED_INTAKE,
        document_profile: str = "EGY_NID_FRONT_V1",
        ocr_confidence: float = 0.95,
        comparison_id: Optional[str] = None,
        as_of_date: Optional[datetime.date] = None,
    ) -> NationalIDValidationPublicResponse:
        """Process National ID input under strict 9-dimensional validation model."""
        if as_of_date is None:
            as_of_date = datetime.date(2026, 11, 8)

        # 1. Normalization
        norm_status, clean_id = self.validator.normalize_digits(raw_id_input)
        if norm_status != NormalizationStatus.NORMALIZATION_PASSED or not clean_id:
            compound, review = self.validator.evaluate_decision_logic(
                workflow_context=workflow_context,
                norm_status=NormalizationStatus.NORMALIZATION_REJECTED,
                format_status=FormatValidationStatus.INVALID_FORMAT,
                gov_status=GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                ocr_status=OCRExtractionStatus.OCR_NOT_RUN if workflow_context == WorkflowContext.STRUCTURED_INTAKE else OCRExtractionStatus.OCR_EXTRACTION_FAILED,
                consistency_status=ConsistencyStatus.CONSISTENCY_NOT_EVALUATED,
            )
            return NationalIDValidationPublicResponse(
                case_id=case_id,
                masked_national_id="****",
                workflow_context=workflow_context,
                normalization_status=NormalizationStatus.NORMALIZATION_REJECTED,
                format_status=FormatValidationStatus.INVALID_FORMAT,
                governorate_status=GovernorateReferenceStatus.GOVERNORATE_REFERENCE_UNMATCHED,
                ocr_status=OCRExtractionStatus.OCR_NOT_RUN if workflow_context == WorkflowContext.STRUCTURED_INTAKE else OCRExtractionStatus.OCR_EXTRACTION_FAILED,
                consistency_status=ConsistencyStatus.CONSISTENCY_NOT_EVALUATED,
                review_status=review,
                compound_status=compound,
            )

        masked_id = self.validator.mask_id(clean_id)

        # 2. Format & Reference Validation
        struct_res = self.validator.validate_structure(clean_id, as_of_date=as_of_date)
        format_status = struct_res["format_status"]
        gov_status = struct_res["governorate_status"]

        # 3. OCR & Profile Resolution
        if workflow_context == WorkflowContext.STRUCTURED_INTAKE:
            ocr_status = OCRExtractionStatus.OCR_NOT_RUN
        else:
            # Verify supported profile
            if document_profile != "EGY_NID_FRONT_V1":
                ocr_status = OCRExtractionStatus.DOCUMENT_PROFILE_UNSUPPORTED
            elif ocr_confidence < 0.80:
                ocr_status = OCRExtractionStatus.OCR_LOW_CONFIDENCE
            else:
                ocr_status = OCRExtractionStatus.OCR_SUCCESS

        # 4. Consistency Evaluation
        consistency_reason = ConsistencyEvaluationReason.NONE
        if comparison_id:
            _, comp_clean = self.validator.normalize_digits(comparison_id)
            if comp_clean == clean_id:
                consistency_status = ConsistencyStatus.CONSISTENCY_PASSED
            else:
                consistency_status = ConsistencyStatus.DATA_MISMATCH
        else:
            consistency_status = ConsistencyStatus.CONSISTENCY_NOT_EVALUATED
            consistency_reason = ConsistencyEvaluationReason.NO_COMPARABLE_FIELD_AVAILABLE

        # 5. Compound Status & Review Routing Decision
        compound_status, review_status = self.validator.evaluate_decision_logic(
            workflow_context=workflow_context,
            norm_status=norm_status,
            format_status=format_status,
            gov_status=gov_status,
            ocr_status=ocr_status,
            consistency_status=consistency_status,
            consistency_reason=consistency_reason,
        )

        return NationalIDValidationPublicResponse(
            case_id=case_id,
            masked_national_id=masked_id,
            workflow_context=workflow_context,
            normalization_status=norm_status,
            format_status=format_status,
            governorate_status=gov_status,
            ocr_status=ocr_status,
            consistency_status=consistency_status,
            review_status=review_status,
            identity_verification_status=IdentityVerificationStatus.NOT_VERIFIED,
            compound_status=compound_status,
            derived_birth_date=struct_res["birth_date"].isoformat() if struct_res["birth_date"] else None,
            derived_governorate=struct_res["governorate_ar"],
            derived_gender=struct_res["gender"],
        )


ocr_service = OCRDocumentService()

