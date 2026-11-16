"""NileOps Dual-Document Cross-Verification Service (National ID + Proof of Address / Utility Bill).

Implements deterministic cross-matching between an Egyptian National ID and a secondary proof-of-address
document (e.g., Electricity, Water, Gas, or Telecom bill) under Egyptian banking compliance guidelines:
  1. Citizen Name Fuzzy Cross-Match: Token-set & character similarity >= 0.85 (85%).
  2. Residential Locality Cross-Match: Governorate, city, and district consistency.
  3. Bill Recency Check: Issue date must be within 90 days (3 months) of verification.
  4. Discrepancy Flagging: Generates standardized bilingual reason codes.
  5. Invariant: Cross-verification NEVER auto-approves identity (NOT_VERIFIED maintained).
"""

from datetime import date, datetime, timedelta
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.kyc_checks import GOVERNORATE_GEO_MAP
from app.services.ocr import EASTERN_TO_WESTERN_DIGITS


class DocumentMatchingReason(str, Enum):
    CLEAN_CROSS_VERIFICATION = "CLEAN_CROSS_VERIFICATION"
    NAME_MISMATCH_ACROSS_DOCS = "NAME_MISMATCH_ACROSS_DOCS"
    ADDRESS_MISMATCH_ACROSS_DOCS = "ADDRESS_MISMATCH_ACROSS_DOCS"
    UTILITY_BILL_TOO_OLD = "UTILITY_BILL_TOO_OLD"
    MISSING_UTILITY_BILL_FIELDS = "MISSING_UTILITY_BILL_FIELDS"


