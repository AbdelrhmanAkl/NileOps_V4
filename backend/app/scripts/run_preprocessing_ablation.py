import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.image_pipeline import image_ocr_pipeline
from app.services.ocr import FormatValidationStatus

FIXTURES_DIR = os.path.abspath(os.path.join(backend_dir, "..", "data", "synthetic_cards"))
OUTPUT_JSON = os.path.abspath(os.path.join(backend_dir, "..", "data", "ocr_preprocessing_ablation.json"))

MODES = [
    "NONE",
    "EXP_A_RESCALING",
    "EXP_B_CLAHE",
    "EXP_C_DESKEW",
    "EXP_D_COMBINED",
]

def get_cohort(filename: str) -> str:
    # card_01 to card_04 are synthetic; card_05 to card_15 are real cards
    base = os.path.splitext(filename)[0]
    num = int(base.split("_")[1])
    if num <= 4:
        return "SYNTHETIC"
    elif filename.endswith(".webp"):
        return "REAL_CARD_WEBP"
    else:
        return "REAL_CARD_JPEG"

def run_ablation():
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    all_files = sorted([f for f in os.listdir(FIXTURES_DIR) if f.startswith("card_")])

    print("================================================================================")
    print("NileOps OCR Phase 2.2 — Controlled Computer Vision Preprocessing Ablation")
    print(f"Total fixtures detected: {len(all_files)}")
    print(f"Modes to evaluate: {', '.join(MODES)}")
    print("================================================================================")

    # Initial SHA256 integrity check
    initial_hashes = {}
    for f in all_files:
        p = os.path.join(FIXTURES_DIR, f)
        with open(p, "rb") as fp:
            initial_hashes[f] = hashlib.sha256(fp.read()).hexdigest()

    raw_results: List[Dict[str, Any]] = []

    for mode in MODES:
        print(f"\n>>> Running Evaluation Mode: {mode} ...")
        t_mode_start = time.perf_counter()
        mode_results = []

        for f in all_files:
            file_path = os.path.join(FIXTURES_DIR, f)
            with open(file_path, "rb") as fp:
                img_bytes = fp.read()

            cohort = get_cohort(f)
            anon_id = f"ANON_{f.replace('.', '_')}"

            res = image_ocr_pipeline.process_image(
                img_bytes,
                case_id=anon_id,
                preprocessing_mode=mode
            )

            # Sanitize any PII for safe persistence
            safe_record = {
                "file_key": f,
                "cohort": cohort,
                "mode": mode,
                "ingestion_status": res["ingestion_status"],
                "masked_id": res["masked_national_id"],
                "format_status": str(res["format_status"].value) if hasattr(res["format_status"], "value") else str(res["format_status"]),
                "ocr_status": str(res["ocr_status"].value) if hasattr(res["ocr_status"], "value") else str(res["ocr_status"]),
                "review_status": str(res["review_status"].value) if hasattr(res["review_status"], "value") else str(res["review_status"]),
                "extracted_fields": {
                    "national_id_extracted": res["extracted_fields"]["national_id_extracted"],
                    "national_id_valid_14d": res["extracted_fields"]["national_id_extracted"] and res["format_status"] == FormatValidationStatus.FORMAT_VALID,
                    "national_id_confidence": res["extracted_fields"]["national_id_confidence"],
                    "name_extracted": res["extracted_fields"]["name_extracted"],
                    "name_confidence": res["extracted_fields"]["name_confidence"],
                    "address_extracted": res["extracted_fields"]["address_extracted"],
                    "address_confidence": res["extracted_fields"]["address_confidence"],
                    "factory_code_extracted": res["extracted_fields"]["factory_code_extracted"],
                    "factory_code_confidence": res["extracted_fields"]["factory_code_confidence"],
                },
                "preprocessing_meta": res["preprocessing_meta"],
                "preprocessing_latency_ms": res["preprocessing_latency_ms"],
                "ocr_inference_latency_ms": res["ocr_inference_latency_ms"],
                "latency_ms": res["latency_ms"],
            }
            mode_results.append(safe_record)
            raw_results.append(safe_record)

        elapsed = time.perf_counter() - t_mode_start
        print(f"Mode {mode} completed in {elapsed:.2f}s ({len(mode_results)} images)")

    # Assert immutability of input images
    for f in all_files:
        p = os.path.join(FIXTURES_DIR, f)
        with open(p, "rb") as fp:
            current_h = hashlib.sha256(fp.read()).hexdigest()
        assert current_h == initial_hashes[f], f"CRITICAL: Fixture {f} mutated during evaluation!"
    print("\n[VERIFIED] Fixture Immutability Check: All 15 SHA-256 hashes completely unchanged.")

    # Calculate Cohort-Level Aggregates
    summary_by_cohort_and_mode = {}
    cohort_keys = ["SYNTHETIC", "REAL_CARD_ALL", "REAL_CARD_JPEG", "REAL_CARD_WEBP"]

    for mode in MODES:
        summary_by_cohort_and_mode[mode] = {}
        for ckey in cohort_keys:
            if ckey == "REAL_CARD_ALL":
                records = [r for r in raw_results if r["mode"] == mode and r["cohort"] in ("REAL_CARD_JPEG", "REAL_CARD_WEBP")]
            else:
                records = [r for r in raw_results if r["mode"] == mode and r["cohort"] == ckey]

            n = len(records)
            if n == 0:
                continue

            nid_ext_cnt = sum(1 for r in records if r["extracted_fields"]["national_id_extracted"])
            nid_val_cnt = sum(1 for r in records if r["extracted_fields"]["national_id_valid_14d"])
            name_ext_cnt = sum(1 for r in records if r["extracted_fields"]["name_extracted"])
            addr_ext_cnt = sum(1 for r in records if r["extracted_fields"]["address_extracted"])
            fact_ext_cnt = sum(1 for r in records if r["extracted_fields"]["factory_code_extracted"])

            # Confidences (exclude missing fields)
            nid_confs = [r["extracted_fields"]["national_id_confidence"] for r in records if r["extracted_fields"]["national_id_extracted"] and r["extracted_fields"]["national_id_confidence"] > 0]
            name_confs = [r["extracted_fields"]["name_confidence"] for r in records if r["extracted_fields"]["name_extracted"] and r["extracted_fields"]["name_confidence"] > 0]
            addr_confs = [r["extracted_fields"]["address_confidence"] for r in records if r["extracted_fields"]["address_extracted"] and r["extracted_fields"]["address_confidence"] > 0]

            mean_prep_lat = sum(r["preprocessing_latency_ms"] for r in records) / n
            mean_ocr_lat = sum(r["ocr_inference_latency_ms"] for r in records) / n
            mean_tot_lat = sum(r["latency_ms"] for r in records) / n

            summary_by_cohort_and_mode[mode][ckey] = {
                "sample_count": n,
                "nid_extracted_count": nid_ext_cnt,
                "nid_extraction_rate_pct": round(nid_ext_cnt / n * 100.0, 1),
                "nid_valid_14d_count": nid_val_cnt,
                "nid_valid_14d_rate_pct": round(nid_val_cnt / n * 100.0, 1),
                "name_extracted_count": name_ext_cnt,
                "name_extraction_rate_pct": round(name_ext_cnt / n * 100.0, 1),
                "address_extracted_count": addr_ext_cnt,
                "address_extraction_rate_pct": round(addr_ext_cnt / n * 100.0, 1),
                "factory_code_extracted_count": fact_ext_cnt,
                "factory_code_extraction_rate_pct": round(fact_ext_cnt / n * 100.0, 1),
                "mean_nid_confidence": round(sum(nid_confs) / len(nid_confs), 4) if nid_confs else 0.0,
                "mean_name_confidence": round(sum(name_confs) / len(name_confs), 4) if name_confs else 0.0,
                "mean_address_confidence": round(sum(addr_confs) / len(addr_confs), 4) if addr_confs else 0.0,
                "mean_prep_latency_ms": round(mean_prep_lat, 2),
                "mean_ocr_latency_ms": round(mean_ocr_lat, 2),
                "mean_total_latency_ms": round(mean_tot_lat, 2),
            }

    # Save to JSON
    output_payload = {
        "metadata": {
            "title": "NileOps Phase 2.2 Controlled Computer Vision Preprocessing Ablation Study",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "device": "CPU",
            "total_samples": len(all_files),
            "modes_evaluated": MODES,
            "synthetic_samples": 4,
            "real_card_samples": 11,
        },
        "cohort_summaries": summary_by_cohort_and_mode,
        "raw_evaluations": raw_results,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fp:
        json.dump(output_payload, fp, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] Comprehensive ablation evaluation saved to: {OUTPUT_JSON}")

    # Print Formatted Comparison Table
    print("\n" + "=" * 100)
    print("PHASE 2.2 PREPROCESSING ABLATION RESULTS (REAL CARDS ALL, N=11)")
    print("=" * 100)
    print(f"{'Mode':<20} | {'NID Ext':<9} | {'NID Valid':<10} | {'Name Ext':<9} | {'Addr Ext':<9} | {'Prep ms':<9} | {'OCR ms':<9} | {'Total ms':<9}")
    print("-" * 100)
    for mode in MODES:
        s = summary_by_cohort_and_mode[mode]["REAL_CARD_ALL"]
        print(f"{mode:<20} | {s['nid_extracted_count']}/11 ({s['nid_extraction_rate_pct']}%) | {s['nid_valid_14d_count']}/11 ({s['nid_valid_14d_rate_pct']}%) | {s['name_extracted_count']}/11 ({s['name_extraction_rate_pct']}%) | {s['address_extracted_count']}/11 ({s['address_extraction_rate_pct']}%) | {s['mean_prep_latency_ms']:<9.2f} | {s['mean_ocr_latency_ms']:<9.2f} | {s['mean_total_latency_ms']:<9.2f}")

    print("\n" + "=" * 100)
    print("PHASE 2.2 PREPROCESSING ABLATION RESULTS (SYNTHETIC FIXTURES, N=4)")
    print("=" * 100)
    print(f"{'Mode':<20} | {'NID Ext':<9} | {'NID Valid':<10} | {'Name Ext':<9} | {'Addr Ext':<9} | {'Prep ms':<9} | {'OCR ms':<9} | {'Total ms':<9}")
    print("-" * 100)
    for mode in MODES:
        s = summary_by_cohort_and_mode[mode]["SYNTHETIC"]
        print(f"{mode:<20} | {s['nid_extracted_count']}/4 ({s['nid_extraction_rate_pct']}%)   | {s['nid_valid_14d_count']}/4 ({s['nid_valid_14d_rate_pct']}%)   | {s['name_extracted_count']}/4 ({s['name_extraction_rate_pct']}%)   | {s['address_extracted_count']}/4 ({s['address_extraction_rate_pct']}%)   | {s['mean_prep_latency_ms']:<9.2f} | {s['mean_ocr_latency_ms']:<9.2f} | {s['mean_total_latency_ms']:<9.2f}")
    print("=" * 100)

if __name__ == "__main__":
    run_ablation()
