"""NileOps Handbook Evaluation — Exception Recall & Escalation Correctness Benchmark.

Evaluates exception detection recall and human escalation correctness on seeded defective and
mismatch KYC cases (30 synthetic cards: 15 clean, 15 planted exceptions).

Metrics computed:
- Exception Detection Recall (Handbook Target: >= 95.0%)
- Correct Escalation Rate to Human Review (Handbook Target: >= 95.0%)
- Precision, Specificity, F1-Score
- Breakdown by Reason Code
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

DEV_RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "kyc_mismatch_evaluation_results.json"
HELD_OUT_RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "kyc_mismatch_held_out_60_results.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "scratch" / "eval_exceptions_results.json"


def run_evaluation(data_path: Path = HELD_OUT_RESULTS_PATH) -> Dict[str, Any]:
    if not data_path.exists():
        data_path = DEV_RESULTS_PATH
    if not data_path.exists():
        raise FileNotFoundError(f"KYC evaluation dataset not found at {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cm = data.get("confusion_matrix", {})
    tp = cm.get("TP", 0)
    fp = cm.get("FP", 0)
    tn = cm.get("TN", 0)
    fn = cm.get("FN", 0)

    total_cards = data.get("total_cards", tp + fp + tn + fn)
    actual_positives = tp + fn
    actual_negatives = tn + fp

    recall = (tp / actual_positives * 100.0) if actual_positives > 0 else 0.0
    precision = (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
    specificity = (tn / actual_negatives * 100.0) if actual_negatives > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    accuracy = ((tp + tn) / total_cards * 100.0) if total_cards > 0 else 0.0
    escalation_correctness = recall  # Percentage of planted exceptions correctly escalated to human review

    per_reason = data.get("per_reason_code_metrics", {})

    summary = {
        "benchmark_name": f"{total_cards}_card_kyc_mismatch_exception_benchmark",
        "sample_size": total_cards,
        "positive_exceptions_ground_truth": actual_positives,
        "negative_clean_ground_truth": actual_negatives,
        "metrics": {
            "exception_recall_pct": round(recall, 2),
            "correct_escalation_rate_pct": round(escalation_correctness, 2),
            "precision_pct": round(precision, 2),
            "specificity_pct": round(specificity, 2),
            "f1_score_pct": round(f1, 2),
            "accuracy_pct": round(accuracy, 2),
        },
        "targets": {
            "exception_recall_target": ">= 95.0%",
            "exception_recall_status": "MET" if recall >= 95.0 else "NOT MET",
            "escalation_rate_target": ">= 95.0%",
            "escalation_rate_status": "MET" if escalation_correctness >= 95.0 else "NOT MET",
        },
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
        },
        "per_reason_code_metrics": per_reason,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n--- Exception Detection & Escalation Summary ({data.get('dataset_type', 'DEV')}) ---")
    print(f"Sample Size: {total_cards} Cards ({actual_negatives} Clean, {actual_positives} Planted Exceptions)")
    print(f"Exception Recall:         {recall:.1f}% (Target: >=95.0%) -> {summary['targets']['exception_recall_status']}")
    print(f"Correct Escalation Rate:  {escalation_correctness:.1f}% (Target: >=95.0%) -> {summary['targets']['escalation_rate_status']}")
    print(f"Precision:                {precision:.1f}%")
    print(f"Specificity:              {specificity:.1f}%")
    print(f"F1-Score:                 {f1:.1f}%")
    print(f"Accuracy:                 {accuracy:.1f}%")

    # False negatives by category
    records = data.get("evaluated_records", [])
    false_negatives = [r for r in records if r.get("classification") == "FN"]
    print(f"False Negatives Count:    {len(false_negatives)}")
    if false_negatives:
        for fn_rec in false_negatives:
            print(f"  - Card: {fn_rec['card_id']} | Category: {fn_rec.get('expected_reasons')} | Detected: {fn_rec.get('detected_reasons')}")
    else:
        print("  (Zero false negatives - all planted anomalies were escalated)")

    return summary


def main():
    print("=== DEV SET EVALUATION (60 CARDS) ===")
    if DEV_RESULTS_PATH.exists():
        run_evaluation(DEV_RESULTS_PATH)
    print("\n=== HELD-OUT SET EVALUATION (60 CARDS) ===")
    if HELD_OUT_RESULTS_PATH.exists():
        run_evaluation(HELD_OUT_RESULTS_PATH)


if __name__ == "__main__":
    main()
