"""NileOps Handbook Evaluation — RAG Grounded Answer & Abstention Benchmark.

Evaluates RAG performance across the standard 40-question benchmark:
- 25 In-domain policy questions (Arabic & English across retail and KYC policies)
- 15 Out-of-domain questions (general knowledge, coding, medical, financial speculation)

Metrics computed:
- Grounded-Answer Rate (Hit@1) on in-domain questions (Handbook Target: >= 90.0%)
- Correct Abstention Rate on out-of-domain questions (Handbook Target: >= 90.0%)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.rag import rag_service

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag_eval" / "rag_evaluation_set_40.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "scratch" / "eval_rag_results.json"


async def run_evaluation() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    print(f"--- Running RAG Evaluation on {len(questions)} Questions (AR + EN) ---")

    in_domain = [q for q in questions if not q.get("should_abstain", False)]
    out_domain = [q for q in questions if q.get("should_abstain", False)]

    results = []
    hit1_count = 0
    hit3_count = 0
    reciprocal_ranks = []

    # Abstention confusion matrix: Positive = Abstain, Negative = Answer
    tp_abs = 0  # Out-domain and correctly abstained
    fn_abs = 0  # Out-domain but gave an answer
    fp_abs = 0  # In-domain but abstained
    tn_abs = 0  # In-domain and gave an answer

    for idx, item in enumerate(questions, start=1):
        q_text = item["question"]
        lang = item.get("language", "ar")
        portal = item.get("portal", "customer")
        expected_policy = item.get("expected_policy")
        should_abstain = item.get("should_abstain", False)

        res = await rag_service.retrieve_and_generate(
            query=q_text,
            portal_type=portal,
            language=lang,
        )

        abstained = res.get("abstained", False)
        citations = res.get("citations", [])
        citation_codes = [c["code"] for c in citations]

        is_hit1 = False
        is_hit3 = False
        rank = None

        if not should_abstain:
            # In-domain evaluation
            if expected_policy in citation_codes:
                rank = citation_codes.index(expected_policy) + 1
                if rank == 1:
                    is_hit1 = True
                    is_hit3 = True
                    hit1_count += 1
                    hit3_count += 1
                    reciprocal_ranks.append(1.0)
                elif rank in (2, 3):
                    is_hit3 = True
                    hit3_count += 1
                    reciprocal_ranks.append(1.0 / rank)
                else:
                    reciprocal_ranks.append(0.0)
            else:
                reciprocal_ranks.append(0.0)

            if abstained:
                fp_abs += 1  # False positive for abstention
            else:
                tn_abs += 1
        else:
            # Out-domain evaluation
            if abstained:
                tp_abs += 1
            else:
                fn_abs += 1

        results.append({
            "id": item.get("id", f"Q{idx:02d}"),
            "question": q_text,
            "language": lang,
            "portal": portal,
            "should_abstain": should_abstain,
            "abstained": abstained,
            "expected_policy": expected_policy,
            "citations": citation_codes,
            "rank": rank,
            "hit1": is_hit1,
            "hit3": is_hit3,
        })

    # Calculations
    n_in = len(in_domain)
    n_out = len(out_domain)

    grounded_answer_rate = (hit1_count / n_in * 100.0) if n_in > 0 else 0.0
    hit3_rate = (hit3_count / n_in * 100.0) if n_in > 0 else 0.0
    mrr = (sum(reciprocal_ranks) / n_in) if n_in > 0 else 0.0

    abstention_recall = (tp_abs / n_out * 100.0) if n_out > 0 else 0.0
    abstention_precision = (tp_abs / (tp_abs + fp_abs) * 100.0) if (tp_abs + fp_abs) > 0 else 0.0
    abstention_f1 = (
        (2 * abstention_precision * abstention_recall / (abstention_precision + abstention_recall))
        if (abstention_precision + abstention_recall) > 0
        else 0.0
    )

    summary = {
        "benchmark_name": "40_question_rag_benchmark",
        "sample_size": len(questions),
        "in_domain_samples": n_in,
        "out_of_domain_samples": n_out,
        "metrics": {
            "grounded_answer_rate_pct": round(grounded_answer_rate, 2),
            "hit3_rate_pct": round(hit3_rate, 2),
            "mrr": round(mrr, 4),
            "correct_abstention_rate_pct": round(abstention_recall, 2),
            "abstention_precision_pct": round(abstention_precision, 2),
            "abstention_f1_pct": round(abstention_f1, 2),
        },
        "targets": {
            "grounded_answer_rate_target": ">= 90.0%",
            "grounded_answer_status": "MET" if grounded_answer_rate >= 90.0 else "NOT MET",
            "abstention_rate_target": ">= 90.0%",
            "abstention_status": "MET" if abstention_recall >= 90.0 else "NOT MET",
        },
        "confusion_matrix_abstention": {
            "true_positives": tp_abs,
            "false_negatives": fn_abs,
            "false_positives": fp_abs,
            "true_negatives": tn_abs,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)

    print("\n--- RAG Evaluation Summary ---")
    print(f"Sample Size: {len(questions)} (In-Domain: {n_in}, Out-of-Domain: {n_out})")
    print(f"Grounded Answer Rate (Hit@1): {grounded_answer_rate:.1f}% (Target: >=90.0%) -> {summary['targets']['grounded_answer_status']}")
    print(f"Hit@3 Rate:                 {hit3_rate:.1f}%")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
    print(f"Correct Abstention Rate:    {abstention_recall:.1f}% (Target: >=90.0%) -> {summary['targets']['abstention_status']}")
    print(f"Abstention Precision:       {abstention_precision:.1f}%")
    print(f"Abstention F1:              {abstention_f1:.1f}%")

    return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
