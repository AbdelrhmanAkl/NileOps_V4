"""Analyze 100-question Dev Pool Distributions & Baseline Performance.

Pool: DEV (40) + HELD-OUT 1 (30) + HELD-OUT 2 (30) = 100 Questions.
Stratified: 70 In-Domain, 30 Out-of-Domain.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

repo_root = Path(__file__).resolve().parent.parent.parent
backend_dir = repo_root / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.embedding import embedding_service
from app.services.vector_store import qdrant_service
from app.services.query_normalizer import normalize_colloquial_query

from app.services.lexical_support import compute_lexical_containment

def compute_lexical_overlap(query: str, doc_text: str) -> float:
    return compute_lexical_containment(query, doc_text)


async def collect_pool_data() -> List[Dict[str, Any]]:
    paths = [
        repo_root / "data" / "rag_eval" / "rag_evaluation_set_40.json",
        repo_root / "data" / "rag_eval" / "rag_evaluation_held_out_30.json",
        repo_root / "data" / "rag_eval" / "rag_evaluation_new_held_out_30.json",
    ]
    all_questions = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                item["source_file"] = p.stem
                all_questions.append(item)

    print(f"Total questions in dev pool: {len(all_questions)}")

    records = []
    for item in all_questions:
        q_text = item["question"]
        lang = item.get("language", "ar")
        portal = item.get("portal", "customer")
        should_abstain = item.get("should_abstain", False)
        expected = item.get("expected_policy")

        normalized_query = normalize_colloquial_query(q_text)
        # Search Qdrant with threshold 0.0 and limit 10 to inspect full candidate distribution
        hits = await qdrant_service.search(
            query=normalized_query,
            portal_type=portal,
            limit=10,
            score_threshold=0.0,
        )

        scores = [h["score"] for h in hits]
        codes = [h["code"] for h in hits]

        top1 = scores[0] if len(scores) >= 1 else 0.0
        top2 = scores[1] if len(scores) >= 2 else 0.0
        margin1_2 = top1 - top2
        margin1_mean10 = top1 - float(np.mean(scores)) if scores else 0.0

        top1_code = hits[0].get("code") if hits else None
        # Combine content across hits matching the top candidate policy code
        top_doc_content = " ".join([h.get("content", "") for h in hits if h.get("code") == top1_code])
        lexical_support = compute_lexical_containment(q_text, top_doc_content)

        rank = codes.index(expected) + 1 if expected in codes else None
        hit1 = (rank == 1) if not should_abstain else False
        hit3 = (rank is not None and rank <= 3) if not should_abstain else False

        records.append({
            "id": item.get("id"),
            "question": q_text,
            "language": lang,
            "portal": portal,
            "should_abstain": should_abstain,
            "expected_policy": expected,
            "source_file": item["source_file"],
            "top1_score": top1,
            "top2_score": top2,
            "margin1_2": margin1_2,
            "margin1_mean10": margin1_mean10,
            "lexical_support": lexical_support,
            "citations": codes,
            "hit1": hit1,
            "hit3": hit3,
            "rank": rank,
        })
    return records


def print_distributions(records: List[Dict[str, Any]]):
    in_domain = [r for r in records if not r["should_abstain"]]
    out_domain = [r for r in records if r["should_abstain"]]

    in_ar = [r for r in in_domain if r["language"] == "ar"]
    in_en = [r for r in in_domain if r["language"] == "en"]
    out_ar = [r for r in out_domain if r["language"] == "ar"]
    out_en = [r for r in out_domain if r["language"] == "en"]

    print("\n" + "=" * 75)
    print("      POOL COMPOSITION (N=100)")
    print("=" * 75)
    print(f"Total In-Domain:     {len(in_domain):>2} (Arabic: {len(in_ar):>2}, English: {len(in_en):>2})")
    print(f"Total Out-of-Domain: {len(out_domain):>2} (Arabic: {len(out_ar):>2}, English: {len(out_en):>2})")

    def stats(vals):
        return {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "p50": float(np.median(vals)),
            "max": float(np.max(vals)),
        }

    groups = [
        ("In-Domain Overall", [r["top1_score"] for r in in_domain]),
        ("  In-Domain Arabic", [r["top1_score"] for r in in_ar]),
        ("  In-Domain English", [r["top1_score"] for r in in_en]),
        ("Out-of-Domain Overall", [r["top1_score"] for r in out_domain]),
        ("  Out-of-Domain Arabic", [r["top1_score"] for r in out_ar]),
        ("  Out-of-Domain English", [r["top1_score"] for r in out_en]),
    ]

    print("\n" + "=" * 75)
    print(f"{'Group':<24} | {'N':<3} | {'Mean':<6} | {'Std':<6} | {'Min':<6} | {'Median':<6} | {'Max':<6}")
    print("-" * 75)
    for name, v in groups:
        s = stats(v)
        print(f"{name:<24} | {len(v):<3} | {s['mean']:.4f} | {s['std']:.4f} | {s['min']:.4f} | {s['p50']:.4f} | {s['max']:.4f}")

    print("\n" + "=" * 75)
    print("      FEATURE COMPARISONS: IN-DOMAIN vs OUT-OF-DOMAIN")
    print("=" * 75)
    for feat in ["top1_score", "margin1_2", "margin1_mean10", "lexical_support"]:
        in_v = [r[feat] for r in in_domain]
        out_v = [r[feat] for r in out_domain]
        print(f"Feature: {feat:<16} | In-Domain Mean: {np.mean(in_v):.4f} (std: {np.std(in_v):.4f}) | Out-Domain Mean: {np.mean(out_v):.4f} (std: {np.std(out_v):.4f})")

    # Current absolute threshold 0.75 behavior
    curr_tp = sum(1 for r in out_domain if r["top1_score"] < 0.75)
    curr_fn = sum(1 for r in out_domain if r["top1_score"] >= 0.75)
    curr_fp = sum(1 for r in in_domain if r["top1_score"] < 0.75)
    curr_tn = sum(1 for r in in_domain if r["top1_score"] >= 0.75)

    curr_rec = curr_tp / len(out_domain) * 100.0
    curr_prec = curr_tp / (curr_tp + curr_fp) * 100.0 if (curr_tp + curr_fp) > 0 else 0.0
    curr_hit1 = sum(1 for r in in_domain if r["hit1"] and r["top1_score"] >= 0.75) / len(in_domain) * 100.0

    print("\n" + "=" * 75)
    print("      CURRENT BASELINE (RAG_SIMILARITY_THRESHOLD = 0.75)")
    print("=" * 75)
    print(f"Hit@1 Rate:              {curr_hit1:.1f}% ({sum(1 for r in in_domain if r['hit1'] and r['top1_score'] >= 0.75)}/{len(in_domain)})")
    print(f"Abstention Recall:       {curr_rec:.1f}% ({curr_tp}/{len(out_domain)})")
    print(f"Abstention Precision:    {curr_prec:.1f}% ({curr_tp}/{curr_tp + curr_fp})")
    print(f"False Abstentions (in):  {curr_fp}/{len(in_domain)} ({curr_fp / len(in_domain) * 100.0:.1f}%)")
    print(f"Failed Abstentions (out):{curr_fn}/{len(out_domain)} ({curr_fn / len(out_domain) * 100.0:.1f}%)")


async def main():
    records = await collect_pool_data()
    print_distributions(records)

    # Save cached records for CV training
    cache_path = repo_root / "scratch" / "pool_features_100.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\nSaved feature cache to {cache_path}")


if __name__ == "__main__":
    asyncio.run(main())
