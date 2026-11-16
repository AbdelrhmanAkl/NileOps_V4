"""Egyptian Colloquial Arabic & Banking Query Normalization Service.

Provides deterministic query preprocessing for Egyptian colloquial expressions (العامية المصرية)
and common banking terms before dense semantic vector retrieval in Qdrant.
Designed to bridge the vocabulary gap between colloquial customer inquiries and formal
Central Bank of Egypt (CBE) regulatory policy phrasing without altering query intent.
"""

import re
from typing import Dict, List, Tuple


# Documented Egyptian Banking Synonym Map
# Each entry maps a colloquial term or phrase to canonical regulatory policy terminology.
EGYPTIAN_BANKING_SYNONYMS: List[Tuple[re.Pattern, str]] = [
    # Money & Balance terms
    (re.compile(r"\bفلوس\b", re.IGNORECASE), "أموال رصيد"),
    (re.compile(r"\bمصاري\b", re.IGNORECASE), "أموال رصيد"),
    (re.compile(r"\bقد\s*ايه\b|\bكام\b", re.IGNORECASE), "الحد الأدنى مبلغ"),
    
    # Request & Intent verbs
    (re.compile(r"\b(عايز|عاوز|حابب|بدي|محتاج)\s+(افتح|اعمل|فتح)\b", re.IGNORECASE), "طلب فتح حساب"),
    (re.compile(r"\b(عايز|عاوز|حابب|بدي|محتاج)\b", re.IGNORECASE), "طلب الحصول على"),
    
    # ATM and Hardware terms
    (re.compile(r"\b(مكنة|مكينة|ماكينة)\s+(اي\s*تي\s*ام|atm|صراف)?\b", re.IGNORECASE), "ماكينة صراف آلي"),
    (re.compile(r"\b(سحب\s*وما\s*طلعش|سحب\s*ومطلعش|سحبت\s*ومطلعتش)\b", re.IGNORECASE), "خصم رصيد دون صرف نقدية من الصراف الآلي"),
    (re.compile(r"\b(اتسحبت|اتخصمت|خصمت|اتسحب)\b", re.IGNORECASE), "خصم رصيد ومعاملة بنكية"),
    
    # Cards & Payments
    (re.compile(r"\b(كارت|فيزا)\b", re.IGNORECASE), "بطاقة مصرفية خصم مباشر"),
    (re.compile(r"\b(انستاباي|انستا\s*باي|insta\s*pay)\b", re.IGNORECASE), "شبكة المدفوعات اللحظية انستاباي تحويل لحظي"),
    
    # Returns & Savings
    (re.compile(r"\b(فوايد|فايدة|ارباح)\b", re.IGNORECASE), "سعر الفائدة والعائد الدوري"),
    (re.compile(r"\b(شهادة|شهادات)\b", re.IGNORECASE), "شهادات الادخار والاستثمار"),
    (re.compile(r"\bحساب\s+عادي\b", re.IGNORECASE), "حساب جاري للأفراد"),
    
    # Identity & KYC
    (re.compile(r"\b(اتولد|مولود|ميلاد)\b", re.IGNORECASE), "تاريخ الميلاد والمحافظة بالرقم القومي"),
    (re.compile(r"\b(البطاقة|الرقم\s*القومي)\b", re.IGNORECASE), "بطاقة الرقم القومي المصري"),
    (re.compile(r"\b(تزوير|مزورة|مضروبة)\b", re.IGNORECASE), "تزوير ومخالفة معايير الهوية"),
    
    # Complaints & Disputes
    (re.compile(r"\b(اشتكي|شكوى|تظلم|اعمل\s+شكوى)\b", re.IGNORECASE), "تقديم شكوى مصرفية ونزاع"),
    (re.compile(r"\b(ترجع|استرداد|استرجع|يرجعولي)\b", re.IGNORECASE), "استرداد المبالغ وتسوية المنازعة"),
]


def normalize_colloquial_query(query: str) -> str:
    """Normalize colloquial Arabic and English query strings for resilient RAG retrieval.
    
    Applies regex-based synonym substitution while preserving overall sentence structure.
    """
    if not query:
        return ""
    
    normalized = query.strip()
    
    for pattern, replacement in EGYPTIAN_BANKING_SYNONYMS:
        if pattern.search(normalized):
            # Append canonical keywords while retaining original terms
            normalized = pattern.sub(lambda m: f"{m.group(0)} {replacement}", normalized)
            
    # Collapse excess whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

