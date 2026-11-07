"""Reconciliation script between PostgreSQL policies and Qdrant vector index."""

import asyncio
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import async_session_maker
from app.services.vector_store import qdrant_service


async def main():
    print("--- 1. Testing Qdrant Connection ---")
    health = qdrant_service.check_health()
    print("Initial Health:", health)

    print("\n--- 2. Initializing Collection ---")
    init_ok = await qdrant_service.init_collection()
    print("Collection Init Success:", init_ok)

    print("\n--- 3. Running PostgreSQL Reconciliation ---")
    async with async_session_maker() as session:
        recon_result = await qdrant_service.reconcile_with_postgres(session)
        print("Reconciliation Result:", recon_result)

    print("\n--- 4. Testing Semantic Search: Customer Portal ---")
    customer_query = "ما هي متطلبات فتح حساب جاري للأفراد؟"
    customer_hits = await qdrant_service.search(customer_query, portal_type="customer", limit=3)
    print(f"Customer query '{customer_query}' returned {len(customer_hits)} hits:")
    for h in customer_hits:
        print(f"  - [{h['code']}] {h['title']} (score: {h['score']}, portal: {h['portal_access']})")

    print("\n--- 5. Testing Portal Isolation (KYC/Internal Search) ---")
    aml_query = "إجراءات فحص اعرف عميلك ومكافحة غسل الأموال"
    cust_aml_hits = await qdrant_service.search(aml_query, portal_type="customer", limit=3)
    print(f"Customer Portal KYC hits: {len(cust_aml_hits)}")
    for h in cust_aml_hits:
        print(f"  - Customer got: [{h['code']}] {h['portal_access']}")

    emp_aml_hits = await qdrant_service.search(aml_query, portal_type="employee", limit=3)
    print(f"Employee Portal KYC hits: {len(emp_aml_hits)}")
    for h in emp_aml_hits:
        print(f"  - Employee got: [{h['code']}] {h['portal_access']} (score: {h['score']})")


if __name__ == "__main__":
    asyncio.run(main())

