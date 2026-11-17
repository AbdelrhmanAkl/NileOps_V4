"""NileOps Handbook Evaluation — Per-Field OCR Extraction F1 Benchmark.

Evaluates field-level extraction accuracy (Exact Match / F1) on synthetic Egyptian National ID cards
across 4 conditions: Clean, Glare, Blur, and Low Contrast / Shadow (N=40 cards).

Fields measured:
- National ID (14 digits)
- Citizen Name
- Residential Address
- Factory Code

Handbook Target: field F1 >= 90.0%
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO_ROOT / "data" / "ocr_evaluation_summary.json"
OUTPUT_PATH = REPO_ROOT / "scratch" / "eval_ocr_results.json"


def run_evaluation() -> Dict[str, Any]:
    target_path = DATA_PATH
    if not target_path.exists():
        fallback_path = REPO_ROOT / "scratch" / "ocr_evaluation_summary.json"
        if fallback_path.exists():
            target_path = fallback_path
        else:
            raise FileNotFoundError(f"OCR evaluation summary not found at {DATA_PATH}")

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results: List[Dict[str, Any]] = data.get("results", [])
    total_cards = len(results)

    if total_cards == 0:
        raise ValueError("No evaluation records found in OCR evaluation summary.")

    # Aggregate metric accumulators
    em_id_sum = 0
    em_name_sum = 0
    em_addr_sum = 0
    em_fc_sum = 0
    review_sum = 0

    per_condition: Dict[str, Dict[str, Any]] = {}

    for r in results:
        cond = r.get("condition", "UNKNOWN")
        tuned = r.get("tuned", {})

        em_id = tuned.get("em_id", 0)
        em_name = tuned.get("em_name", 0)
        em_addr = tuned.get("em_addr", 0)
        em_fc = tuned.get("em_fc", 0)
        req_review = 1 if tuned.get("requires_review", False) else 0

        em_id_sum += em_id
        em_name_sum += em_name
        em_addr_sum += em_addr
        em_fc_sum += em_fc
        review_sum += req_review

        if cond not in per_condition:
            per_condition[cond] = {"count": 0, "em_id": 0, "em_name": 0, "em_addr": 0, "em_fc": 0}

        per_condition[cond]["count"] += 1
        per_condition[cond]["em_id"] += em_id
        per_condition[cond]["em_name"] += em_name
        per_condition[cond]["em_addr"] += em_addr
        per_condition[cond]["em_fc"] += em_fc

    id_f1 = (em_id_sum / total_cards) * 100.0
    name_f1 = (em_name_sum / total_cards) * 100.0
    addr_f1 = (em_addr_sum / total_cards) * 100.0
    fc_f1 = (em_fc_sum / total_cards) * 100.0
    review_rate = (review_sum / total_cards) * 100.0

    target = "field F1 >= 90.0%"

    summary = {
        "benchmark_name": "40_card_ocr_field_extraction_benchmark",
        "sample_size": total_cards,
        "conditions": list(per_condition.keys()),
        "metrics": {
            "national_id_f1_pct": round(id_f1, 2),
            "name_f1_pct": round(name_f1, 2),
            "address_f1_pct": round(addr_f1, 2),
            "factory_code_f1_pct": round(fc_f1, 2),
            "human_review_rate_pct": round(review_rate, 2),
        },
        "targets": {
            "handbook_target": target,
            "national_id_status": "MET" if id_f1 >= 90.0 else "NOT MET",
            "name_status": "MET" if name_f1 >= 90.0 else "NOT MET",
            "address_status": "MET" if addr_f1 >= 90.0 else "NOT MET",
            "factory_code_status": "MET" if fc_f1 >= 90.0 else "NOT MET",
        },
        "per_condition_breakdown": {
            cond: {
                "sample_size": v["count"],
                "national_id_f1": round((v["em_id"] / v["count"]) * 100.0, 1),
                "name_f1": round((v["em_name"] / v["count"]) * 100.0, 1),
                "address_f1": round((v["em_addr"] / v["count"]) * 100.0, 1),
                "factory_code_f1": round((v["em_fc"] / v["count"]) * 100.0, 1),
            }
            for cond, v in per_condition.items()
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n--- OCR Field Extraction F1 Summary ---")
    print(f"Sample Size: {total_cards} Cards (Clean, Glare, Blur, Shadow)")
    print(f"National ID Field F1:  {id_f1:.1f}% (Target: >=90.0%) -> {summary['targets']['national_id_status']}")
    print(f"Name Field F1:         {name_f1:.1f}% (Target: >=90.0%) -> {summary['targets']['name_status']}")
    print(f"Address Field F1:      {addr_f1:.1f}% (Target: >=90.0%) -> {summary['targets']['address_status']}")
    print(f"Factory Code Field F1: {fc_f1:.1f}% (Target: >=90.0%) -> {summary['targets']['factory_code_status']}")
    print(f"Human Review Rate:     {review_rate:.1f}%")

    return summary


if __name__ == "__main__":
    run_evaluation()
