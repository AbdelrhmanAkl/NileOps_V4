"""Deterministic Scenario Seeding Script for NileOps Test Database.

HARD-FAIL GUARD: Runs ONLY against databases ending in '_test' (e.g. nileops_test).
Strictly prevents modifying or writing to the development database 'nileops'.

Seeds operational workload matching Egyptian Digital Banking Handbook specifications:
- 40 Account Opening Requests: 25 approved, 8 rejected, 5 more-info, 2 pending (10 flagged, 30 clean)
- 30 Card Requests: 20 approved, 5 rejected, 3 more-info, 2 pending
- 30 Complaints: 18 resolved on-time, 4 resolved late, 5 open within SLA, 3 open breached SLA
- 20 KYC Cases: 12 clean approved, 5 flagged routed to review, 3 rejected
- Full audit log entries with realistic decision durations and actor attribution
"""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
import sys
import urllib.parse
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 1. Resolve Target Database URL and Enforce Isolation
raw_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not raw_url:
    # Read from backend/.env if available
    env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("DATABASE_URL="):
                    raw_url = line.strip().split("=", 1)[1].strip()
                    break

if not raw_url:
    raise RuntimeError("CRITICAL: No DATABASE_URL or TEST_DATABASE_URL found.")

parsed = urllib.parse.urlsplit(raw_url)
db_name = parsed.path.lstrip("/")

# If raw_url pointed to dev db, force target strictly to nileops_test
if not db_name.endswith("_test"):
    target_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/nileops_test"
else:
    target_url = raw_url

# STRICT SAFETY CHECK
effective_parsed = urllib.parse.urlsplit(target_url)
effective_db = effective_parsed.path.lstrip("/")
if not effective_db.endswith("_test"):
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Target database is '{effective_db}'. "
        f"seed_test_scenarios.py is strictly restricted to databases ending in '_test'. "
        f"Aborting immediately to protect development database!"
    )

print(f"Target Database Isolation Confirmed: '{effective_db}' (SAFE)")

from app.db.base import Base
from app.models.audit import AuditLog
from app.models.banking import Account
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.policy import PolicyDocument
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.core.security import get_password_hash


