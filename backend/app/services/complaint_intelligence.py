"""NileOps Complaint Advisory Intelligence & Draft Reply Engine.

Provides deterministic keyword/rule-based suggestions (category, team, priority)
with matched keywords, and an optional local Ollama draft reply with graceful
deterministic template fallback.

All outputs are strictly labeled: 'AI suggestion - requires human review'.
"""

import json
import logging
import urllib.request
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

ADVISORY_LABEL = "AI suggestion - requires human review"

# Bilingual keyword dictionaries for deterministic categorization
CATEGORY_KEYWORD_RULES: Dict[str, List[str]] = {
    "ATM_CARD": [
        "atm", "card", "swallowed", "captured", "dispense", "cash", "pin", "retained",
        "debit", "credit", "machine", "صراف", "ماكينة", "بطاقة", "سحب", "بلع", "احتجاز", "كارت"
    ],
    "TRANSFER": [
        "instapay", "transfer", "fawry", "ach", "swift", "pending", "credited", "recipient",
        "beneficiary", "transaction", "تحويل", "إنستاباي", "انستاباي", "فوري", "حوالة", "معاملة", "إيداع"
    ],
    "ACCOUNT_FEES": [
        "fee", "fees", "charge", "charges", "deduction", "commission", "overdraft", "balance",
        "maintenance", "رسوم", "عمولة", "خصم", "مصاريف", "رصيد", "صيانة"
    ],
    "MOBILE_BANKING": [
        "app", "application", "login", "otp", "password", "crash", "mobile", "ios", "android",
        "error code", "تطبيق", "تسجيل الدخول", "رمز", "كلمة سر", "تعليق"
    ],
    "GENERAL_INQUIRY": [
        "inquiry", "question", "branch", "working hours", "open account", "certificate",
        "استفسار", "سؤال", "فرع", "مواعيد", "شهادة", "خدمة"
    ],
}

# Team routing map based on category
CATEGORY_TEAM_MAP: Dict[str, str] = {
    "ATM_CARD": "CARDS_PAYMENTS",
    "TRANSFER": "OPERATIONS",
    "ACCOUNT_FEES": "CUSTOMER_SERVICE",
    "MOBILE_BANKING": "CUSTOMER_SERVICE",
    "GENERAL_INQUIRY": "BRANCH_NETWORK",
}

# Priority keywords
URGENT_KEYWORDS: List[str] = [
    "fraud", "stolen", "unauthorized", "emergency", "retained", "hacked", "police",
    "سرقة", "احتيال", "اختراق", "طارئ", "عاجل", "سحب بدون علم"
]

HIGH_KEYWORDS: List[str] = [
    "failed", "dispute", "not received", "double charge", "debited", "delayed",
    "فشل", "خصم مكرر", "لم تصل", "معلق", "تأخير"
]


class AdvisoryClassificationResult(BaseModel):
    """Advisory suggestion bundle for employee review."""
    advisory_label: str = ADVISORY_LABEL
    suggested_category: str
    suggested_team: str
    suggested_priority: str
    matched_keywords: List[str]
    draft_reply: str
    generation_source: str  # "DETERMINISTIC_TEMPLATE" or "OLLAMA_LOCAL"
    confidence_claimed: bool = False
    confidence_note: str = "Deterministic keyword-rule match; no unverified confidence claims."


def match_keywords_in_text(text: str, keywords: List[str]) -> List[str]:
    """Find all matching keywords within lowercase text."""
    text_lower = text.lower()
    matches = []
    for kw in keywords:
        if kw.lower() in text_lower:
            matches.append(kw)
    return matches


def classify_complaint_deterministically(
    subject: str,
    details: str,
    customer_name: Optional[str] = None,
    ticket_number: Optional[str] = None,
) -> AdvisoryClassificationResult:
    """Analyze subject and details to produce advisory classification and draft response."""
    combined_text = f"{subject} {details}"
    matched_by_cat: Dict[str, List[str]] = {}
    all_matched_keywords: List[str] = []

    # 1. Match category keywords
    for cat, kws in CATEGORY_KEYWORD_RULES.items():
        found = match_keywords_in_text(combined_text, kws)
        if found:
            matched_by_cat[cat] = found
            all_matched_keywords.extend(found)

    # Determine highest matching category
    if matched_by_cat:
        best_category = max(matched_by_cat.keys(), key=lambda k: len(matched_by_cat[k]))
    else:
        best_category = "GENERAL_INQUIRY"

    # 2. Determine team assignment
    suggested_team = CATEGORY_TEAM_MAP.get(best_category, "CUSTOMER_SERVICE")

    # 3. Determine priority
    urgent_matches = match_keywords_in_text(combined_text, URGENT_KEYWORDS)
    high_matches = match_keywords_in_text(combined_text, HIGH_KEYWORDS)

    if urgent_matches:
        suggested_priority = "URGENT"
        all_matched_keywords.extend(urgent_matches)
    elif high_matches:
        suggested_priority = "HIGH"
        all_matched_keywords.extend(high_matches)
    elif best_category in ("ATM_CARD", "TRANSFER"):
        suggested_priority = "MEDIUM"
    else:
        suggested_priority = "LOW"

    # Deduplicate matched keywords
    unique_keywords = sorted(list(set(all_matched_keywords)))

    # 4. Generate draft reply (Deterministic Template first)
    cname = customer_name or "Valued Customer"
    tnum = ticket_number or "CMP-2026-TICKET"

    template_draft = (
        f"Dear {cname},\n\n"
        f"Thank you for contacting NileOps Demo Bank. We have registered your complaint under ticket #{tnum} "
        f"concerning {subject.strip()}.\n\n"
        f"Our {suggested_team.replace('_', ' ').title()} Team is actively investigating the incident. "
        f"Under our simulated service policy, we target resolution within our priority SLA timeframe. "
        f"No funds or personal data have been compromised.\n\n"
        f"عزيزي العميل،\n"
        f"نشكر تواصلكم مع بنك النيل التجريبي. تم تسجيل طلبكم برقم تذكرة #{tnum} وجاري مراجعته والتحقق من العملية "
        f"عبر الفريق المختص لضمان سرعة التسوية وفق معايير الجودة المعتمدة.\n\n"
        f"Sincerely,\n"
        f"NileOps Banking Operations Team"
    )

    # 5. Optional local Ollama draft reply (strict 2.0s timeout)
    draft_reply = template_draft
    generation_source = "DETERMINISTIC_TEMPLATE"

    try:
        ollama_url = getattr(settings, "OLLAMA_URL", "http://127.0.0.1:11434")
        ollama_model = getattr(settings, "OLLAMA_MODEL", "qwen3:8b")
        req_data = json.dumps({
            "model": ollama_model,
            "prompt": (
                f"As a retail bank customer service officer, write a concise, professional 3-sentence acknowledgement "
                f"and action response in English and Arabic for ticket {tnum} regarding: {subject}. Customer name is {cname}."
            ),
            "stream": False,
        }).encode("utf-8")
        
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            candidate = resp_data.get("response", "").strip()
            if candidate and len(candidate) > 40:
                draft_reply = candidate
                generation_source = "OLLAMA_LOCAL"
    except Exception as e:
        logger.debug(f"Ollama local draft generation skipped or timed out: {e}")
        # Gracefully keep deterministic template

    return AdvisoryClassificationResult(
        advisory_label=ADVISORY_LABEL,
        suggested_category=best_category,
        suggested_team=suggested_team,
        suggested_priority=suggested_priority,
        matched_keywords=unique_keywords,
        draft_reply=draft_reply,
        generation_source=generation_source,
    )

