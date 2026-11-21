"""NileOps Demo Data Reset Script.

Restores development database ('nileops') to its pristine seed state:
1. Hard-safeguarded to NEVER touch 'nileops_test'.
2. Purges temporary requests, complaints, KYC verifications, audit records, and demo uploads.
3. Re-seeds canonical staff accounts, customer profiles, initial balances, and policies.
4. Reconciles Qdrant 'nileops_kb' vector index.
"""

import asyncio
import os
from pathlib import Path
import shutil
import sys
import urllib.parse
from sqlalchemy import delete, select, text

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.api.v1.auth import seed_demo_data
from app.core.config import settings
from app.db.session import async_session_maker, engine
from app.models.banking import Account, Transaction
from app.models.audit import AuditLog
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.policy import PolicyDocument
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.services.vector_store import qdrant_service

CANONICAL_USER_IDS = {
    "usr-admin-01",
    "usr-ops-01",
    "usr-cs-01",
    "usr-comp-01",
    "usr-mgr-01",
    "usr-cust-01",
    "usr-cust-02",
}

CANONICAL_ACCOUNT_IDS = {
    "acc-cust1-chk",
    "acc-cust1-sav",
    "acc-cust2-chk",
}


async def reset_demo():
    parsed = urllib.parse.urlsplit(settings.DATABASE_URL)
    db_name = parsed.path.lstrip("/")

    # CRITICAL HARD-STOP GUARD
    if "test" in db_name.lower():
        raise RuntimeError(
            f"REFUSING EXECUTION: Database '{db_name}' contains 'test'! "
            f"reset_demo.py operates strictly on the development 'nileops' database."
        )

    print(f"--- [1/4] Resetting NileOps Demo Database ('{db_name}') ---")

    async with async_session_maker() as session:
        # 1. Delete runtime operational records created during demo sessions
        await session.execute(delete(CardRequest))
        await session.execute(delete(AccountOpeningRequest))
        await session.execute(delete(KycVerification))
        await session.execute(delete(AuditLog))
        await session.execute(delete(Transaction))
        await session.execute(delete(Complaint))

        # 2. Remove non-canonical users created in self-service or test runs
        users_result = await session.execute(select(User))
        for u in users_result.scalars().all():
            if u.id not in CANONICAL_USER_IDS:
                await session.delete(u)

        # 3. Remove non-canonical accounts
        accs_result = await session.execute(select(Account))
        for a in accs_result.scalars().all():
            if a.id not in CANONICAL_ACCOUNT_IDS:
                await session.delete(a)

        await session.commit()
        print("  - Cleared temporary requests, complaints, audit logs, and dynamic users.")

        # 4. Re-seed canonical data (users, accounts, baseline balances, approved policies)
        await seed_demo_data(session)
        print("  - Re-seeded canonical staff, customer accounts, and baseline policies.")

    # 5. Clean temporary upload folder
    print("--- [2/4] Cleaning Temporary Upload Artifacts ---")
    uploads_dir = backend_dir / "uploads"
    if uploads_dir.exists():
        cleaned_files = 0
        for item in uploads_dir.iterdir():
            if item.name != ".gitkeep" and item.is_file():
                try:
                    item.unlink()
                    cleaned_files += 1
                except Exception as e:
                    print(f"    Warning: Could not remove {item.name}: {e}")
        print(f"  - Removed {cleaned_files} temporary uploaded files.")

    # 6. Reconcile Qdrant vector index
    print("--- [3/4] Recreating & Reconciling Qdrant Knowledge Base Collection ---")
    try:
        if qdrant_service.client.collection_exists(qdrant_service.collection_name):
            qdrant_service.client.delete_collection(qdrant_service.collection_name)
        await qdrant_service.init_collection()
        async with async_session_maker() as session:
            recon = await qdrant_service.reconcile_with_postgres(session)
            print(f"  - Qdrant reconciled: {recon.get('total_qdrant_points', 0)} total points.")
    except Exception as e:
        print(f"  - Qdrant notice: {e}")

    print("--- [4/4] NileOps Demo Environment Successfully Reset ---")


if __name__ == "__main__":
    asyncio.run(reset_demo())
