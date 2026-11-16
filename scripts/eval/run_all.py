"""Master Benchmark Runner for NileOps Handbook KPI Evaluations.

Executes all 4 evaluations in sequence:
1. RAG Grounded Answer & Abstention Benchmark (40 questions, AR + EN)
2. Exception Detection Recall & Escalation Correctness Benchmark (30 cards)
3. OCR Per-Field Extraction F1 Benchmark (40 cards across 4 conditions)
4. Audit Chain Completeness Benchmark (PostgreSQL relational entities)
"""

import asyncio
import os
import sys
from pathlib import Path

scripts_eval_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_eval_dir))

import eval_rag
import eval_exceptions
import eval_ocr_extraction
import eval_audit_completeness


async def main():
    print("=================================================================")
    print("       NileOps Digital Banking Handbook KPI Evaluation Suite     ")
    print("=================================================================\n")

    print("[1/4] Running RAG Evaluation Benchmark...")
    rag_summary = await eval_rag.run_evaluation()

    print("\n[2/4] Running Exception Detection Recall Benchmark...")
    exc_summary = eval_exceptions.run_evaluation()

    print("\n[3/4] Running OCR Per-Field Extraction Benchmark...")
    ocr_summary = eval_ocr_extraction.run_evaluation()

    print("\n[4/4] Running Audit Completeness Benchmark...")
    audit_summary = await eval_audit_completeness.run_evaluation()

    print("\n=================================================================")
    print("                    AGGREGATED KPI RESULTS TABLE                 ")
    print("=================================================================")
    print(f"{'Metric':<35} | {'Target':<15} | {'Measured':<12} | {'Sample':<8} | {'Status':<8}")
    print("-" * 88)
    
    r_m = rag_summary["metrics"]
    e_m = exc_summary["metrics"]
    o_m = ocr_summary["metrics"]
    a_m = audit_summary["metrics"]

    print(f"{'RAG Grounded-Answer Rate (Hit@1)':<35} | {'>= 90.0%':<15} | {r_m['grounded_answer_rate_pct']:>5.1f}%      | {rag_summary['in_domain_samples']:<8} | {rag_summary['targets']['grounded_answer_status']:<8}")
    print(f"{'RAG Correct Abstention Rate':<35} | {'>= 90.0%':<15} | {r_m['correct_abstention_rate_pct']:>5.1f}%      | {rag_summary['out_of_domain_samples']:<8} | {rag_summary['targets']['abstention_status']:<8}")
    print(f"{'Exception Detection Recall':<35} | {'>= 95.0%':<15} | {e_m['exception_recall_pct']:>5.1f}%      | {exc_summary['sample_size']:<8} | {exc_summary['targets']['exception_recall_status']:<8}")
    print(f"{'Correct Escalation Rate':<35} | {'>= 95.0%':<15} | {e_m['correct_escalation_rate_pct']:>5.1f}%      | {exc_summary['sample_size']:<8} | {exc_summary['targets']['escalation_rate_status']:<8}")
    print(f"{'OCR National ID Field F1':<35} | {'>= 90.0%':<15} | {o_m['national_id_f1_pct']:>5.1f}%      | {ocr_summary['sample_size']:<8} | {ocr_summary['targets']['national_id_status']:<8}")
    print(f"{'OCR Citizen Name Field F1':<35} | {'>= 90.0%':<15} | {o_m['name_f1_pct']:>5.1f}%      | {ocr_summary['sample_size']:<8} | {ocr_summary['targets']['name_status']:<8}")
    print(f"{'OCR Residential Address Field F1':<35} | {'>= 90.0%':<15} | {o_m['address_f1_pct']:>5.1f}%      | {ocr_summary['sample_size']:<8} | {ocr_summary['targets']['address_status']:<8}")
    print(f"{'Audit Chain Completeness':<35} | {'100.0%':<15} | {a_m['audit_completeness_pct']:>5.1f}%      | {audit_summary['total_decisions_evaluated']:<8} | {audit_summary['targets']['status']:<8}")
    print("=================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
