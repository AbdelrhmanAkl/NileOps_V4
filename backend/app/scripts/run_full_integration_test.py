"""NileOps Live End-to-End System Integration Test Suite.

Executes real HTTP requests against the live running FastAPI server on http://127.0.0.1:8000
verifying Authentication, RBAC, Customer/Employee portals, Four-Eyes governance,
Qdrant vector retrieval, strict portal isolation, and 9D OCR validation.
"""

import sys
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000"

results = []

def record(name: str, passed: bool, detail: str = ""):
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {name}: {detail}")
    results.append({"test": name, "status": status_str, "detail": detail})


def run_tests():
    print(f"=== Starting NileOps Full System Integration Tests against {BASE_URL} ===\n")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Health Probe
    try:
        r = client.get("/health")
        data = r.json()
        record("Health Probe", r.status_code == 200 and data.get("status") == "healthy", f"status={data.get('status')}, db={data.get('database')}")
    except Exception as e:
        record("Health Probe", False, str(e))
        return

    # 2. Authentication: Customer Login
    try:
        r = client.post("/api/v1/auth/login", json={"email": "customer1@nileops.demo", "password": "Customer2026!"})
        data = r.json()
        cust_token = data.get("access_token")
        cust_user = data.get("user", {})
        record("Customer Login", r.status_code == 200 and bool(cust_token) and cust_user.get("user_type") == "customer", f"token_obtained=True, user_type={cust_user.get('user_type')}")
    except Exception as e:
        record("Customer Login", False, str(e))
        cust_token = None

    # 3. Authentication: Employee Logins
    try:
        # Operations Officer
        r_ops = client.post("/api/v1/auth/login", json={"email": "ops@nileops.demo", "password": "NileOps2026!"})
        ops_token = r_ops.json().get("access_token")
        record("Employee Login (Operations)", r_ops.status_code == 200 and bool(ops_token), f"role={r_ops.json().get('user', {}).get('role')}")

        # Compliance Reviewer
        r_comp = client.post("/api/v1/auth/login", json={"email": "compliance@nileops.demo", "password": "NileOps2026!"})
        comp_token = r_comp.json().get("access_token")
        record("Employee Login (Compliance)", r_comp.status_code == 200 and bool(comp_token), f"role={r_comp.json().get('user', {}).get('role')}")

        # Branch Manager
        r_mgr = client.post("/api/v1/auth/login", json={"email": "manager@nileops.demo", "password": "NileOps2026!"})
        mgr_token = r_mgr.json().get("access_token")
        record("Employee Login (Manager)", r_mgr.status_code == 200 and bool(mgr_token), f"role={r_mgr.json().get('user', {}).get('role')}")

        # Admin
        r_adm = client.post("/api/v1/auth/login", json={"email": "admin@nileops.demo", "password": "NileOps2026!"})
        adm_token = r_adm.json().get("access_token")
        record("Employee Login (Admin)", r_adm.status_code == 200 and bool(adm_token), f"role={r_adm.json().get('user', {}).get('role')}")
    except Exception as e:
        record("Employee Logins", False, str(e))

    # 4. Authentication: Invalid Credentials & Security Rejection
    try:
        r_bad = client.post("/api/v1/auth/login", json={"email": "customer1@nileops.demo", "password": "WrongPassword!"})
        record("Invalid Password Rejection", r_bad.status_code == 401, f"status={r_bad.status_code}")

        r_fake_jwt = client.get("/api/v1/customer/accounts", headers={"Authorization": "Bearer invalid.jwt.signature"})
        record("Invalid JWT Rejection", r_fake_jwt.status_code == 401, f"status={r_fake_jwt.status_code}")

        r_no_auth = client.get("/api/v1/customer/accounts")
        record("Missing Auth Token Rejection", r_no_auth.status_code == 401, f"status={r_no_auth.status_code}")
    except Exception as e:
        record("Auth Rejections", False, str(e))

    # 5. Authorization: Customer Isolation & Employee Barrier
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    try:
        # Customer tries to access employee dashboard -> must be 403
        r_emp_dash = client.get("/api/v1/employee/dashboard", headers=cust_headers)
        record("Customer Forbidden from Employee Dashboard", r_emp_dash.status_code == 403, f"status={r_emp_dash.status_code}")

        # Customer accesses own accounts -> 200 OK
        r_cust_acc = client.get("/api/v1/customer/accounts", headers=cust_headers)
        accounts = r_cust_acc.json()
        record("Customer Accounts Retrieval", r_cust_acc.status_code == 200 and len(accounts) > 0, f"accounts_count={len(accounts)}, balances={[a.get('balance') for a in accounts]}")

        # Customer accesses own transactions -> 200 OK
        r_cust_tx = client.get("/api/v1/customer/transactions", headers=cust_headers)
        record("Customer Transactions Retrieval", r_cust_tx.status_code == 200, f"tx_count={len(r_cust_tx.json())}")
    except Exception as e:
        record("Customer Authorization", False, str(e))

    # 6. Customer Portal: Complaint Submission & Tracking
    complaint_id = None
    try:
        complaint_payload = {
            "category": "ATM_CARD",
            "subject": "ATM Cash Retained Issue",
            "details": "ATM transaction deducted funds but cash was not dispensed at Zamalek branch.",
        }
        r_comp_sub = client.post("/api/v1/customer/complaints", json=complaint_payload, headers=cust_headers)
        comp_data = r_comp_sub.json()
        ticket_num = comp_data.get("ticket_number")
        complaint_id = comp_data.get("id")
        record("Customer Complaint Submission", r_comp_sub.status_code == 201 and bool(ticket_num), f"ticket={ticket_num}, id={complaint_id}")

        # List customer complaints
        r_comp_list = client.get("/api/v1/customer/complaints", headers=cust_headers)
        tickets = [c.get("ticket_number") for c in r_comp_list.json()]
        record("Customer Complaint Tracking", ticket_num in tickets, f"found_ticket={ticket_num in tickets}")
    except Exception as e:
        record("Customer Complaint Workflow", False, str(e))

    # 7. Employee Portal: Dashboard, Customers, Complaints
    ops_headers = {"Authorization": f"Bearer {ops_token}"}
    try:
        r_dash = client.get("/api/v1/employee/dashboard", headers=ops_headers)
        record("Employee Dashboard", r_dash.status_code == 200, f"total_customers={r_dash.json().get('total_customers')}")

        r_custs = client.get("/api/v1/employee/customers", headers=ops_headers)
        record("Employee Customer Lookup", r_custs.status_code == 200 and len(r_custs.json()) > 0, f"count={len(r_custs.json())}")

        # Employee updates complaint status
        if complaint_id:
            update_payload = {"status": "IN_PROGRESS", "staff_notes": "Assigned to ATM Reconciliation team."}
            r_upd = client.patch(f"/api/v1/employee/complaints/{complaint_id}", json=update_payload, headers=ops_headers)
            record("Employee Complaint Status Update", r_upd.status_code == 200 and r_upd.json().get("status") == "IN_PROGRESS", f"new_status={r_upd.json().get('status')}")
    except Exception as e:
        record("Employee Workflows", False, str(e))

    # 8. Four-Eyes Policy Governance Lifecycle
    try:
        unique_code = f"POL-TEST-{uuid.uuid4().hex[:6].upper()}"
        policy_payload = {
            "code": unique_code,
            "title_en": "ATM Cash Dispensation Policy (Live Test)",
            "title_ar": "سياسة تسوية منازعات الصراف الآلي",
            "domain": "RETAIL_BANKING",
            "content_en": "ATM dispensation errors must be reconciled and credited within 24 business hours.",
            "content_ar": "يجب تسوية أخطاء السحب من ماكينات الصراف الآلي وقيد المبالغ في حساب العميل خلال ٢٤ ساعة عمل.",
            "version": "1.0.0",
        }
        # Step A: Ops creates policy draft -> status is DRAFT
        r_create_pol = client.post("/api/v1/policies", json=policy_payload, headers=ops_headers)
        pol_data = r_create_pol.json()
        pol_id = pol_data.get("id")
        pol_code = pol_data.get("code")
        record("Four-Eyes Step 1: Create Policy Draft", r_create_pol.status_code == 201 and pol_data.get("status") == "DRAFT", f"id={pol_id}, code={pol_code}")

        # Step B: Submit policy for approval -> status is PENDING_APPROVAL
        r_sub_pol = client.post(f"/api/v1/policies/{pol_id}/submit", headers=ops_headers)
        sub_data = r_sub_pol.json()
        record("Four-Eyes Step 2: Submit Policy for Approval", r_sub_pol.status_code == 200 and sub_data.get("status") == "PENDING_APPROVAL", f"status={sub_data.get('status')}")

        # Step C: Ops (Creator) attempts to approve own policy -> MUST BE REJECTED (4-eyes violation)
        r_self_appr = client.post(f"/api/v1/policies/{pol_id}/approve", json={"notes": "Self approval attempt"}, headers=ops_headers)
        record("Four-Eyes Step 3: Self-Approval Prevention", r_self_appr.status_code in (400, 403), f"status={r_self_appr.status_code}, error={r_self_appr.json().get('detail')}")

        # Step D: Compliance Reviewer (Separate Actor) approves policy -> APPROVED
        comp_headers = {"Authorization": f"Bearer {comp_token}"}
        r_appr = client.post(f"/api/v1/policies/{pol_id}/approve", json={"notes": "Approved by Compliance Reviewer"}, headers=comp_headers)
        record("Four-Eyes Step 4: Independent Approval", r_appr.status_code == 200 and r_appr.json().get("status") in ("APPROVED", "INDEXED"), f"status={r_appr.json().get('status')}")

        # Step E: Reconcile Qdrant -> document indexed into vector collection
        r_recon = client.post("/api/v1/rag/reconcile", headers=comp_headers)
        record("Four-Eyes Step 5: Qdrant Reconciliation", r_recon.status_code == 200, f"points={r_recon.json().get('result', {}).get('total_qdrant_points')}")
    except Exception as e:
        record("Four-Eyes Policy Governance", False, str(e))

    # 9. RAG: Real Policy Retrieval & Strict Portal Isolation
    try:
        # A. Customer searches retail policy in Arabic
        r_rag_cust = client.post(
            "/api/v1/rag/ask",
            json={"query": "ما هي متطلبات فتح حساب جاري للأفراد؟", "portal_type": "customer", "language": "ar", "threshold": 0.15},
        )
        data_rag = r_rag_cust.json()
        codes = [c.get("code") for c in data_rag.get("citations", [])]
        record("RAG Customer Retail Query (Arabic)", r_rag_cust.status_code == 200 and not data_rag.get("abstained") and "POL-RETAIL-001" in codes, f"citations={codes}, score={data_rag.get('confidence_score')}")

        # B. Customer searches internal KYC procedure -> MUST NOT return POL-KYC-001
        r_leak = client.post(
            "/api/v1/rag/ask",
            json={"query": "KYC customer identification and verification process", "portal_type": "customer", "language": "en", "threshold": 0.20},
        )
        data_leak = r_leak.json()
        leak_codes = [c.get("code") for c in data_leak.get("citations", [])]
        record("RAG Strict Portal Isolation (POL-KYC-001 Blocked for Customer)", "POL-KYC-001" not in leak_codes, f"customer_got_codes={leak_codes}")

        # C. Employee searches same KYC query -> CAN access POL-KYC-001
        r_emp_rag = client.post(
            "/api/v1/rag/ask",
            json={"query": "KYC customer identification and verification process", "portal_type": "employee", "language": "en", "threshold": 0.20},
        )
        data_emp = r_emp_rag.json()
        emp_codes = [c.get("code") for c in data_emp.get("citations", [])]
        record("RAG Employee Compliance Access (POL-KYC-001 Accessible)", "POL-KYC-001" in emp_codes, f"employee_got_codes={emp_codes}")

        # D. Off-topic query -> MUST abstain
        r_off = client.post(
            "/api/v1/rag/ask",
            json={"query": "كيف أقوم بتغيير زيت محرك السيارة؟", "portal_type": "customer", "language": "ar", "threshold": 0.20},
        )
        data_off = r_off.json()
        record("RAG Off-Topic Abstention", data_off.get("abstained") is True and data_off.get("confidence_score") == 0.0, f"abstained={data_off.get('abstained')}")
    except Exception as e:
        record("RAG Live Integration", False, str(e))

    # 10. OCR & National ID Deterministic Validation
    try:
        # A. Valid Western digits
        r_ocr_w = client.post("/api/v1/ocr/validate-national-id", json={"raw_national_id": "29505140101234", "workflow_context": "STRUCTURED_INTAKE"})
        d_ocr_w = r_ocr_w.json()
        record("OCR Valid Western Digits", d_ocr_w.get("format_status") == "FORMAT_VALID" and d_ocr_w.get("derived_governorate") == "القاهرة", f"gov={d_ocr_w.get('derived_governorate')}, gender={d_ocr_w.get('derived_gender')}")

        # B. Eastern Arabic-Indic digits
        r_ocr_e = client.post("/api/v1/ocr/validate-national-id", json={"raw_national_id": "٢٩٥٠٥١٤٠١٠١٢٣٤", "workflow_context": "STRUCTURED_INTAKE"})
        d_ocr_e = r_ocr_e.json()
        record("OCR Eastern Arabic-Indic Normalization", d_ocr_e.get("normalization_status") == "NORMALIZATION_PASSED" and d_ocr_e.get("masked_national_id") == "2950****1234", f"masked={d_ocr_e.get('masked_national_id')}")

        # C. Invalid governorate code (e.g. 99) -> human review
        r_ocr_gov = client.post("/api/v1/ocr/validate-national-id", json={"raw_national_id": "29505149901234", "workflow_context": "STRUCTURED_INTAKE"})
        d_ocr_gov = r_ocr_gov.json()
        record("OCR Invalid Governorate Review Routing", d_ocr_gov.get("governorate_status") == "GOVERNORATE_REFERENCE_UNMATCHED" and d_ocr_gov.get("review_status") == "REQUIRES_HUMAN_REVIEW", f"review={d_ocr_gov.get('review_status')}")

        # D. Synthetic card extraction simulation
        r_card = client.post("/api/v1/ocr/process-synthetic-card", data={"synthetic_id": "29505140101234", "ocr_confidence": 0.95})
        d_card = r_card.json()
        record("OCR Document AI Compound Status (DAI-02)", d_card.get("compound_status") == "PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED", f"compound={d_card.get('compound_status')}")
    except Exception as e:
        record("OCR Live Integration", False, str(e))

    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n=== Summary: {passed_count} PASSED, {failed_count} FAILED out of {len(results)} integration tests ===")
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
