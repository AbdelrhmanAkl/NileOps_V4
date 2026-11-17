import os
import sys
import json
import time
import re
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_DATA = os.path.join(REPO_ROOT, "data")
os.environ["PADDLE_PDX_CACHE_HOME"] = os.path.join(WORKSPACE_DATA, "paddlex")
os.environ["PADDLE_HOME"] = os.path.join(WORKSPACE_DATA, "paddle")
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"

sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from app.services.image_pipeline import (
    get_ocr_engine,
    ImageOCRPipeline,
    ADMINISTRATIVE_HEADERS,
    EASTERN_TO_WESTERN,
    ReviewRoutingStatus,
)

def levenshtein_distance(s1: str, s2: str) -> int:
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1] * (len(s2) + 1)
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr[j + 1] = min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost)
        prev = curr
    return prev[len(s2)]

def normalize_text_for_eval(txt: Optional[str]) -> str:
    if not txt:
        return ""
    # Strip punctuation, normalize multiple whitespace
    clean = re.sub(r"[^\w\s\u0600-\u06FF]", " ", txt)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def compute_cer(gt: str, pred: Optional[str]) -> float:
    n_gt = normalize_text_for_eval(gt)
    n_pred = normalize_text_for_eval(pred)
    if not n_gt:
        return 0.0 if not n_pred else 1.0
    if not n_pred:
        return 1.0
    return min(1.0, levenshtein_distance(n_gt, n_pred) / float(len(n_gt)))

def compute_em(gt: str, pred: Optional[str]) -> int:
    n_gt = normalize_text_for_eval(gt)
    n_pred = normalize_text_for_eval(pred)
    return 1 if (n_gt and n_pred and n_gt == n_pred) else 0

CARD_FIELD_LABELS = {
    "الاسم", "الاسم:", "اسم", "العنوان", "العنوان:", "عنوان",
    "الرقم القومي", "الرقم القومي:", "الرقم", "الرقم:", "مهنة", "المهنة", "الوظيفة",
    "تحقيق الشخصية", "بطاقة تحقيق الشخصية"
}

def tuned_extract_fields(
    pipeline: ImageOCRPipeline,
    rec_texts: List[str],
    rec_scores: List[float],
) -> Dict[str, Any]:
    """Tuned field extraction with label filtering, address disambiguation, and clean token joining."""
    extracted = {
        "national_id": None,
        "national_id_conf": 0.0,
        "factory_code": None,
        "factory_code_conf": 0.0,
        "name": None,
        "name_conf": 0.0,
        "address": None,
        "address_conf": 0.0,
        "raw_tokens": [],
    }

    name_candidates = []
    address_candidates = []

    for text, score in zip(rec_texts, rec_scores):
        raw = text.strip()
        if not raw:
            continue
        extracted["raw_tokens"].append({"text": raw, "score": float(score)})

        # 1. 14-Digit National ID Extraction
        norm = raw.translate(EASTERN_TO_WESTERN)
        digits = re.sub(r"[^\d]", "", norm)

        if len(digits) == 14:
            if digits[0] in ("2", "3"):
                candidate_nid = digits
            elif digits[-1] in ("2", "3"):
                candidate_nid = digits[::-1]
            else:
                candidate_nid = digits

            if extracted["national_id"] is None or score > extracted["national_id_conf"]:
                extracted["national_id"] = candidate_nid
                extracted["national_id_conf"] = float(score)

        # 2. Factory Code
        fc_match = re.search(r"([A-Za-z]{1,2}\s*\d{6,8}[A-Za-z]{0,2}|\d{5,8}\s*[A-Za-z]{1,2})", norm)
        if fc_match:
            cand_fc = re.sub(r"\s+", "", fc_match.group(1)).upper()
            if extracted["factory_code"] is None or score > extracted["factory_code_conf"]:
                extracted["factory_code"] = cand_fc
                extracted["factory_code_conf"] = float(score)

        # 3. Filter Administrative Headers & Field Labels
        if any(h in raw for h in ADMINISTRATIVE_HEADERS):
            continue

        raw_clean = re.sub(r"[:\-\s]", "", raw)
        if raw in CARD_FIELD_LABELS or raw_clean in CARD_FIELD_LABELS:
            continue

        # 4. Arabic Name vs Address Separation
        has_arabic = any("\u0600" <= c <= "\u06FF" for c in raw)
        if not has_arabic:
            continue

        if pipeline.is_likely_address(raw, has_prior_address=bool(address_candidates)):
            address_candidates.append((raw, float(score)))
        elif len(digits) < 5:
            # Clean off any residual leading label e.g. "الاسم : "
            cleaned_token = re.sub(r"^(الاسم|اسم)\s*[:\-]\s*", "", raw).strip()
            if cleaned_token and cleaned_token not in CARD_FIELD_LABELS:
                name_candidates.append((cleaned_token, float(score)))

    if name_candidates:
        extracted["name"] = " ".join(t[0] for t in name_candidates)
        extracted["name_conf"] = sum(t[1] for t in name_candidates) / len(name_candidates)

    if address_candidates:
        extracted["address"] = " ".join(t[0] for t in address_candidates)
        extracted["address_conf"] = sum(t[1] for t in address_candidates) / len(address_candidates)

    return extracted

