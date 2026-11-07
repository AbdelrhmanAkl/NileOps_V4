"""Comprehensive NileOps MVP Integration & Security Tests."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()


# 1. Health check
def test_health_check(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NileOps Backend"


# 2. Authentication & JWT Sessions
def test_auth_success_and_failure(client: TestClient):
    # Success
    data = login(client, "admin@nileops.demo", "NileOps2026!")
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@nileops.demo"

    # Bad password
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@nileops.demo", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


# 3. Role-Based Access Control
def test_employee_endpoint_rejects_customer(client: TestClient):
    # Customer login
    cust_data = login(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_data['access_token']}"}

    # Attempt to access Employee Dashboard
    resp = client.get("/api/v1/employee/dashboard", headers=cust_headers)
    assert resp.status_code == 403
    assert "restricted" in resp.json()["detail"].lower()

    # Employee login succeeds
    ops_data = login(client, "ops@nileops.demo", "NileOps2026!")
    ops_headers = {"Authorization": f"Bearer {ops_data['access_token']}"}
    resp = client.get("/api/v1/employee/dashboard", headers=ops_headers)
    assert resp.status_code == 200
    assert "metrics" in resp.json()


# 4. Customer Data Ownership Isolation
def test_customer_data_ownership(client: TestClient):
    cust1 = login(client, "customer1@nileops.demo", "Customer2026!")
    cust2 = login(client, "customer2@nileops.demo", "Customer2026!")

    h1 = {"Authorization": f"Bearer {cust1['access_token']}"}
    h2 = {"Authorization": f"Bearer {cust2['access_token']}"}

    # Cust 1 accounts
    r1 = client.get("/api/v1/customer/accounts", headers=h1)
    assert r1.status_code == 200
    accs1 = r1.json()
    assert len(accs1) >= 1
    acc1_id = accs1[0]["id"]

    # Cust 2 cannot view Cust 1's transactions
    r2_forbidden = client.get(f"/api/v1/customer/transactions?account_id={acc1_id}", headers=h2)
    assert r2_forbidden.status_code == 403


# 5. Complaint Submission & Lifecycle
def test_complaint_lifecycle(client: TestClient):
    cust1 = login(client, "customer1@nileops.demo", "Customer2026!")
    h_cust = {"Authorization": f"Bearer {cust1['access_token']}"}

    # Submit complaint
    payload = {
        "category": "ATM_CARD",
        "subject": "Card captured by ATM machine at branch",
        "details": "The ATM machine retained my debit card after entering PIN.",
    }
    create_resp = client.post("/api/v1/customer/complaints", json=payload, headers=h_cust)
    assert create_resp.status_code == 201
    created_cmp = create_resp.json()
    cmp_id = created_cmp["id"]
    assert created_cmp["status"] == "OPEN"

    # Staff updates status to IN_PROGRESS
    cs_user = login(client, "cs@nileops.demo", "NileOps2026!")
    h_cs = {"Authorization": f"Bearer {cs_user['access_token']}"}

    patch_resp = client.patch(
        f"/api/v1/employee/complaints/{cmp_id}",
        json={"status": "IN_PROGRESS", "staff_notes": "Branch team contacted."},
        headers=h_cs,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "IN_PROGRESS"


import uuid

# 6. Policy Approval Restrictions (4-Eyes Governance)
def test_policy_four_eyes_approval(client: TestClient):
    comp_user = login(client, "compliance@nileops.demo", "NileOps2026!")
    h_comp = {"Authorization": f"Bearer {comp_user['access_token']}"}

    mgr_user = login(client, "manager@nileops.demo", "NileOps2026!")
    h_mgr = {"Authorization": f"Bearer {mgr_user['access_token']}"}

    unique_code = f"POL-TEST-{uuid.uuid4().hex[:6].upper()}"

    # 1. Author (Compliance Reviewer) creates a draft policy
    draft_data = {
        "code": unique_code,
        "title_en": "Whistleblower Protection Policy",
        "title_ar": "سياسة حماية المبلغين عن المخالفات",
        "domain": "governance",
        "content_en": "Employees may confidentially report suspicious activities without fear of retaliation.",
        "content_ar": "يجوز للموظفين الإبلاغ بسرية عن أي أنشطة مشبوهة دون خوف من الإجراءات الانتقامية.",
        "version": "1.0.0",
    }
    r_create = client.post("/api/v1/policies", json=draft_data, headers=h_comp)
    assert r_create.status_code == 201
    policy_id = r_create.json()["id"]

    # 2. Submit policy for approval
    r_submit = client.post(f"/api/v1/policies/{policy_id}/submit", headers=h_comp)
    assert r_submit.status_code == 200
    assert r_submit.json()["status"] == "PENDING_APPROVAL"

    # 3. RULE: Author CANNOT approve their own policy (4-Eyes violation)
    # Even though Compliance Reviewer has the approve role, self-approval is blocked!
    r_self_approve = client.post(
        f"/api/v1/policies/{policy_id}/approve",
        json={"approval_notes": "Self approval attempt"},
        headers=h_comp,
    )
    assert r_self_approve.status_code == 403
    assert "four-eyes" in r_self_approve.json()["detail"].lower()

    # 4. Another authorized user (Branch Manager) CAN approve it
    r_approve = client.post(
        f"/api/v1/policies/{policy_id}/approve",
        json={"approval_notes": "Approved by Branch Manager"},
        headers=h_mgr,
    )
    assert r_approve.status_code == 200
    assert r_approve.json()["status"] == "INDEXED"
    assert r_approve.json()["approved_by_id"] == mgr_user["user"]["id"]