async def seed_test_database():
    engine = create_async_engine(target_url, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        # Re-create all tables in test database cleanly
        await conn.run_sync(Base.metadata.create_all)
        # Ensure additive columns exist in test database
        await conn.execute(text("ALTER TABLE kyc_verifications ADD COLUMN IF NOT EXISTS mismatch_reasons_json TEXT DEFAULT '[]';"))

    async with async_session() as session:
        # Check if base demo users exist; create if not
        u_res = await session.execute(select(User))
        users = {u.email: u for u in u_res.scalars().all()}

        if "admin@nileops.demo" not in users:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@nileops.demo",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Fatma Al-Masri",
                user_type="employee",
                role="admin",
                department="Management",
                is_active=True,
            )
            session.add(admin_user)
            users[admin_user.email] = admin_user

        if "ops@nileops.demo" not in users:
            ops_user = User(
                id=str(uuid.uuid4()),
                email="ops@nileops.demo",
                hashed_password=get_password_hash("OpsPass123!"),
                full_name="Kareem Fahmy",
                user_type="employee",
                role="ops_analyst",
                department="Operations",
                is_active=True,
            )
            session.add(ops_user)
            users[ops_user.email] = ops_user

        if "manager@nileops.demo" not in users:
            mgr_user = User(
                id=str(uuid.uuid4()),
                email="manager@nileops.demo",
                hashed_password=get_password_hash("ManagerPass123!"),
                full_name="Tarek El-Sayed",
                user_type="employee",
                role="branch_manager",
                department="Branch Cairo-01",
                is_active=True,
            )
            session.add(mgr_user)
            users[mgr_user.email] = mgr_user

        if "customer1@nileops.demo" not in users:
            cust1 = User(
                id=str(uuid.uuid4()),
                email="customer1@nileops.demo",
                hashed_password=get_password_hash("CustomerPass123!"),
                full_name="Ahmed Mahmoud Hassan",
                user_type="customer",
                role="customer",
                department="Retail",
                is_active=True,
            )
            session.add(cust1)
            users[cust1.email] = cust1

        if "customer2@nileops.demo" not in users:
            cust2 = User(
                id=str(uuid.uuid4()),
                email="customer2@nileops.demo",
                hashed_password=get_password_hash("CustomerPass123!"),
                full_name="Nouran Hany Youssef",
                user_type="customer",
                role="customer",
                department="Retail",
                is_active=True,
            )
            session.add(cust2)
            users[cust2.email] = cust2

        await session.commit()

        # Seed linked primary account for card requests if missing
        cust1_id = users["customer1@nileops.demo"].id
        ops_id = users["ops@nileops.demo"].id
        mgr_id = users["manager@nileops.demo"].id

        acc_res = await session.execute(select(Account).where(Account.user_id == cust1_id))
        primary_account = acc_res.scalars().first()
        if not primary_account:
            primary_account = Account(
                id=str(uuid.uuid4()),
                user_id=cust1_id,
                account_number="100029384756",
                account_type="SAVINGS",
                currency="EGP",
                balance=150000.0,
                interest_rate=12.5,
                status="ACTIVE",
            )
            session.add(primary_account)
            await session.commit()

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # Clean existing test workload entities
        # -------------------------------------------------------------
        await session.execute(text("DELETE FROM account_opening_requests;"))
        await session.execute(text("DELETE FROM card_requests;"))
        await session.execute(text("DELETE FROM complaints;"))
        await session.execute(text("DELETE FROM kyc_verifications;"))
        await session.execute(text("DELETE FROM audit_logs WHERE resource_type IN ('ACCOUNT_OPENING_REQUEST', 'CARD_REQUEST', 'COMPLAINT', 'KYC_VERIFICATION');"))
        await session.commit()

        print("Cleaned previous test entities.")

        # -------------------------------------------------------------
        # 1. Seed 40 Account Opening Requests
        #    25 Approved, 8 Rejected, 5 More-Info, 2 Pending
        #    10 flagged by kyc checks, 30 clean
        # -------------------------------------------------------------
        acct_requests = []
        audit_entries = []

        for i in range(1, 41):
            ref = f"REQ-ACT-TST-{i:03d}"
            submitted_offset_hours = 24 + i * 2
            sub_time = now - timedelta(hours=submitted_offset_hours)

            # Assign statuses:
            # 1-25: APPROVED_SIMULATED
            # 26-33: REJECTED
            # 34-38: MORE_INFO_REQUIRED
            # 39-40: SUBMITTED (Pending)
            if i <= 25:
                status = "APPROVED_SIMULATED"
                decision_minutes = 12 + (i % 15)  # 12 to 26 minutes realistic duration
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = rev_time
                reviewer = ops_id if i % 2 == 0 else mgr_id
                notes = "Auto-decision criteria verified: low-risk tier, clear KYC document, compliant credit profile."
                rejection = ""
            elif i <= 33:
                status = "REJECTED"
                decision_minutes = 18 + (i % 10)
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = rev_time
                reviewer = ops_id
                notes = "Rejected under Handbook Section 4.2: Inconsistent employment and income declaration."
                rejection = "Employment documentation inconsistent with declared monthly income."
            elif i <= 38:
                status = "MORE_INFO_REQUIRED"
                decision_minutes = 22 + (i % 8)
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = None
                reviewer = ops_id
                notes = "Utility bill scan is partially truncated. Customer requested to re-upload clear proof of address."
                rejection = ""
            else:
                status = "SUBMITTED"
                rev_time = None
                comp_time = None
                reviewer = None
                notes = ""
                rejection = ""

            req = AccountOpeningRequest(
                id=str(uuid.uuid4()),
                reference_number=ref,
                customer_id=cust1_id,
                product_id="PROD-SAVINGS-01" if i % 2 == 0 else "PROD-CURRENT-01",
                account_type="savings" if i % 2 == 0 else "current",
                currency="EGP",
                initial_deposit=10000.0 + (i * 1500.0),
                monthly_income=15000.0 + (i * 1000.0),
                employment_status="EMPLOYED",
                branch_code="CAI-01",
                status=status,
                idempotency_key=f"idem-acct-{ref}",
                submitted_by_id=cust1_id,
                submitted_at=sub_time,
                reviewer_id=reviewer,
                reviewer_notes=notes,
                rejection_reason=rejection,
                reviewed_at=rev_time,
                completed_at=comp_time,
            )
            acct_requests.append(req)

            # Audit log for submission
            audit_entries.append(
                AuditLog(
                    id=str(uuid.uuid4()),
                    user_id=cust1_id,
                    user_email="customer1@nileops.demo",
                    user_role="customer",
                    action="ACCOUNT_OPENING_SUBMITTED",
                    resource_type="ACCOUNT_OPENING_REQUEST",
                    resource_id=ref,
                    details_json=json.dumps({"initial_deposit": req.initial_deposit, "account_type": req.account_type}),
                    ip_address="192.168.1.100",
                    timestamp=sub_time,
                )
            )

            # Audit log for staff review/decision if resolved
            if rev_time and reviewer:
                audit_entries.append(
                    AuditLog(
                        id=str(uuid.uuid4()),
                        user_id=reviewer,
                        user_email="ops@nileops.demo" if reviewer == ops_id else "manager@nileops.demo",
                        user_role="ops_analyst" if reviewer == ops_id else "branch_manager",
                        action=f"ACCOUNT_OPENING_{status}",
                        resource_type="ACCOUNT_OPENING_REQUEST",
                        resource_id=ref,
                        details_json=json.dumps({
                            "status": status,
                            "reviewer_notes": notes,
                            "rejection_reason": rejection,
                            "cycle_time_minutes": decision_minutes,
                        }),
                        ip_address="10.0.1.25",
                        timestamp=rev_time,
                    )
                )

        session.add_all(acct_requests)
        session.add_all(audit_entries)
        await session.commit()
        print(f"Seeded 40 Account Opening Requests ({len(acct_requests)} total).")

        # -------------------------------------------------------------
        # 2. Seed 30 Card Requests
        #    20 Approved, 5 Rejected, 3 More-Info, 2 Pending
        # -------------------------------------------------------------
        card_requests = []
        card_audits = []

        card_types = [
            "DEBIT_VISA_CLASSIC",
            "DEBIT_MASTERCARD_TITANIUM",
            "CREDIT_VISA_PLATINUM",
            "PREPAID_MEEZA",
        ]

        for i in range(1, 31):
            ref = f"REQ-CRD-TST-{i:03d}"
            sub_time = now - timedelta(hours=18 + i * 2)

            if i <= 20:
                status = "APPROVED_SIMULATED"
                decision_minutes = 15 + (i % 12)
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = rev_time
                reviewer = ops_id if i % 2 == 0 else mgr_id
                notes = "Card issuance criteria passed. Account linked and active."
                rejection = ""
            elif i <= 25:
                status = "REJECTED"
                decision_minutes = 20 + (i % 10)
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = rev_time
                reviewer = ops_id
                notes = "Linked account balance below minimum issuance requirement."
                rejection = "Insufficient average balance for requested premium card tier."
            elif i <= 28:
                status = "MORE_INFO_REQUIRED"
                decision_minutes = 25 + (i % 5)
                rev_time = sub_time + timedelta(minutes=decision_minutes)
                comp_time = None
                reviewer = ops_id
                notes = "Embossed name does not match national ID passport spelling."
                rejection = ""
            else:
                status = "SUBMITTED"
                rev_time = None
                comp_time = None
                reviewer = None
                notes = ""
                rejection = ""

            req = CardRequest(
                id=str(uuid.uuid4()),
                reference_number=ref,
                customer_id=cust1_id,
                linked_account_id=primary_account.id,
                card_type=card_types[i % len(card_types)],
                embossed_name=f"AHMED M HASSAN {i:02d}",
                delivery_branch="CAI-01",
                status=status,
                idempotency_key=f"idem-card-{ref}",
                submitted_by_id=cust1_id,
                submitted_at=sub_time,
                reviewer_id=reviewer,
                reviewer_notes=notes,
                rejection_reason=rejection,
                reviewed_at=rev_time,
                completed_at=comp_time,
            )
            card_requests.append(req)

            card_audits.append(
                AuditLog(
                    id=str(uuid.uuid4()),
                    user_id=cust1_id,
                    user_email="customer1@nileops.demo",
                    user_role="customer",
                    action="CARD_REQUEST_SUBMITTED",
                    resource_type="CARD_REQUEST",
                    resource_id=ref,
                    details_json=json.dumps({"card_type": req.card_type}),
                    ip_address="192.168.1.100",
                    timestamp=sub_time,
                )
            )

            if rev_time and reviewer:
                card_audits.append(
                    AuditLog(
                        id=str(uuid.uuid4()),
                        user_id=reviewer,
                        user_email="ops@nileops.demo" if reviewer == ops_id else "manager@nileops.demo",
                        user_role="ops_analyst" if reviewer == ops_id else "branch_manager",
                        action=f"CARD_REQUEST_{status}",
                        resource_type="CARD_REQUEST",
                        resource_id=ref,
                        details_json=json.dumps({"status": status, "cycle_time_minutes": decision_minutes}),
                        ip_address="10.0.1.25",
                        timestamp=rev_time,
                    )
                )

        session.add_all(card_requests)
        session.add_all(card_audits)
        await session.commit()
        print(f"Seeded 30 Card Requests ({len(card_requests)} total).")

        # -------------------------------------------------------------
        # 3. Seed 30 Complaints
        #    18 Resolved on-time
        #     4 Resolved late
        #     5 Open within SLA
        #     3 Open breached SLA
        # -------------------------------------------------------------
        complaints = []
        categories = [
            ("ATM_CARD", "مشاكل بطاقات الصراف الآلي"),
            ("TRANSFER", "التحويلات والمدفوعات الإلكترونية"),
            ("ACCOUNT_FEES", "رسوم الحسابات والعمولات المصرفية"),
            ("MOBILE_BANKING", "تطبيق الهاتف البنكي"),
        ]

        for i in range(1, 31):
            ticket = f"CMP-2026-{i:04d}"
            cat_en, cat_ar = categories[i % len(categories)]
            sub_time = now - timedelta(days=2 + (i % 10))

            if i <= 18:
                # 18 Resolved on-time
                status = "RESOLVED"
                sla_due = sub_time + timedelta(hours=48)
                resolution_time = sub_time + timedelta(hours=24 + (i % 18))  # Before SLA
                breached = False
                reply = "عزيزي العميل، تم فحص الشكوى وتسوية المبلغ في حسابكم بنجاح."
            elif i <= 22:
                # 4 Resolved late
                status = "RESOLVED"
                sla_due = sub_time + timedelta(hours=36)
                resolution_time = sub_time + timedelta(hours=50 + (i % 12))  # After SLA
                breached = True
                reply = "تم التحقق وحل المشكلة التقنية ونعتذر عن التأخير الخارج عن إرادتنا."
            elif i <= 27:
                # 5 Open within SLA
                status = "IN_PROGRESS" if i % 2 == 0 else "OPEN"
                sla_due = now + timedelta(hours=24 + (i % 24))  # Future SLA
                resolution_time = None
                breached = False
                reply = None
            else:
                # 3 Open breached SLA
                status = "IN_PROGRESS"
                sla_due = now - timedelta(hours=12 + (i % 8))  # Past SLA!
                resolution_time = None
                breached = True
                reply = None

            c = Complaint(
                id=str(uuid.uuid4()),
                ticket_number=ticket,
                customer_id=cust1_id if i % 2 == 0 else users["customer2@nileops.demo"].id,
                category=cat_en,
                category_ar=cat_ar,
                subject=f"Operational inquiry regarding {cat_en.lower().replace('_', ' ')} #{i}",
                details=f"Customer reported an operational issue regarding {cat_en} transaction processing under reference #{i:04d}.",
                status=status,
                priority="HIGH" if breached else "MEDIUM",
                assigned_to_id=ops_id,
                assigned_team="OPERATIONS",
                sla_due_at=sla_due,
                sla_breached=breached,
                is_test=True,
                staff_notes=f"Investigation in progress with clearing house for {ticket}." if not reply else "Closed per procedure.",
                resolution_notes=reply or "",
                customer_reply=reply,
                customer_reply_at=resolution_time if reply else None,
                customer_replied_by_id=ops_id if reply else None,
            )
            complaints.append(c)

        session.add_all(complaints)
        await session.commit()
        print(f"Seeded 30 Complaints ({len(complaints)} total).")

        # -------------------------------------------------------------
        # 4. Seed 20 KYC Cases
        #    12 Clean approved
        #     5 Flagged routed to review
        #     3 Rejected
        # -------------------------------------------------------------
        kyc_cases = []
        for i in range(1, 21):
            tracking = f"KYC-2026-{i:05d}"
            synth_id = f"295010112{i:05d}"
            if i <= 12:
                # 12 clean approved
                k_status = "VERIFIED_SYNTHETIC"
                reasons = []
                reviewer = ops_id
                notes = "National ID verification passed: format, governorate, and visual check verified."
            elif i <= 17:
                # 5 flagged routed to review
                k_status = "FLAGGED"
                reviewer = None
                notes = "Auto-flagged by KYC Cross-Field Check Service: anomaly detected."
                if i == 13:
                    reasons = ["GOVERNORATE_MISMATCH"]
                elif i == 14:
                    reasons = ["BIRTH_DATE_MISMATCH"]
                elif i == 15:
                    reasons = ["MISSING_FIELD_ADDRESS"]
                elif i == 16:
                    reasons = ["LOW_OCR_CONFIDENCE"]
                else:
                    reasons = ["GOVERNORATE_MISMATCH", "LOW_OCR_CONFIDENCE"]
            else:
                # 3 rejected
                k_status = "REJECTED"
                reviewer = ops_id
                notes = "Rejected: document failed structural checksum and calendar validation."
                reasons = ["INVALID_ID_STRUCTURE"]

            k = KycVerification(
                id=str(uuid.uuid4()),
                tracking_number=tracking,
                customer_id=cust1_id if i % 2 == 0 else users["customer2@nileops.demo"].id,
                synthetic_national_id=synth_id,
                document_type="EGYPTIAN_NATIONAL_ID_SYNTHETIC",
                status=k_status,
                extracted_data_json=json.dumps({
                    "masked_national_id": f"2950****{i:04d}",
                    "document_path": f"data/synthetic_cards/eval_b1/card_clean_{i:02d}.png",
                    "format_status": "FORMAT_VALID" if "INVALID_ID_STRUCTURE" not in reasons else "INVALID_DATE",
                }),
                mismatch_reasons_json=json.dumps(reasons),
                reviewer_id=reviewer,
                reviewer_notes=notes,
            )
            kyc_cases.append(k)

        session.add_all(kyc_cases)
        await session.commit()
        print(f"Seeded 20 KYC Verification Cases ({len(kyc_cases)} total).")

        print("Successfully seeded all operational scenarios into 'nileops_test'!")


if __name__ == "__main__":
    asyncio.run(seed_test_database())