def run_evaluation_suite():
    manifest_path = r"c:\AI\NileOps_V4\data\synthetic_cards\manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Loaded manifest with {len(manifest)} cards.")
    pipeline = ImageOCRPipeline()
    ocr = get_ocr_engine()

    eval_results = []
    chunk_size = 5
    n_chunks = (len(manifest) + chunk_size - 1) // chunk_size

    t_suite_start = time.perf_counter()

    for chunk_idx in range(n_chunks):
        t_chunk_start = time.perf_counter()
        start_i = chunk_idx * chunk_size
        end_i = min(start_i + chunk_size, len(manifest))
        chunk_items = manifest[start_i:end_i]

        print(f"\n=================== PROCESSING CHUNK {chunk_idx + 1}/{n_chunks} (Cards {start_i+1} to {end_i}) ===================")

        for item in chunk_items:
            cid = item["card_id"]
            cond = item["condition"]
            gt = item["ground_truth"]
            card_file = os.path.join(r"c:\AI\NileOps_V4\data\synthetic_cards", item["filename"])

            t_card_start = time.perf_counter()

            # 1. Pipeline processing (standard ingestion)
            img, meta = pipeline.load_and_validate_image(card_file)
            if not meta["is_valid"]:
                print(f"[{cid}] Ingestion failure: {meta['error']}")
                eval_results.append({
                    "card_id": cid,
                    "condition": cond,
                    "ingestion_pass": False,
                    "baseline": {"em_id": 0, "em_name": 0, "em_addr": 0, "em_fc": 0, "requires_review": True},
                    "tuned": {"em_id": 0, "em_name": 0, "em_addr": 0, "em_fc": 0, "requires_review": True},
                })
                continue

            # Run OCR Predict
            results = ocr.predict(img)
            res = results[0] if results else {}
            rec_texts = res.get("rec_texts", [])
            rec_scores = res.get("rec_scores", [])

            # Baseline field extraction
            b_fields = pipeline.extract_fields_from_ocr(rec_texts, rec_scores)
            # Full baseline decision routing
            b_full = pipeline.process_image(card_file, case_id=f"EVAL_B_{cid}")

            # Tuned field extraction
            t_fields = tuned_extract_fields(pipeline, rec_texts, rec_scores)

            # Masked National ID for safe logging
            gt_masked = gt["masked_id"]
            b_id_masked = pipeline.validator.mask_id(b_fields.get("national_id")) if b_fields.get("national_id") else "****"
            t_id_masked = pipeline.validator.mask_id(t_fields.get("national_id")) if t_fields.get("national_id") else "****"

            # Compute Baseline Metrics
            b_em_id = 1 if b_fields.get("national_id") == gt["national_id"] else 0
            b_em_name = compute_em(gt["name"], b_fields.get("name"))
            b_em_addr = compute_em(gt["address"], b_fields.get("address"))
            b_em_fc = 1 if b_fields.get("factory_code") == gt["factory_code"] else 0

            b_cer_id = compute_cer(gt["national_id"], b_fields.get("national_id"))
            b_cer_name = compute_cer(gt["name"], b_fields.get("name"))
            b_cer_addr = compute_cer(gt["address"], b_fields.get("address"))
            b_cer_fc = compute_cer(gt["factory_code"], b_fields.get("factory_code"))

            b_req_review = (b_full.get("review_status") == ReviewRoutingStatus.REQUIRES_HUMAN_REVIEW)

            # Compute Tuned Metrics
            t_em_id = 1 if t_fields.get("national_id") == gt["national_id"] else 0
            t_em_name = compute_em(gt["name"], t_fields.get("name"))
            t_em_addr = compute_em(gt["address"], t_fields.get("address"))
            t_em_fc = 1 if t_fields.get("factory_code") == gt["factory_code"] else 0

            t_cer_id = compute_cer(gt["national_id"], t_fields.get("national_id"))
            t_cer_name = compute_cer(gt["name"], t_fields.get("name"))
            t_cer_addr = compute_cer(gt["address"], t_fields.get("address"))
            t_cer_fc = compute_cer(gt["factory_code"], t_fields.get("factory_code"))

            # Tuned Review Routing Logic:
            # If NID missing or conf < 0.80 or Name missing or Addr missing -> Requires review
            t_req_review = (
                (t_fields.get("national_id") is None)
                or (t_fields.get("national_id_conf", 0.0) < 0.80)
                or (t_fields.get("name") is None)
                or (t_fields.get("address") is None)
            )

            card_dur = time.perf_counter() - t_card_start

            print(f"[{cid:28s} | {cond:20s}] in {card_dur:.2f}s | "
                  f"ID: {t_id_masked} (EM:{t_em_id}) | Name EM: B={b_em_name}/T={t_em_name} (CER:{t_cer_name:.2f}) | "
                  f"Addr CER:{t_cer_addr:.2f} | Rev: {'REVIEW' if t_req_review else 'PASS'}")

            eval_results.append({
                "card_id": cid,
                "condition": cond,
                "gt_masked_id": gt_masked,
                "latency_sec": round(card_dur, 2),
                "baseline": {
                    "extracted_id_masked": b_id_masked,
                    "name": b_fields.get("name"),
                    "address": b_fields.get("address"),
                    "factory_code": b_fields.get("factory_code"),
                    "em_id": b_em_id,
                    "em_name": b_em_name,
                    "em_addr": b_em_addr,
                    "em_fc": b_em_fc,
                    "cer_id": round(b_cer_id, 4),
                    "cer_name": round(b_cer_name, 4),
                    "cer_addr": round(b_cer_addr, 4),
                    "cer_fc": round(b_cer_fc, 4),
                    "requires_review": b_req_review,
                },
                "tuned": {
                    "extracted_id_masked": t_id_masked,
                    "name": t_fields.get("name"),
                    "address": t_fields.get("address"),
                    "factory_code": t_fields.get("factory_code"),
                    "em_id": t_em_id,
                    "em_name": t_em_name,
                    "em_addr": t_em_addr,
                    "em_fc": t_em_fc,
                    "cer_id": round(t_cer_id, 4),
                    "cer_name": round(t_cer_name, 4),
                    "cer_addr": round(t_cer_addr, 4),
                    "cer_fc": round(t_cer_fc, 4),
                    "requires_review": t_req_review,
                }
            })

        chunk_dur = time.perf_counter() - t_chunk_start
        print(f"Chunk {chunk_idx + 1} completed in {chunk_dur:.1f} s ({chunk_dur/60.0:.2f} min).")

    total_dur = time.perf_counter() - t_suite_start
    print(f"\n=================== EVALUATION COMPLETE ({total_dur:.1f} s / {total_dur/60.0:.2f} min) ===================")

    # Save raw JSON
    out_json = os.path.join(WORKSPACE_DATA, "ocr_evaluation_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"total_duration_sec": total_dur, "results": eval_results}, f, ensure_ascii=False, indent=2)
    print(f"Saved evaluation results to {out_json}")

if __name__ == "__main__":
    run_evaluation_suite()

