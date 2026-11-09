"""Tests for NileOps Production RAG Pipeline.

Validates:
1. Health check and vector database connectivity.
2. Grounded policy answers, citations with expandable passage text, and fallback flag.
3. Strict portal isolation and zero customer-portal leakage.
4. Abstention on off-topic / out-of-domain inquiries.
5. Strict RBAC & Authentication enforcement on employee portal queries.
"""

import pytest
from starlette.testclient import TestClient


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and return a bearer JWT token."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Authentication failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_rag_health(client: TestClient):
    """Verify Qdrant health check endpoint."""
    resp = client.get("/api/v1/rag/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "ok")
    assert data["qdrant"]["connected"] is True


def test_rag_grounded_answer_and_citations(client: TestClient):
    """Verify customer query returns grounded policy answer, citation, passage, and fallback flag."""
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
    assert "fallback_used" in data
    assert isinstance(data["fallback_used"], bool)
    assert len(data["citations"]) >= 1
    top_citation = data["citations"][0]
    assert top_citation["code"] == "POL-RETAIL-001"
    assert top_citation["portal_access"] == "customer"
    assert "POL-RETAIL-001" in data["answer"]
    # Verify expandable source passage is present
    assert "passage" in top_citation
    assert top_citation["passage"] is not None
    assert len(top_citation["passage"]) > 10


def test_rag_portal_isolation_and_leakage(client: TestClient):
    """Verify customer portal cannot retrieve internal employee KYC policies (0.0% leakage)."""
    # 1. Search internal employee procedure as customer
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

    # 2. Search as authenticated employee
    emp_token = get_auth_token(client, "ops@nileops.demo", "NileOps2026!")
    emp_headers = {"Authorization": f"Bearer {emp_token}"}
    emp_payload = {
        "query": "KYC customer identification and verification process",
        "portal_type": "employee",
        "language": "en",
        "threshold": 0.20,
    }
    emp_resp = client.post("/api/v1/rag/ask", json=emp_payload, headers=emp_headers)
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
    assert data["fallback_used"] is False


def test_rag_fallback_flag(client: TestClient):
    """Verify fallback_used flag is True when LLM is unavailable and extractive answer is returned."""
    payload = {
        "query": "What is the initial deposit requirement for checking accounts?",
        "portal_type": "customer",
        "language": "en",
        "threshold": 0.15,
    }
    resp = client.post("/api/v1/rag/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["abstained"] is False
    # In test environment where Ollama LLM is not running, fallback_used must be True
    assert data["fallback_used"] is True
    assert "Based on the approved banking policy" in data["answer"]


def test_rag_auth_and_rbac_guards(client: TestClient):
    """Verify strict RBAC guards prevent unauthorized access to employee policies."""
    emp_payload = {
        "query": "What are the rules for verifying Egyptian National IDs?",
        "portal_type": "employee",
        "language": "en",
        "threshold": 0.15,
    }

    # 1. Anonymous request with portal_type=employee -> 403 Forbidden & Zero KYC Leakage
    res_anon = client.post("/api/v1/rag/ask", json=emp_payload)
    assert res_anon.status_code == 403
    assert "Employee authentication required" in res_anon.json()["detail"] or "Authentication required" in res_anon.json()["detail"]
    assert "POL-KYC-001" not in res_anon.text
    assert "14-digit" not in res_anon.text.lower()
    assert "governorate" not in res_anon.text.lower()

    # 2. Customer token with portal_type=employee -> 403 Forbidden & Zero KYC Leakage
    cust_token = get_auth_token(client, "customer1@nileops.demo", "Customer2026!")
    res_cust = client.post(
        "/api/v1/rag/ask",
        json=emp_payload,
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res_cust.status_code == 403
    assert "Customers are strictly forbidden" in res_cust.json()["detail"]
    assert "POL-KYC-001" not in res_cust.text
    assert "14-digit" not in res_cust.text.lower()
    assert "governorate" not in res_cust.text.lower()

    # 3. Employee token with portal_type=employee -> 200 OK
    emp_token = get_auth_token(client, "ops@nileops.demo", "NileOps2026!")
    res_emp = client.post(
        "/api/v1/rag/ask",
        json=emp_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert res_emp.status_code == 200
    assert res_emp.json()["abstained"] is False


def test_rag_pol_test_retrieval_guard(client: TestClient):
    """Verify retrieval-level defense-in-depth guard strictly excludes POL-TEST-* policies."""
    payload = {
        "query": "يجوز للموظفين الإبلاغ بسرية عن أي أنشطة أو تسوية أخطاء السحب",
        "portal_type": "customer",
        "language": "ar",
        "threshold": 0.10,
    }
    resp = client.post("/api/v1/rag/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    for cit in data.get("citations", []):
        assert not cit["code"].startswith("POL-TEST-"), f"Retrieval leaked test policy: {cit['code']}"
    assert "POL-TEST-" not in data.get("answer", "")


def test_qdrant_test_isolation_guard():
    """Verify test suites strictly run against isolated _test Qdrant collection and hard-fail otherwise."""
    from app.services.vector_store import qdrant_service, QdrantVectorService
    # Ensure current test service collection strictly ends with _test
    assert qdrant_service.collection_name.endswith("_test")
    assert qdrant_service.collection_name == "nileops_kb_test"
    assert qdrant_service.collection_name != "nileops_kb"

    # Verify hard-fail guard if non-test collection name is attempted under test environment
    with pytest.raises(RuntimeError) as exc_info:
        QdrantVectorService(collection_name="nileops_kb")
    assert "CRITICAL TEST ISOLATION FAILURE" in str(exc_info.value)
    assert "nileops_kb" in str(exc_info.value)
