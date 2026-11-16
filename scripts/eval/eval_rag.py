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
import time
from pathlib import Path
from typing import Any, Dict, List

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.rag import rag_service

DEV_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag_eval" / "rag_evaluation_set_40.json"
HELD_OUT_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag_eval" / "rag_evaluation_held_out_30.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "scratch" / "eval_rag_results.json"


async def run_evaluation(data_path: Path = DEV_DATA_PATH, output_file: Path = OUTPUT_PATH) -> Dict[str, Any]:
    if not data_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    benchmark_name = data_path.stem
    print(f"\n--- Running RAG Evaluation on '{benchmark_name}' ({len(questions)} Questions) ---")

    in_domain = [q for q in questions if not q.get("should_abstain", False)]
    out_domain = [q for q in questions if q.get("should_abstain", False)]

    results = []
    hit1_count = 0
    hit3_count = 0
    reciprocal_ranks = []
    latencies = []
    portal_leakage_count = 0

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

        t0 = time.time()
        res = await rag_service.retrieve_and_generate(
            query=q_text,
            portal_type=portal,
            language=lang,
        )
        t_elapsed = time.time() - t0
        latencies.append(t_elapsed)

        abstained = res.get("abstained", False)
        citations = res.get("citations", [])
        citation_codes = [c["code"] for c in citations]

        # Check for cross-portal isolation / leakage
        if portal == "customer":
            for c in citations:
                if c.get("portal_access") == "employee":
                    portal_leakage_count += 1

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
                fp_abs += 1
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
            "latency_ms": round(t_elapsed * 1000, 2),
            "should_abstain": should_abstain,
            "abstained": abstained,
            "expected_policy": expected_policy,
            "citations": citation_codes,
            "rank": rank,
            "hit1": is_hit1,
            "hit3": is_hit3,
        })

    n_in = len(in_domain)
    n_out = len(out_domain)

    grounded_answer_rate = (hit1_count / n_in * 100.0) if n_in > 0 else 0.0
    hit3_rate = (hit3_count / n_in * 100.0) if n_in > 0 else 0.0
    mrr = (sum(reciprocal_ranks) / n_in) if n_in > 0 else 0.0
    avg_latency_ms = (sum(latencies) / len(latencies) * 1000.0) if latencies else 0.0

    abstention_recall = (tp_abs / n_out * 100.0) if n_out > 0 else 0.0
    abstention_precision = (tp_abs / (tp_abs + fp_abs) * 100.0) if (tp_abs + fp_abs) > 0 else 0.0
    abstention_f1 = (
        (2 * abstention_precision * abstention_recall / (abstention_precision + abstention_recall))
        if (abstention_precision + abstention_recall) > 0
        else 0.0
    )

    summary = {
        "benchmark_name": benchmark_name,
        "sample_size": len(questions),
        "in_domain_samples": n_in,
        "out_of_domain_samples": n_out,
        "metrics": {
            "grounded_answer_rate_pct": round(grounded_answer_rate, 2),
            "hit3_rate_pct": round(hit3_rate, 2),
            "mrr": round(mrr, 4),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "portal_leakage_count": portal_leakage_count,
            "correct_abstention_rate_pct": round(abstention_recall, 2),
            "abstention_precision_pct": round(abstention_precision, 2),
            "abstention_f1_pct": round(abstention_f1, 2),
        },
        "targets": {
            "grounded_answer_rate_target": ">= 90.0%",
            "grounded_answer_status": "MET" if grounded_answer_rate >= 90.0 else "NOT MET",
            "abstention_rate_target": ">= 90.0%",
            "abstention_status": "MET" if abstention_recall >= 90.0 else "NOT MET",
            "portal_leakage_status": "MET" if portal_leakage_count == 0 else "FAIL",
            "latency_status": "MET" if avg_latency_ms < 1000.0 else "NOT MET",
        },
        "confusion_matrix_abstention": {
            "true_positives": tp_abs,
            "false_negatives": fn_abs,
            "false_positives": fp_abs,
            "true_negatives": tn_abs,
        },
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)

    print(f"\n--- RAG Evaluation Summary ({benchmark_name}) ---")
    print(f"Sample Size: {len(questions)} (In-Domain: {n_in}, Out-of-Domain: {n_out})")
    print(f"Grounded Answer Rate (Hit@1): {grounded_answer_rate:.1f}% (Target: >=90.0%) -> {summary['targets']['grounded_answer_status']}")
    print(f"Hit@3 Rate:                 {hit3_rate:.1f}%")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
    print(f"Avg Latency:                {avg_latency_ms:.1f}ms (Target: <1000ms) -> {summary['targets']['latency_status']}")
    print(f"Portal Leakage:             {portal_leakage_count} (Target: 0) -> {summary['targets']['portal_leakage_status']}")
    print(f"Correct Abstention Rate:    {abstention_recall:.1f}% (Target: >=90.0%) -> {summary['targets']['abstention_status']}")
    print(f"Abstention Precision:       {abstention_precision:.1f}%")
    print(f"Abstention F1:              {abstention_f1:.1f}%")

    return summary


async def main():
    dev_summary = await run_evaluation(DEV_DATA_PATH, OUTPUT_PATH)
    held_out_summary = await run_evaluation(
        HELD_OUT_DATA_PATH,
        Path(__file__).resolve().parent.parent.parent / "scratch" / "eval_rag_held_out_results.json",
    )
    return dev_summary, held_out_summary


if __name__ == "__main__":
    asyncio.run(main())
