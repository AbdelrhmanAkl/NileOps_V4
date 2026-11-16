"""Generate synthetic Egyptian utility bill fixtures (Electricity, Gas, Water) for dual-document cross-verification.

Produces synthetic fixtures with clean matches, name typos/mismatches, address/governorate discrepancies,
and expired bill dates (> 90 days) for testing and evaluation.
Synthetic data only — zero real citizen or consumer PII.
"""

from datetime import date, timedelta
import json
import os
from typing import Any, Dict, List


def generate_synthetic_utility_bills() -> List[Dict[str, Any]]:
    today = date.today()

    bills = [
        # 1. Clean Match (Cairo, Electricity, 25 days old)
        {
            "id": "bill-clean-01",
            "utility_type": "ELECTRICITY_BILL",
            "provider_name": "شركة شمال القاهرة لتوزيع الكهرباء",
            "consumer_name": "محمود عادل إبراهيم حسن",
            "service_address": "15 شارع النيل، المعادي، القاهرة",
            "issue_date": (today - timedelta(days=25)).isoformat(),
            "account_number": "ELEC-CAI-984210",
            "meter_number": "MTR-55421",
            "expected_match": True,
            "expected_discrepancy": None,
        },
        # 2. Clean Match with Minor Typo/Alef Variant (Giza, Gas, 45 days old)
        {
            "id": "bill-clean-02",
            "utility_type": "NATURAL_GAS_BILL",
            "provider_name": "شركة تاون جاس - مصر",
            "consumer_name": "احمد سامي عبد الرحمن",  # Matches أحمد سامي عبد الرحمن
            "service_address": "40 شارع الدقي، الجيزة",
            "issue_date": (today - timedelta(days=45)).isoformat(),
            "account_number": "GAS-GIZ-331298",
            "meter_number": "MTR-88124",
            "expected_match": True,
            "expected_discrepancy": None,
        },
        # 3. Clean Match with 3-part vs 4-part name (Alexandria, Water, 60 days old)
        {
            "id": "bill-clean-03",
            "utility_type": "WATER_BILL",
            "provider_name": "شركة مياه الشرب بالإسكندرية",
            "consumer_name": "سارة محمد إبراهيم",  # ID has سارة محمد إبراهيم حسن
            "service_address": "25 طريق الجيش، سيدي جابر، الإسكندرية",
            "issue_date": (today - timedelta(days=60)).isoformat(),
            "account_number": "WTR-ALX-774120",
            "meter_number": "MTR-12948",
            "expected_match": True,
            "expected_discrepancy": None,
        },
        # 4. Name Mismatch (Completely different person)
        {
            "id": "bill-mismatch-name",
            "utility_type": "ELECTRICITY_BILL",
            "provider_name": "شركة جنوب القاهرة لتوزيع الكهرباء",
            "consumer_name": "خالد محمود عبد العزيز",  # Does not match ID
            "service_address": "15 شارع النيل، المعادي، القاهرة",
            "issue_date": (today - timedelta(days=20)).isoformat(),
            "account_number": "ELEC-CAI-112233",
            "meter_number": "MTR-99411",
            "expected_match": False,
            "expected_discrepancy": "NAME_MISMATCH_ACROSS_DOCS",
        },
        # 5. Address / Governorate Mismatch (ID Cairo vs Bill Alexandria)
        {
            "id": "bill-mismatch-addr",
            "utility_type": "ELECTRICITY_BILL",
            "provider_name": "شركة الإسكندرية لتوزيع الكهرباء",
            "consumer_name": "محمود عادل إبراهيم حسن",
            "service_address": "12 طريق الحرية، المنتزه، الإسكندرية",
            "issue_date": (today - timedelta(days=30)).isoformat(),
            "account_number": "ELEC-ALX-445566",
            "meter_number": "MTR-33214",
            "expected_match": False,
            "expected_discrepancy": "ADDRESS_MISMATCH_ACROSS_DOCS",
        },
        # 6. Bill Too Old (> 90 days, e.g. 150 days old)
        {
            "id": "bill-too-old",
            "utility_type": "ELECTRICITY_BILL",
            "provider_name": "شركة شمال القاهرة لتوزيع الكهرباء",
            "consumer_name": "محمود عادل إبراهيم حسن",
            "service_address": "15 شارع النيل، المعادي، القاهرة",
            "issue_date": (today - timedelta(days=150)).isoformat(),
            "account_number": "ELEC-CAI-998877",
            "meter_number": "MTR-77412",
            "expected_match": False,
            "expected_discrepancy": "UTILITY_BILL_TOO_OLD",
        },
    ]
    return bills


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_bills")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_utility_bills.json")
    bills = generate_synthetic_utility_bills()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(bills)} synthetic utility bill fixtures at: {out_path}")
