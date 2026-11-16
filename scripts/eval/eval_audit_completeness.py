"""NileOps Handbook Evaluation — Audit Completeness Benchmark.

Verifies end-to-end audit completeness across operational entities:
- Terminal-state account requests & card requests having reviewer_id and timestamp
- Correlation with immutable AuditLog records in PostgreSQL
- Zero orphaned decisions or state changes without audit records

Handbook Target: 100.0% Audit Completeness
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.db.session import async_session_maker
from app.models.audit import AuditLog
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.kyc import KycVerification
from app.models.complaint import Complaint

OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "scratch" / "eval_audit_results.json"


async def run_evaluation() -> Dict[str, Any]:
    print("--- Evaluating Audit Chain Completeness against PostgreSQL ---")

    async with async_session_maker() as session:
        # 1. Total audit logs
        total_logs = await session.scalar(select(func.count(AuditLog.id)))

        # 2. Terminal requests evaluation
        acct_stmt = select(AccountOpeningRequest)
        accts = (await session.execute(acct_stmt)).scalars().all()

        card_stmt = select(CardRequest)
        cards = (await session.execute(card_stmt)).scalars().all()

        terminal_states = {"APPROVED_SIMULATED", "REJECTED", "SIMULATED_COMPLETED"}
        terminal_requests = [r for r in accts if r.status in terminal_states] + [
            r for r in cards if r.status in terminal_states
        ]

        # 3. Check for immutable audit log presence per request
        audited_count = 0
        missing_audit_ids = []

        for req in terminal_requests:
            has_reviewer = bool(req.reviewer_id)
            has_reviewed_at = req.reviewed_at is not None
            has_decision = bool(req.status in terminal_states)

            # Query audit table for matching resource record
            audit_records = (await session.execute(
                select(AuditLog).where(AuditLog.resource_id == req.id)
            )).scalars().all()

            if has_reviewer and has_reviewed_at and has_decision and len(audit_records) > 0:
                audited_count += 1
            else:
                missing_audit_ids.append(req.id)

        # 4. KYC records audit verification
        kyc_records = (await session.execute(select(KycVerification))).scalars().all()
        reviewed_kyc = [k for k in kyc_records if k.status in {"APPROVED_SIMULATED", "REJECTED", "MORE_INFO_REQUESTED"}]
        kyc_audited = 0
        for k in reviewed_kyc:
            audit_k = (await session.execute(
                select(AuditLog).where(AuditLog.resource_id == k.id)
            )).scalars().all()
            if len(audit_k) > 0 and k.reviewed_by_id is not None:
                kyc_audited += 1

        total_evaluated = len(terminal_requests) + len(reviewed_kyc)
        total_passed = audited_count + kyc_audited

        if total_evaluated > 0:
            completeness_rate = (total_passed / total_evaluated) * 100.0
        else:
            completeness_rate = 100.0

        target = "100.0%"
        status = "MET" if completeness_rate >= 100.0 else "NOT MET"

        summary = {
            "benchmark_name": "database_audit_completeness_benchmark",
            "total_audit_logs_in_database": total_logs,
            "terminal_requests_evaluated": len(terminal_requests),
            "terminal_requests_fully_audited": audited_count,
            "reviewed_kyc_evaluated": len(reviewed_kyc),
            "reviewed_kyc_audited": kyc_audited,
            "total_decisions_evaluated": total_evaluated,
            "total_decisions_fully_audited": total_passed,
            "metrics": {
                "audit_completeness_pct": round(completeness_rate, 2),
            },
            "targets": {
                "handbook_target": target,
                "status": status,
            },
            "missing_audit_ids": missing_audit_ids,
        }

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"Total Audit Logs in DB: {total_logs}")
        print(f"Terminal Requests Evaluated: {len(terminal_requests)} (Audited: {audited_count})")
        print(f"Reviewed KYC Evaluated:      {len(reviewed_kyc)} (Audited: {kyc_audited})")
        print(f"Audit Completeness Rate:     {completeness_rate:.1f}% (Target: 100.0%) -> {status}")

        return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
