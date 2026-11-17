"""Evaluate 60 Held-Out Synthetic Cards against OCR Pipeline and KYC Exception Detector.

Processes cards from data/synthetic_cards/eval_held_out_60/ and records evaluation metrics in
data/kyc_mismatch_held_out_60_results.json.
"""

import json
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from app.services.image_pipeline import image_ocr_pipeline
from app.services.kyc_checks import kyc_check_service, KycReasonCode

CARDS_DIR = os.path.join(REPO_ROOT, "data", "synthetic_cards", "eval_held_out_60")
MANIFEST_PATH = os.path.join(CARDS_DIR, "manifest.json")
RESULTS_PATH = os.path.join(REPO_ROOT, "data", "kyc_mismatch_held_out_60_results.json")

def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    total_cards = len(manifest)
    print(f"Starting KYC Evaluation across {total_cards} held-out cards...", flush=True)

    evaluated_records = []
    t_start = time.time()

    for idx, card in enumerate(manifest, 1):
        cid = card["card_id"]
        fname = card["filename"]
        fpath = os.path.join(CARDS_DIR, fname)
        t_card = time.time()

        # Run OCR
        ocr_res = image_ocr_pipeline.process_image(
            image_input=fpath,
            case_id=cid,
        )

        # Run KYC checks
        comp_data = card.get("comparison_data", {})
        eval_res = kyc_check_service.evaluate_case(
            extracted_fields=ocr_res,
            comparison_data=comp_data,
        )

        dur = time.time() - t_card
        is_anomaly = card["is_anomaly"]
        detected_anomaly = eval_res["is_escalated"]
        reasons = eval_res.get("reason_codes", [])

        # Classification
        if is_anomaly and detected_anomaly:
            clf = "TP"
        elif not is_anomaly and not detected_anomaly:
            clf = "TN"
        elif not is_anomaly and detected_anomaly:
            clf = "FP"
        else:
            clf = "FN"

        evaluated_records.append({
            "card_id": cid,
            "filename": fname,
            "condition": card["condition"],
            "is_ground_truth_anomaly": is_anomaly,
            "expected_reasons": card.get("expected_reasons", []),
            "detected_reasons": reasons,
            "is_escalated": detected_anomaly,
            "recommended_status": eval_res.get("recommended_status"),
            "review_status": eval_res.get("review_status"),
            "classification": clf,
            "duration_sec": round(dur, 2),
            "extracted_fields": {
                "national_id": ocr_res.get("masked_national_id"),
                "name": ocr_res.get("name"),
                "address": ocr_res.get("address"),
                "birth_date": ocr_res.get("birth_date"),
                "governorate": ocr_res.get("governorate"),
                "nid_conf": ocr_res.get("national_id_conf"),
                "name_conf": ocr_res.get("name_conf"),
                "address_conf": ocr_res.get("address_conf"),
            },
        })

        exp_str = ",".join(card.get("expected_reasons", [])) or "NONE"
        det_str = ",".join(reasons) or "CLEAN"
        print(f"[{idx:02d}/{total_cards}] [{clf}] {cid} ({dur:.2f}s) | Exp: [{exp_str}] | Det: [{det_str}]", flush=True)

    total_time = time.time() - t_start

    tp = sum(1 for r in evaluated_records if r["classification"] == "TP")
    tn = sum(1 for r in evaluated_records if r["classification"] == "TN")
    fp = sum(1 for r in evaluated_records if r["classification"] == "FP")
    fn = sum(1 for r in evaluated_records if r["classification"] == "FN")

    n_pos = tp + fn
    n_neg = tn + fp

    recall = (tp / n_pos * 100.0) if n_pos else 0.0
    precision = (tp / (tp + fp) * 100.0) if (tp + fp) else 0.0
    specificity = (tn / n_neg * 100.0) if n_neg else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = ((tp + tn) / total_cards * 100.0) if total_cards else 0.0
    escalation_correctness = (tp / n_pos * 100.0) if n_pos else 0.0

    all_reason_codes = [c.value for c in KycReasonCode]
    per_reason_metrics = {}

    for code in all_reason_codes:
        c_tp = 0
        c_fp = 0
        c_fn = 0
        for r in evaluated_records:
            in_expected = code in r["expected_reasons"]
            in_detected = code in r["detected_reasons"]
            if in_expected and in_detected:
                c_tp += 1
            elif in_expected and not in_detected:
                c_fn += 1
            elif not in_expected and in_detected:
                c_fp += 1

        c_rec = (c_tp / (c_tp + c_fn) * 100.0) if (c_tp + c_fn) else 0.0
        c_prec = (c_tp / (c_tp + c_fp) * 100.0) if (c_tp + c_fp) else 0.0

        per_reason_metrics[code] = {
            "expected_count": c_tp + c_fn,
            "detected_count": c_tp + c_fp,
            "true_positives": c_tp,
            "false_positives": c_fp,
            "false_negatives": c_fn,
            "recall": round(c_rec, 1),
            "precision": round(c_prec, 1),
        }

    output_summary = {
        "dataset_type": "HELD-OUT",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_cards": total_cards,
        "execution_duration_sec": round(total_time, 2),
        "confusion_matrix": {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "total_positive_ground_truth": n_pos,
            "total_negative_ground_truth": n_neg,
        },
        "overall_metrics": {
            "recall": round(recall, 2),
            "precision": round(precision, 2),
            "specificity": round(specificity, 2),
            "f1_score": round(f1, 2),
            "accuracy": round(accuracy, 2),
            "escalation_correctness": round(escalation_correctness, 2),
            "handbook_target_recall": 95.0,
            "target_status": "MET" if recall >= 95.0 else "NOT MET",
        },
        "per_reason_code_metrics": per_reason_metrics,
        "evaluated_records": evaluated_records,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output_summary, f, ensure_ascii=False, indent=2)

    print(f"\nCompleted evaluation! Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    main()
