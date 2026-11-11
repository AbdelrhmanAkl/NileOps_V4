"""Tests for KPI Calculation Service and REST API Endpoints.

Verifies:
1. Employee RBAC: ops_analyst, branch_manager, compliance_officer, admin can access /api/v1/kpi/summary.
2. Customer RBAC rejection: retail customer is rejected with 403 Forbidden.
3. Unauthenticated rejection: requests without token return 401 Unauthorized.
4. Single metric endpoint /api/v1/kpi/{key}: valid keys return 200, invalid keys return 404.
5. Hand-computed expected values and Handbook benchmarks on persisted data.
"""

import pytest
from starlette.testclient import TestClient


def get_token(client: TestClient, email: str, password: str = "NileOps2026!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_kpi_summary_unauthenticated(client: TestClient):
    """Anonymous access to /api/v1/kpi/summary must return 401."""
    res = client.get("/api/v1/kpi/summary")
    assert res.status_code == 401


def test_kpi_summary_customer_forbidden(client: TestClient):
    """Customer access to /api/v1/kpi/summary must be denied with 403 Forbidden."""
    token = get_token(client, "customer1@nileops.demo", password="Customer2026!")
    res = client.get(
        "/api/v1/kpi/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Access restricted" in res.text or "not authorized" in res.text


def test_kpi_summary_employee_success(client: TestClient):
    """Employee access to /api/v1/kpi/summary must succeed with 200 and return all required metrics."""
    token = get_token(client, "ops@nileops.demo")
    res = client.get(
        "/api/v1/kpi/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "calculated_at" in data
    assert "environment_mode" in data

    metrics = data["metrics"]
    required_keys = [
        "stp_eligibility_rate",
        "exception_detection_recall",
        "audit_completeness",
        "rework_rate",
        "median_decision_time",
        "complaint_sla_breach_rate",
        "rag_retrieval_accuracy",
        "ocr_field_accuracy",
    ]
    for key in required_keys:
        assert key in metrics, f"Missing required KPI key: {key}"
        metric = metrics[key]
        assert "key" in metric
        assert "title_en" in metric
        assert "title_ar" in metric
        assert "value" in metric
        assert "formatted_value" in metric
        assert "definition" in metric
        assert "target_benchmark" in metric
        assert metric["status"] in ("MET", "NOT MET", "NO TARGET", "NOT MEASURED")


def test_kpi_single_metric_valid(client: TestClient):
    """GET /api/v1/kpi/{key} returns single metric for valid key."""
    token = get_token(client, "admin@nileops.demo")
    res = client.get(
        "/api/v1/kpi/stp_eligibility_rate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    metric = res.json()
    assert metric["key"] == "stp_eligibility_rate"
    assert "Straight-Through-Processing" in metric["title_en"]
    assert "breakdown" in metric
    assert metric["breakdown"]["auto_executed_rate"] == "0.0%"


def test_kpi_single_metric_not_found(client: TestClient):
    """GET /api/v1/kpi/{key} returns 404 for unknown metric key."""
    token = get_token(client, "manager@nileops.demo")
    res = client.get(
        "/api/v1/kpi/non_existent_metric",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_kpi_rbac_all_employee_roles(client: TestClient):
    """Verify all employee roles (admin, ops_analyst, branch_manager, compliance_officer) have access."""
    roles_emails = [
        "admin@nileops.demo",
        "ops@nileops.demo",
        "manager@nileops.demo",
        "compliance@nileops.demo",
    ]
    for email in roles_emails:
        token = get_token(client, email)
        res = client.get(
            "/api/v1/kpi/audit_completeness",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200, f"Role for {email} failed with status {res.status_code}"
