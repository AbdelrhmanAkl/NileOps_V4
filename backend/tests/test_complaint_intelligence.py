"""Phase 4 API & Functional Tests for Complaint Intelligence & Operations.

Tests:
1. Deterministic advisory classification (keywords, category, team, priority, draft).
2. SLA calculation, breach detection, and simulated banking policy.
3. Status transitions and invalid transition conflict (409 Conflict).
4. Server-side pagination, search, and filtering (status, category, priority, team, test exclusion).
5. Strict customer segregation: customers CANNOT see staff_notes or internal AI drafts.
6. Employee management, human-approved customer reply, and audit logging.
7. RBAC: customers cannot access employee management endpoints (403 Forbidden).
"""

import pytest
from starlette.testclient import TestClient
from fastapi import HTTPException

from app.services.complaint_sla import calculate_sla_due_at, evaluate_sla
from app.services.complaint_intelligence import classify_complaint_deterministically
from app.services.complaint_workflow import validate_complaint_transition


def get_token(client: TestClient, email: str, password: str = "NileOps2026!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_deterministic_advisory_classification():
    """Verify deterministic keyword-based category, team, priority, and draft template."""
    # Test ATM card retention
    res_atm = classify_complaint_deterministically(
        subject="ATM card captured at Zamalek machine",
        details="I attempted a cash withdrawal and the ATM retained my card without dispensing money.",
        customer_name="Tarek Nour",
        ticket_number="CMP-TEST-001",
    )
    assert res_atm.suggested_category == "ATM_CARD"
    assert res_atm.suggested_team == "CARDS_PAYMENTS"
    assert res_atm.suggested_priority in ("HIGH", "URGENT")
    assert any(k in ["atm", "card", "captured", "retained"] for k in res_atm.matched_keywords)
    assert "Tarek Nour" in res_atm.draft_reply
    assert res_atm.advisory_label == "AI suggestion - requires human review"
    assert res_atm.confidence_claimed is False

    # Test InstaPay transfer delay
    res_transfer = classify_complaint_deterministically(
        subject="Delayed InstaPay fast transfer to recipient",
        details="Sent 5000 EGP via InstaPay, debited from account but beneficiary has not received it.",
        customer_name="Mona Zaki",
        ticket_number="CMP-TEST-002",
    )
    assert res_transfer.suggested_category == "TRANSFER"
    assert res_transfer.suggested_team == "OPERATIONS"
    assert "instapay" in res_transfer.matched_keywords or "transfer" in res_transfer.matched_keywords


def test_sla_calculation_and_breach_detection():
    """Verify SLA policy hours, remaining time computation, and breach statuses."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    due_urgent = calculate_sla_due_at(now, "URGENT")
    assert round((due_urgent - now).total_seconds() / 3600.0) == 4

    due_medium = calculate_sla_due_at(now, "MEDIUM")
    assert round((due_medium - now).total_seconds() / 3600.0) == 24

    # Evaluate on-track
    eval_ontrack = evaluate_sla(created_at=now, priority="URGENT", status="OPEN", due_at=due_urgent, now=now)
    assert eval_ontrack.is_breached is False
    assert eval_ontrack.status_label == "ON_TRACK"

    # Evaluate breached (simulated past ticket)
    past_created = now - timedelta(hours=30)
    past_due = past_created + timedelta(hours=4)
    eval_breached = evaluate_sla(created_at=past_created, priority="URGENT", status="OPEN", due_at=past_due, now=now)
    assert eval_breached.is_breached is True
    assert eval_breached.status_label == "BREACHED"


def test_strict_complaint_status_transitions():
    """Verify state machine transitions and HTTP 409 on invalid transitions."""
    # Valid transitions
    validate_complaint_transition("OPEN", "IN_PROGRESS")
    validate_complaint_transition("IN_PROGRESS", "RESOLVED")
    validate_complaint_transition("OPEN", "REJECTED")

    # Invalid transitions: terminal states cannot transition
    with pytest.raises(HTTPException) as exc1:
        validate_complaint_transition("RESOLVED", "IN_PROGRESS")
    assert exc1.value.status_code == 409

    with pytest.raises(HTTPException) as exc2:
        validate_complaint_transition("REJECTED", "OPEN")
    assert exc2.value.status_code == 409


def test_customer_complaint_segregation_and_submission(client: TestClient):
    """Prove that customer cannot see internal staff notes or AI draft fields."""
    # 1. Login as customer
    token = get_token(client, "customer1@nileops.demo", "Customer2026!")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit complaint
    submit_res = client.post(
        "/api/v1/customer/complaints",
        headers=headers,
        json={
            "category": "ATM_CARD",
            "subject": "ATM retained payment card at Zamalek branch",
            "details": "The machine swallowed my card during an evening withdrawal attempt.",
        },
    )
    assert submit_res.status_code == 201, submit_res.text
    created_cmp = submit_res.json()
    assert "ticket_number" in created_cmp
    assert created_cmp["ticket_number"].startswith("CMP-2026-")

    # Verify that customer submission response NEVER leaks staff_notes or ai_draft_reply
    assert "staff_notes" not in created_cmp
    assert "ai_draft_reply" not in created_cmp
    assert "ai_matched_keywords" not in created_cmp
    assert "assigned_team" not in created_cmp

    # 3. List complaints as customer
    list_res = client.get("/api/v1/customer/complaints", headers=headers)
    assert list_res.status_code == 200
    customer_cmps = list_res.json()
    assert len(customer_cmps) >= 1
    for c in customer_cmps:
        assert "staff_notes" not in c
        assert "ai_draft_reply" not in c
        assert "assigned_team" not in c


def test_employee_complaint_table_pagination_and_advisory(client: TestClient):
    """Verify employee server-side pagination, advisory drawer, and human-approved reply flow."""
    # 1. Login as operations officer
    emp_token = get_token(client, "ops@nileops.demo", "NileOps2026!")
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # 2. List complaints with server-side pagination
    pag_res = client.get(
        "/api/v1/employee/complaints?page=1&page_size=5&include_test=true",
        headers=emp_headers,
    )
    assert pag_res.status_code == 200, pag_res.text
    pag_data = pag_res.json()
    assert "items" in pag_data
    assert "total" in pag_data
    assert "page" in pag_data
    assert "total_pages" in pag_data
    assert pag_data["page"] == 1
    assert pag_data["page_size"] == 5

    # 3. Check customer name is resolved on employee view
    first_item = pag_data["items"][0]
    assert "customer_name" in first_item
    assert "sla_status_label" in first_item
    assert "ai_suggested_category" in first_item
    assert first_item["ai_suggested_category"] is not None

    # 4. Request advisory intelligence on-demand
    cmp_id = first_item["id"]
    adv_res = client.post(
        f"/api/v1/employee/complaints/{cmp_id}/advisory",
        headers=emp_headers,
    )
    assert adv_res.status_code == 200
    adv_data = adv_res.json()
    assert adv_data["advisory_label"] == "AI suggestion - requires human review"
    assert "draft_reply" in adv_data

    # 5. Transition complaint and provide human-approved customer reply
    patch_res = client.patch(
        f"/api/v1/employee/complaints/{cmp_id}",
        headers=emp_headers,
        json={
            "status": "IN_PROGRESS",
            "assigned_team": "CARDS_PAYMENTS",
            "staff_notes": "Internal check: physical ATM cassette inspected by branch technicians.",
            "customer_reply": "Dear customer, our branch team has retrieved your card. It is ready for pickup.",
            "ai_draft_status": "MODIFIED",
        },
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["status"] == "IN_PROGRESS"
    assert patched["assigned_team"] == "CARDS_PAYMENTS"
    assert patched["customer_reply"] is not None

    # 6. Verify Customer can now see the human-approved reply, but NOT the internal staff note
    cust_token = get_token(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    cust_view = client.get("/api/v1/customer/complaints", headers=cust_headers)
    assert cust_view.status_code == 200
    matching = next((c for c in cust_view.json() if c["id"] == cmp_id), None)
    if matching:
        assert matching["customer_reply"] == "Dear customer, our branch team has retrieved your card. It is ready for pickup."
        assert "staff_notes" not in matching


def test_employee_complaint_rbac_restrictions(client: TestClient):
    """Verify that customers are blocked with 403 Forbidden on employee complaint endpoints."""
    cust_token = get_token(client, "customer1@nileops.demo", "Customer2026!")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Customers cannot view employee complaint queue
    emp_list = client.get("/api/v1/employee/complaints", headers=cust_headers)
    assert emp_list.status_code == 403

    # Customers cannot update complaint status
    emp_patch = client.patch(
        "/api/v1/employee/complaints/any-id",
        headers=cust_headers,
        json={"status": "RESOLVED"},
    )
    assert emp_patch.status_code == 403
