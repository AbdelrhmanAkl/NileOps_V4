"""Tests for NileOps Production RAG Pipeline."""

import pytest
from starlette.testclient import TestClient


def test_rag_health(client: TestClient):
    """Verify Qdrant health check endpoint."""
    resp = client.get("/api/v1/rag/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "ok")
    assert data["qdrant"]["connected"] is True


def test_rag_grounded_answer_and_citations(client: TestClient):
    """Verify customer query returns grounded policy answer and citation."""
    payload = {
        "query": "ما هي متطلبات فتح حساب جاري للأفراد؟",
        "portal_type": "customer",
        "language": "ar",
        "threshold": 0.15,
    }
    resp = client.post("/api/v1/rag/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["abstained"] is False
    assert len(data["citations"]) >= 1
    top_citation = data["citations"][0]
    assert top_citation["code"] == "POL-RETAIL-001"
    assert top_citation["portal_access"] == "customer"
    assert "POL-RETAIL-001" in data["answer"]


def test_rag_portal_isolation(client: TestClient):
    """Verify customer portal cannot retrieve internal employee KYC policies."""
    # Search internal employee procedure as customer
    cust_payload = {
        "query": "KYC customer identification and verification process",
        "portal_type": "customer",
        "language": "en",
        "threshold": 0.20,
    }
    cust_resp = client.post("/api/v1/rag/ask", json=cust_payload)
    assert cust_resp.status_code == 200
    cust_data = cust_resp.json()
    # Ensure employee-only POL-KYC-001 is NEVER returned to customer portal
    for cit in cust_data.get("citations", []):
        assert cit["code"] != "POL-KYC-001"
        assert cit["portal_access"] == "customer"

    # Search the same as employee
    emp_payload = {
        "query": "KYC customer identification and verification process",
        "portal_type": "employee",
        "language": "en",
        "threshold": 0.20,
    }
    emp_resp = client.post("/api/v1/rag/ask", json=emp_payload)
    assert emp_resp.status_code == 200
    emp_data = emp_resp.json()
    assert emp_data["abstained"] is False
    emp_codes = [c["code"] for c in emp_data["citations"]]
    assert "POL-KYC-001" in emp_codes


def test_rag_abstention_on_off_topic_query(client: TestClient):
    """Verify system strictly abstains when inquiry is not in approved policies."""
    payload = {
        "query": "كيف أقوم بتغيير زيت محرك السيارة الرياضية؟",
        "portal_type": "customer",
        "language": "ar",
        "threshold": 0.20,
    }
    resp = client.post("/api/v1/rag/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["abstained"] is True
    assert data["confidence_score"] == 0.0
    assert len(data["citations"]) == 0
    assert "لم أتمكن من العثور على معلومات كافية" in data["answer"]
