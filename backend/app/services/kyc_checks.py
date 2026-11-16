"""NileOps KYC Cross-Field Mismatch & Quality Exception Detection Service.

Implements deterministic cross-field validation rules according to the NileOps Handbook:
  (a) Birth date derived from National ID vs extracted/provided birth date
  (b) Governorate derived from National ID vs location in extracted residential address
  (c) Missing critical fields (National ID, citizen name, residential address)
  (d) Low OCR engine confidence below configurable per-field thresholds
  (e) Invalid National ID structural rules (Century, calendar date, leap year, governorate reference)

Every check produces a standardized reason code, severity, and bilingual human-readable explanation (EN + AR).
Any triggered check routes the case to human compliance review with stored reasons.
Never auto-approves; NOT_VERIFIED status is maintained at all times.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.ocr import (
    FormatValidationStatus,
    GovernorateReferenceStatus,
    NationalIDValidator,
    GOVERNORATE_CODES,
    EASTERN_TO_WESTERN_DIGITS,
)


class KycReasonCode(str, Enum):
    BIRTH_DATE_MISMATCH = "BIRTH_DATE_MISMATCH"
    GOVERNORATE_MISMATCH = "GOVERNORATE_MISMATCH"
    MISSING_FIELD_NATIONAL_ID = "MISSING_FIELD_NATIONAL_ID"
    MISSING_FIELD_NAME = "MISSING_FIELD_NAME"
    MISSING_FIELD_ADDRESS = "MISSING_FIELD_ADDRESS"
    LOW_OCR_CONFIDENCE = "LOW_OCR_CONFIDENCE"
    INVALID_ID_STRUCTURE = "INVALID_ID_STRUCTURE"


class KycSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


# Default confidence thresholds per field
DEFAULT_CONFIDENCE_THRESHOLDS = {
    "national_id": 0.85,
    "name": 0.70,
    "address": 0.70,
    "factory_code": 0.70,
}

# Mapping of governorate code to primary Arabic names and key district/city keywords
GOVERNORATE_GEO_MAP: Dict[str, Dict[str, Any]] = {
    "01": {
        "en": "Cairo",
        "ar": "القاهرة",
        "keywords": [
            "القاهرة", "القاهره", "مدينة نصر", "المعادي", "المعادى", "شبرا", "حلوان",
            "المطرية", "المطريه", "عين شمس", "الزيتون", "مصر الجديدة", "السيدة زينب",
            "قصر العيني", "الوايلي", "الوايلى", "الزمالك", "التبين", "بدر", "الشروق",
            "التجمع", "العبور", "المقطم", "روض الفرج", "المرج", "الظاهر", "الأزبكية"
        ],
    },
    "02": {
        "en": "Alexandria",
        "ar": "الإسكندرية",
        "keywords": [
            "الإسكندرية", "الاسكندرية", "الاسكندريه", "الإسكندريه", "سيدي جابر", "ميامي",
            "سموحة", "سموحه", "الرمل", "المنتزه", "محرم بك", "العطارين", "الدخيلة",
            "برج العرب", "العجمي", "كرموز", "كوم الدكة", "ستانلي", "جليم"
        ],
    },
    "03": {
        "en": "Port Said",
        "ar": "بورسعيد",
        "keywords": ["بورسعيد", "بور سعيد", "بورفؤاد", "بور فؤاد", "الزهور", "الضواحي"],
    },
    "04": {
        "en": "Suez",
        "ar": "السويس",
        "keywords": ["السويس", "الأربعين", "الاربعين", "عتاقة", "عتاقه", "الجناين", "فيصل السويس"],
    },
    "11": {
        "en": "Damietta",
        "ar": "دمياط",
        "keywords": ["دمياط", "رأس البر", "فارسكور", "الزرقا", "كفر سعد", "كفر البطيخ"],
    },
    "12": {
        "en": "Dakahlia",
        "ar": "الدقهلية",
        "keywords": [
            "الدقهلية", "الدقهليه", "المنصورة", "المنصوره", "ميت غمر", "السنبلاوين",
            "بلقاس", "دكرنس", "شربين", "أجا", "طلخا", "منية النصر", "بني عبيد"
        ],
    },
    "13": {
        "en": "Ash Sharqia",
        "ar": "الشرقية",
        "keywords": [
            "الشرقية", "الشرقيه", "الزقازيق", "العاشر من رمضان", "بلبيس", "فاقوس",
            "أبو حماد", "ابو حماد", "منيا القمح", "أبو كبير", "ههيا", "كفر صقر", "ديرب نجم"
        ],
    },
    "14": {
        "en": "Al Qalyubia",
        "ar": "القليوبية",
        "keywords": [
            "القليوبية", "القليوبيه", "بنها", "شبرا الخيمة", "شبرا الخيمه", "قليوب",
            "طوخ", "الخانكة", "الخانكه", "القناطر الخيرية", "كفر شكر", "شبين القناطر"
        ],
    },
    "15": {
        "en": "Kafr El Sheikh",
        "ar": "كفر الشيخ",
        "keywords": ["كفر الشيخ", "دسوق", "فوه", "مطوبس", "بيلا", "سيدي سالم", "الحامول", "بلطيم"],
    },
    "16": {
        "en": "Al Gharbia",
        "ar": "الغربية",
        "keywords": [
            "الغربية", "الغربيه", "طنطا", "المحلة الكبرى", "المحله", "زفتى", "زفتي",
            "كفر الزيات", "بسيون", "سمنود", "قطور", "السنطة"
        ],
    },
    "17": {
        "en": "Al Monufia",
        "ar": "المنوفية",
        "keywords": [
            "المنوفية", "المنوفيه", "شبين الكوم", "منوف", "أشمون", "اشمون", "قويسنا",
            "بركة السبع", "تلا", "الشهداء", "السادات", "مدينة السادات"
        ],
    },
    "18": {
        "en": "Al Beheira",
        "ar": "البحيرة",
        "keywords": [
            "البحيرة", "البحيره", "دمنهور", "كفر الدوار", "إيتاي البارود", "ايتاي البارود",
            "أبو حمص", "ابو حمص", "حوش عيسى", "رشيد", "كوم حمادة", "الدلنجات", "وادي النطرون"
        ],
    },
    "19": {
        "en": "Ismailia",
        "ar": "الإسماعيلية",
        "keywords": ["الإسماعيلية", "الاسماعيلية", "الاسماعيليه", "فايد", "القنطرة", "التل الكبير", "أبو صوير"],
    },
    "21": {
        "en": "Giza",
        "ar": "الجيزة",
        "keywords": [
            "الجيزة", "الجيزه", "الدقي", "الدقى", "المهندسين", "الهرم", "فيصل",
            "العجوزة", "العجوزه", "أكتوبر", "اكتوبر", "الشيخ زايد", "الوراق",
            "العمرانية", "العمرانيه", "البدرشين", "الصف", "العياط", "أوسيم", "اوسيم",
            "الحوامدية", "أطفيح", "كرداسة", "بولاق الدكرور", "إمبابة", "امبابة"
        ],
    },
    "22": {
        "en": "Beni Suef",
        "ar": "بني سويف",
        "keywords": ["بني سويف", "بنى سويف", "الواسطى", "الواسطي", "ناصر", "ببا", "الفشن", "إهناسيا", "سمسطا"],
    },
    "23": {
        "en": "Faiyum",
        "ar": "الفيوم",
        "keywords": ["الفيوم", "إطسا", "اطسا", "طامية", "طاميه", "سنورس", "أبشواي", "يوسف الصديق"],
    },
    "24": {
        "en": "Minya",
        "ar": "المنيا",
        "keywords": ["المنيا", "ملوي", "مغاغة", "مغاغه", "بني مزار", "سمالوط", "أبو قرقاص", "مطاي", "دير مواس"],
    },
    "25": {
        "en": "Asyut",
        "ar": "أسيوط",
        "keywords": ["أسيوط", "اسيوط", "ديروط", "القوصية", "منفلوط", "أبنوب", "صدفا", "الغنايم", "البداري"],
    },
    "26": {
        "en": "Sohag",
        "ar": "سوهاج",
        "keywords": ["سوهاج", "البلينا", "طما", "طهطا", "المراغة", "المراغه", "جرجا", "المنشأة", "أخميم", "ساقلتة", "دار السلام سوهاج"],
    },
    "27": {
        "en": "Qena",
        "ar": "قنا",
        "keywords": ["قنا", "نجع حمادي", "دشنا", "قوص", "أبو تشت", "ابو تشت", "فارشوط", "نقادة", "الوقف"],
    },
    "28": {
        "en": "Aswan",
        "ar": "أسوان",
        "keywords": ["أسوان", "اسوان", "كوم أمبو", "كوم امبو", "إدفو", "ادفو", "نصر النوبة", "دراو", "أبو سمبل"],
    },
    "29": {
        "en": "Luxor",
        "ar": "الأقصر",
        "keywords": ["الأقصر", "الاقصر", "إسنا", "اسنا", "أرمنت", "ارمنت", "الطود", "القرنة", "البياضية"],
    },
    "31": {
        "en": "Red Sea",
        "ar": "البحر الأحمر",
        "keywords": ["البحر الأحمر", "البحر الاحمر", "الغردقة", "الغردقه", "سفاجا", "رأس غارب", "القصير", "مرسى علم", "شلاتين", "حلايب"],
    },
    "32": {
        "en": "New Valley",
        "ar": "الوادي الجديد",
        "keywords": ["الوادي الجديد", "الوادى الجديد", "الخارجة", "الداخلة", "الفرافرة", "باريس"],
    },
    "33": {
        "en": "Matrouh",
        "ar": "مطروح",
        "keywords": ["مطروح", "مرسى مطروح", "العلمين", "سيوة", "سيوه", "الحمام", "الضبعة", "سيدي براني", "السلوم"],
    },
    "34": {
        "en": "North Sinai",
        "ar": "شمال سيناء",
        "keywords": ["شمال سيناء", "العريش", "الشيخ زويد", "رفح", "بئر العبد", "الحسنة", "نخل"],
    },
    "35": {
        "en": "South Sinai",
        "ar": "جنوب سيناء",
        "keywords": ["جنوب سيناء", "شرم الشيخ", "طور سيناء", "دهب", "نويبع", "طابا", "رأس سدر", "سانت كاترين"],
    },
}

NAME_TO_CODE = {}
for code, data in GOVERNORATE_GEO_MAP.items():
    NAME_TO_CODE[data["ar"]] = code
    for kw in data["keywords"]:
        if kw not in NAME_TO_CODE:
            NAME_TO_CODE[kw] = code


def normalize_arabic_text(text: str) -> str:
    """Strip diacritics and normalize Arabic letter variants for robust matching."""
    if not text:
        return ""
    t = re.sub(r"[\u064B-\u0652\u0640]", "", text)
    t = re.sub(r"[إأآٱ]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"ى", "ي", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def detect_address_governorates(address_text: str) -> List[Tuple[str, str]]:
    """Scan extracted address text and return list of matched (gov_code, matched_keyword)."""
    if not address_text:
        return []

    norm_addr = normalize_arabic_text(address_text)
    matches = []

    for code, info in GOVERNORATE_GEO_MAP.items():
        for kw in info["keywords"]:
            norm_kw = normalize_arabic_text(kw)
            pattern = r"(?<!\w)" + re.escape(norm_kw) + r"(?!\w)"
            if re.search(pattern, norm_addr):
                matches.append((code, kw))
                break

    return matches


class KycCheckService:
    """Deterministic KYC Cross-Field and Quality Validation Engine."""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = dict(DEFAULT_CONFIDENCE_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)

    def evaluate_case(
        self,
        extracted_fields: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate deterministic cross-field checks and quality metrics on extracted document data."""
        reasons: List[Dict[str, Any]] = []

        sub_fields = extracted_fields.get("extracted_fields", {}) if isinstance(extracted_fields.get("extracted_fields"), dict) else {}

        raw_nid = (
            extracted_fields.get("national_id")
            or extracted_fields.get("raw_national_id")
            or extracted_fields.get("synthetic_national_id")
            or sub_fields.get("national_id")
        )
        nid_extracted = extracted_fields.get("national_id_extracted", sub_fields.get("national_id_extracted"))
        masked_nid = extracted_fields.get("masked_national_id")

        nid_conf = float(
            extracted_fields.get("national_id_conf")
            or extracted_fields.get("national_id_confidence")
            or sub_fields.get("national_id_confidence")
            or 0.0
        )

        citizen_name = (
            extracted_fields.get("name")
            or sub_fields.get("name")
        )
        name_extracted = extracted_fields.get("name_extracted", sub_fields.get("name_extracted"))
        name_conf = float(
            extracted_fields.get("name_conf")
            or extracted_fields.get("name_confidence")
            or sub_fields.get("name_confidence")
            or 0.0
        )

        address = (
            extracted_fields.get("address")
            or sub_fields.get("address")
        )
        address_extracted = extracted_fields.get("address_extracted", sub_fields.get("address_extracted"))
        address_conf = float(
            extracted_fields.get("address_conf")
            or extracted_fields.get("address_confidence")
            or sub_fields.get("address_confidence")
            or 0.0
        )

        pipeline_format_status = str(extracted_fields.get("format_status", ""))
        pipeline_gov_status = str(extracted_fields.get("governorate_status", ""))
        pipeline_ocr_status = str(extracted_fields.get("ocr_status", ""))
        derived_dob = extracted_fields.get("derived_birth_date")
        derived_gov_ar = extracted_fields.get("derived_governorate")

        # -------------------------------------------------------------
        # Check (c): Missing Critical Fields
        # -------------------------------------------------------------
        # 1. Missing National ID
        has_nid = (nid_extracted is True) or (raw_nid and str(raw_nid).strip() not in ("****", "None", "")) or (masked_nid and masked_nid != "****")
        if not has_nid or "OCR_EXTRACTION_FAILED" in pipeline_ocr_status:
            reasons.append({
                "code": KycReasonCode.MISSING_FIELD_NATIONAL_ID.value,
                "severity": KycSeverity.CRITICAL.value,
                "field": "national_id",
                "explanation_en": "National ID number could not be extracted from document scan.",
                "explanation_ar": "تعذر استخراج رقم بطاقة الرقم القومي من المسح الضوئي للوثيقة.",
                "details": {"raw_input": raw_nid},
            })

        # 2. Missing Name
        # Validate that citizen_name contains real Arabic/English letters and is not header noise or single fragment
        is_valid_name = False
        if citizen_name:
            c_str = str(citizen_name).strip()
            has_letters = bool(re.search(r"[\u0621-\u064Aa-zA-Z]", c_str))
            not_placeholder = c_str not in ("Missing from card", "مفقود من الوثيقة", "None", "")
            not_header = not any(h in c_str for h in ["بطاقة", "تحقيق", "الشخصية", "تحقليق", "الداخلية", "الأحوال", "المدنية", "جمهورية"])
            if has_letters and not_placeholder and not_header and len(c_str) >= 4 and len(c_str.split()) >= 2:
                is_valid_name = True
        has_name = is_valid_name

        if not is_valid_name or (name_extracted is False):
            reasons.append({
                "code": KycReasonCode.MISSING_FIELD_NAME.value,
                "severity": KycSeverity.WARNING.value,
                "field": "name",
                "explanation_en": "Citizen full name is missing or contains invalid noise in document extraction.",
                "explanation_ar": "اسم المواطن بالكامل مفقود أو غير صالح في البيانات المستخرجة للوثيقة.",
                "details": {"raw_name": citizen_name},
            })

        # 3. Missing Address
        is_valid_address = False
        if address:
            a_str = str(address).strip()
            has_letters = bool(re.search(r"[\u0621-\u064Aa-zA-Z]", a_str))
            not_placeholder = a_str not in ("Missing from card", "مفقود من الوثيقة", "None", "")
            if has_letters and not_placeholder and len(a_str) >= 5:
                is_valid_address = True
        has_address = is_valid_address

        if not is_valid_address or (address_extracted is False):
            reasons.append({
                "code": KycReasonCode.MISSING_FIELD_ADDRESS.value,
                "severity": KycSeverity.WARNING.value,
                "field": "address",
                "explanation_en": "Residential address is missing or incomplete in document extraction.",
                "explanation_ar": "محل الإقامة مفقود أو غير مكتمل في البيانات المستخرجة للوثيقة.",
                "details": {"raw_address": address},
            })

        # -------------------------------------------------------------
        # Check (e): Invalid National ID Structural Rules (9D Validator)
        # -------------------------------------------------------------
        clean_nid = None
        if raw_nid and str(raw_nid).strip() not in ("****", "None", ""):
            norm_status, clean_id = NationalIDValidator.normalize_digits(str(raw_nid))
            if norm_status.value == "NORMALIZATION_PASSED" and clean_id:
                clean_nid = clean_id
                struct_res = NationalIDValidator.validate_structure(clean_nid)
                fmt_status = struct_res.get("format_status")
                gov_status = struct_res.get("governorate_status")
                derived_dob = derived_dob or (struct_res.get("birth_date").isoformat() if struct_res.get("birth_date") else None)
                derived_gov_ar = derived_gov_ar or struct_res.get("governorate_ar")

                if fmt_status != FormatValidationStatus.FORMAT_VALID:
                    reasons.append({
                        "code": KycReasonCode.INVALID_ID_STRUCTURE.value,
                        "severity": KycSeverity.CRITICAL.value,
                        "field": "national_id",
                        "explanation_en": f"National ID failed structural calendar validation: {fmt_status.value}.",
                        "explanation_ar": f"فشل الرقم القومي في التحقق الهيكلي من صحة التاريخ: {fmt_status.value}.",
                        "details": {"format_status": fmt_status.value},
                    })
                elif gov_status != GovernorateReferenceStatus.GOVERNORATE_REFERENCE_MATCHED:
                    reasons.append({
                        "code": KycReasonCode.INVALID_ID_STRUCTURE.value,
                        "severity": KycSeverity.CRITICAL.value,
                        "field": "national_id",
                        "explanation_en": f"National ID contains unlisted governorate reference code: {clean_nid[7:9]}.",
                        "explanation_ar": f"الرقم القومي يتضمن كود محافظة غير مسجل في جدول الأكواد الرسمية: {clean_nid[7:9]}.",
                        "details": {"governorate_code": clean_nid[7:9]},
                    })
        elif has_nid and ("INVALID_FORMAT" in pipeline_format_status or "INVALID_DATE" in pipeline_format_status):
            reasons.append({
                "code": KycReasonCode.INVALID_ID_STRUCTURE.value,
                "severity": KycSeverity.CRITICAL.value,
                "field": "national_id",
                "explanation_en": f"National ID failed structural calendar validation: {pipeline_format_status}.",
                "explanation_ar": f"فشل الرقم القومي في التحقق الهيكلي من صحة التاريخ: {pipeline_format_status}.",
                "details": {"format_status": pipeline_format_status},
            })
        elif has_nid and "GOVERNORATE_REFERENCE_UNMATCHED" in pipeline_gov_status:
            reasons.append({
                "code": KycReasonCode.INVALID_ID_STRUCTURE.value,
                "severity": KycSeverity.CRITICAL.value,
                "field": "national_id",
                "explanation_en": "National ID contains unlisted governorate reference code.",
                "explanation_ar": "الرقم القومي يتضمن كود محافظة غير مسجل في جدول الأكواد الرسمية.",
                "details": {"governorate_status": pipeline_gov_status},
            })

        # -------------------------------------------------------------
        # Check (a): Birth Date Derived vs Extracted / Comparison DOB
        # -------------------------------------------------------------
        extracted_dob = extracted_fields.get("birth_date_extracted") or (comparison_data.get("birth_date") if comparison_data else None)
        if derived_dob and extracted_dob:
            norm_derived = str(derived_dob).strip()
            norm_extracted = str(extracted_dob).strip().translate(EASTERN_TO_WESTERN_DIGITS)
            norm_extracted = re.sub(r"[/.]", "-", norm_extracted)

            if norm_derived != norm_extracted:
                reasons.append({
                    "code": KycReasonCode.BIRTH_DATE_MISMATCH.value,
                    "severity": KycSeverity.CRITICAL.value,
                    "field": "birth_date",
                    "explanation_en": f"Derived birth date from National ID ({norm_derived}) does not match declared/extracted birth date ({norm_extracted}).",
                    "explanation_ar": f"تاريخ الميلاد المستنتج من الرقم القومي ({norm_derived}) لا يتطابق مع تاريخ الميلاد المصرح به/المستخرج ({norm_extracted}).",
                    "details": {
                        "derived_birth_date": norm_derived,
                        "extracted_birth_date": norm_extracted,
                    },
                })

        # -------------------------------------------------------------
        # Check (b): Governorate Derived from ID vs Extracted Address
        # -------------------------------------------------------------
        derived_gov_code = None
        if clean_nid and len(clean_nid) >= 9:
            derived_gov_code = clean_nid[7:9]
        elif derived_gov_ar and derived_gov_ar in NAME_TO_CODE:
            derived_gov_code = NAME_TO_CODE[derived_gov_ar]

        if derived_gov_code and address and str(address).strip() not in ("Missing from card", "مفقود من الوثيقة", "None", ""):
            addr_govs = detect_address_governorates(address)
            if addr_govs:
                matched_codes = [g[0] for g in addr_govs]
                if derived_gov_code not in matched_codes:
                    detected_names_ar = ", ".join(GOVERNORATE_GEO_MAP[c]["ar"] for c in matched_codes if c in GOVERNORATE_GEO_MAP)
                    detected_names_en = ", ".join(GOVERNORATE_GEO_MAP[c]["en"] for c in matched_codes if c in GOVERNORATE_GEO_MAP)
                    exp_name_ar = derived_gov_ar or GOVERNORATE_GEO_MAP.get(derived_gov_code, {}).get("ar", derived_gov_code)
                    exp_name_en = GOVERNORATE_CODES.get(derived_gov_code, (derived_gov_code, ""))[0]

                    reasons.append({
                        "code": KycReasonCode.GOVERNORATE_MISMATCH.value,
                        "severity": KycSeverity.CRITICAL.value,
                        "field": "governorate",
                        "explanation_en": f"Governorate derived from National ID ({exp_name_en}) conflicts with residential address location ({detected_names_en}).",
                        "explanation_ar": f"المحافظة المستنتجة من الرقم القومي ({exp_name_ar}) تتعارض مع الموقع السكني في العنوان ({detected_names_ar}).",
                        "details": {
                            "derived_governorate_code": derived_gov_code,
                            "derived_governorate_ar": exp_name_ar,
                            "detected_governorates": matched_codes,
                        },
                    })

        # -------------------------------------------------------------
        # Check (d): Low OCR Confidence Below Configurable Thresholds & Image Quality
        # -------------------------------------------------------------
        nid_thresh = self.thresholds.get("national_id", 0.85)
        name_thresh = self.thresholds.get("name", 0.70)
        addr_thresh = self.thresholds.get("address", 0.70)

        prep_meta = extracted_fields.get("preprocessing_meta", {}) if isinstance(extracted_fields.get("preprocessing_meta"), dict) else {}
        qa = (
            extracted_fields.get("quality_metrics")
            or extracted_fields.get("quality_assessment")
            or prep_meta.get("quality_assessment")
            or {}
        )
        is_dark_or_blurry = (
            qa.get("contrast_std", 100.0) < 10.0
            or qa.get("brightness_mean", 100.0) < 75.0
            or (qa.get("sharpness_laplacian", 100.0) < 15.0 and qa.get("is_blurry", False))
        )

        is_low_conf = (
            "OCR_LOW_CONFIDENCE" in pipeline_ocr_status
            or is_dark_or_blurry
            or (has_nid and 0.0 < nid_conf < nid_thresh)
            or (has_name and 0.0 < name_conf < name_thresh)
            or (has_address and 0.0 < address_conf < addr_thresh)
        )

        if is_low_conf:
            flagged_fields = []
            if has_nid and 0.0 < nid_conf < nid_thresh:
                flagged_fields.append(f"National ID ({nid_conf:.1%})")
            if has_name and 0.0 < name_conf < name_thresh:
                flagged_fields.append(f"Name ({name_conf:.1%})")
            if has_address and 0.0 < address_conf < addr_thresh:
                flagged_fields.append(f"Address ({address_conf:.1%})")
            if not flagged_fields:
                flagged_fields.append(f"Overall OCR ({min(nid_conf, name_conf, address_conf):.1%})")

            reasons.append({
                "code": KycReasonCode.LOW_OCR_CONFIDENCE.value,
                "severity": KycSeverity.WARNING.value,
                "field": "ocr_quality",
                "explanation_en": f"OCR extraction confidence for {', '.join(flagged_fields)} is below acceptable threshold.",
                "explanation_ar": f"نسبة ثقة محرك الاستخراج للحقول ({', '.join(flagged_fields)}) أقل من حد القبول الأدنى.",
                "details": {
                    "national_id_conf": nid_conf,
                    "name_conf": name_conf,
                    "address_conf": address_conf,
                },
            })

        # -------------------------------------------------------------
        # Decision Synthesis & Invariant Routing
        # -------------------------------------------------------------
        has_critical = any(r["severity"] == KycSeverity.CRITICAL.value for r in reasons)
        has_warning = any(r["severity"] == KycSeverity.WARNING.value for r in reasons)
        is_escalated = bool(reasons)

        recommended_status = "FLAGGED" if has_critical else "PENDING_REVIEW"

        return {
            "is_escalated": is_escalated,
            "has_critical_failure": has_critical,
            "has_quality_warning": has_warning,
            "recommended_status": recommended_status,
            "review_status": "REQUIRES_HUMAN_REVIEW",
            "identity_verification_status": "NOT_VERIFIED",
            "reason_count": len(reasons),
            "reasons": reasons,
            "reason_codes": [r["code"] for r in reasons],
        }


# Global singleton instance
kyc_check_service = KycCheckService()