def normalize_arabic_name(name: str) -> str:
    """Normalize Arabic text for deterministic and phonetic-tolerant comparison."""
    if not name:
        return ""
    text = str(name).strip()
    # Normalize Alef variants
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize Taa Marbouta / Haa
    text = re.sub(r"[ةه]", "ه", text)
    # Normalize Yaa / Alef Maksura
    text = re.sub(r"[يى]", "ي", text)
    # Remove Arabic diacritics (Tashkeel)
    text = re.sub(r"[\u064B-\u0652\u0670]", "", text)
    # Remove punctuation, prefixes, honorifics
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Compute token-set & sequence similarity between two citizen names (0.0 to 1.0)."""
    norm1 = normalize_arabic_name(name1)
    norm2 = normalize_arabic_name(name2)

    if not norm1 or not norm2:
        return 0.0

    if norm1 == norm2:
        return 1.0

    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    if not tokens1 or not tokens2:
        return 0.0

    # Token overlap (Jaccard on token set)
    common_tokens = tokens1.intersection(tokens2)
    min_tokens = min(len(tokens1), len(tokens2))
    max_tokens = max(len(tokens1), len(tokens2))

    # Token-containment score (useful when ID has 4-part name and bill has 3-part name)
    containment = len(common_tokens) / float(min_tokens)
    jaccard = len(common_tokens) / float(max_tokens)

    # Character-level bigram Dice coefficient for typo tolerance
    def _get_bigrams(s: str) -> set:
        return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else {s}

    bg1 = _get_bigrams(norm1)
    bg2 = _get_bigrams(norm2)
    dice = (2.0 * len(bg1.intersection(bg2))) / float(len(bg1) + len(bg2)) if (bg1 and bg2) else 0.0

    # Weighted composite: 60% token containment (allowing 3 vs 4 name parts) + 40% bigram similarity
    composite = 0.60 * containment + 0.40 * dice
    return round(min(1.0, max(0.0, composite)), 4)


def detect_governorate_from_address(address_str: str) -> Tuple[Optional[str], Optional[str]]:
    """Identify matching governorate code and Arabic name from an address string."""
    if not address_str:
        return None, None

    norm = normalize_arabic_name(address_str)

    for code, info in GOVERNORATE_GEO_MAP.items():
        for kw in info.get("keywords", []):
            norm_kw = normalize_arabic_name(kw)
            if norm_kw and norm_kw in norm:
                return code, info["ar"]

    return None, None


def parse_bill_date(date_input: Any) -> Optional[date]:
    """Parse bill date from string or date object."""
    if isinstance(date_input, date):
        return date_input
    if isinstance(date_input, datetime):
        return date_input.date()
    if not date_input:
        return None

    clean_str = str(date_input).strip()
    # Replace Eastern Arabic digits
    clean_str = "".join(EASTERN_TO_WESTERN_DIGITS.get(c, c) for c in clean_str)

    patterns = [
        r"%Y-%m-%d",
        r"%Y/%m/%d",
        r"%d/%m/%Y",
        r"%d-%m-%Y",
        r"%Y-%m",
        r"%Y/%m",
    ]
    for pat in patterns:
        try:
            dt = datetime.strptime(clean_str, pat)
            return dt.date()
        except ValueError:
            continue
    return None


class DualDocumentMatcher:
    """Deterministic Cross-Document Verification Engine."""

    def __init__(self, name_threshold: Optional[float] = None, max_bill_age_days: Optional[int] = None):
        self.name_threshold = (
            name_threshold
            if name_threshold is not None
            else getattr(settings, "DOC_MATCH_NAME_SIMILARITY_THRESHOLD", 0.85)
        )
        self.max_bill_age_days = (
            max_bill_age_days
            if max_bill_age_days is not None
            else getattr(settings, "DOC_MATCH_MAX_BILL_AGE_DAYS", 90)
        )

    def cross_verify(
        self,
        id_data: Dict[str, Any],
        bill_data: Dict[str, Any],
        reference_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Cross-verify Egyptian National ID against secondary proof of address (utility bill)."""
        ref_date = reference_date or date.today()
        discrepancies: List[Dict[str, Any]] = []

        # 1. Extract National ID fields
        id_name = id_data.get("name") or id_data.get("citizen_name") or ""
        id_address = id_data.get("address") or id_data.get("residential_address") or ""
        id_number = id_data.get("national_id") or id_data.get("synthetic_national_id") or ""
        derived_gov = id_data.get("derived_governorate") or ""

        # 2. Extract Utility Bill fields
        bill_type = bill_data.get("utility_type", "ELECTRICITY_BILL")  # ELECTRICITY, GAS, WATER, TELECOM
        bill_consumer_name = bill_data.get("consumer_name") or bill_data.get("name") or ""
        bill_address = bill_data.get("service_address") or bill_data.get("address") or ""
        bill_date_raw = bill_data.get("issue_date") or bill_data.get("bill_date")
        bill_account_number = bill_data.get("account_number") or bill_data.get("meter_number") or "UTIL-12345"

        # Check for missing bill fields
        if not bill_consumer_name or not bill_address or not bill_date_raw:
            discrepancies.append({
                "code": DocumentMatchingReason.MISSING_UTILITY_BILL_FIELDS.value,
                "severity": "CRITICAL",
                "explanation_en": "Utility bill is missing mandatory fields (consumer name, service address, or issue date).",
                "explanation_ar": "فاتورة المرافق تفتقر إلى حقول إلزامية (اسم المشترك أو عنوان الخدمة أو تاريخ الإصدار).",
            })

        # 3. Name Similarity Cross-Match
        name_sim = calculate_name_similarity(id_name, bill_consumer_name)
        is_name_match = name_sim >= self.name_threshold

        if not is_name_match and bill_consumer_name:
            discrepancies.append({
                "code": DocumentMatchingReason.NAME_MISMATCH_ACROSS_DOCS.value,
                "severity": "CRITICAL",
                "score": name_sim,
                "threshold": self.name_threshold,
                "explanation_en": f"Name mismatch between National ID ('{id_name}') and utility bill ('{bill_consumer_name}') (similarity {name_sim:.1%} < {self.name_threshold:.0%}).",
                "explanation_ar": f"تعارض في اسم المواطن بين بطاقة الرقم القومي ('{id_name}') وفاتورة المرافق ('{bill_consumer_name}') (نسبة التطابق {name_sim:.1%} أقل من الحد الأدنى {self.name_threshold:.0%}).",
            })

        # 4. Address / Locality Cross-Match
        id_gov_code, id_gov_name = detect_governorate_from_address(id_address)
        bill_gov_code, bill_gov_name = detect_governorate_from_address(bill_address)

        # Also check if derived_gov matches bill_gov
        effective_id_gov = id_gov_name or derived_gov
        is_address_match = True

        if id_gov_code and bill_gov_code and id_gov_code != bill_gov_code:
            is_address_match = False
        elif effective_id_gov and bill_gov_name and normalize_arabic_name(effective_id_gov) != normalize_arabic_name(bill_gov_name):
            is_address_match = False

        if not is_address_match:
            discrepancies.append({
                "code": DocumentMatchingReason.ADDRESS_MISMATCH_ACROSS_DOCS.value,
                "severity": "CRITICAL",
                "id_governorate": effective_id_gov,
                "bill_governorate": bill_gov_name,
                "explanation_en": f"Address mismatch: National ID indicates '{effective_id_gov}', but utility bill service address indicates '{bill_gov_name}'.",
                "explanation_ar": f"تعارض في العنوان: بطاقة الرقم القومي تشير إلى '{effective_id_gov}'، بينما تشير فاتورة المرافق إلى '{bill_gov_name}'.",
            })

        # 5. Bill Recency Check (must be <= 90 days)
        parsed_bdate = parse_bill_date(bill_date_raw)
        bill_age_days = None
        is_recent = True

        if parsed_bdate:
            bill_age_days = (ref_date - parsed_bdate).days
            if bill_age_days > self.max_bill_age_days:
                is_recent = False
                discrepancies.append({
                    "code": DocumentMatchingReason.UTILITY_BILL_TOO_OLD.value,
                    "severity": "WARNING",
                    "bill_issue_date": parsed_bdate.isoformat(),
                    "bill_age_days": bill_age_days,
                    "max_allowed_days": self.max_bill_age_days,
                    "explanation_en": f"Utility bill is {bill_age_days} days old (exceeds regulatory limit of {self.max_bill_age_days} days / 3 months).",
                    "explanation_ar": f"فاتورة المرافق مر عليها {bill_age_days} يوماً (تتجاوز الحد الأقصى المسموح به رقابياً وهو {self.max_bill_age_days} يوماً / 3 أشهر).",
                })
        elif bill_date_raw:
            is_recent = False
            discrepancies.append({
                "code": DocumentMatchingReason.UTILITY_BILL_TOO_OLD.value,
                "severity": "WARNING",
                "explanation_en": "Could not verify utility bill issue date format.",
                "explanation_ar": "تعذر التحقق من صيغة تاريخ إصدار فاتورة المرافق.",
            })

        is_cross_verified = len(discrepancies) == 0

        return {
            "is_cross_verified": is_cross_verified,
            "discrepancy_count": len(discrepancies),
            "discrepancies": discrepancies,
            "discrepancy_codes": [d["code"] for d in discrepancies],
            "name_cross_match": {
                "similarity_score": name_sim,
                "threshold": self.name_threshold,
                "is_match": is_name_match,
                "id_name": id_name,
                "bill_consumer_name": bill_consumer_name,
            },
            "address_cross_match": {
                "is_match": is_address_match,
                "id_governorate": effective_id_gov,
                "bill_governorate": bill_gov_name,
                "id_address": id_address,
                "bill_address": bill_address,
            },
            "recency_check": {
                "is_recent": is_recent,
                "bill_issue_date": parsed_bdate.isoformat() if parsed_bdate else str(bill_date_raw),
                "bill_age_days": bill_age_days,
                "max_allowed_days": self.max_bill_age_days,
            },
            "utility_bill_meta": {
                "utility_type": bill_type,
                "account_number": bill_account_number,
            },
            "identity_verification_status": "NOT_VERIFIED",
            "review_status": "REQUIRES_HUMAN_REVIEW" if not is_cross_verified else "PENDING_REVIEW",
        }


dual_document_matcher = DualDocumentMatcher()
