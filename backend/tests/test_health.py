"""NileOps Phase 1 Automated Health-Check & Scaffolding Verification Tests."""

from starlette.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Verify GET /health returns 200 OK and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NileOps Backend"
    assert data["version"] == "1.0.0"


def test_root_endpoint(client: TestClient):
    """Verify root GET / returns active platform metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_api_v1_status(client: TestClient):
    """Verify API v1 prefix is correctly mounted."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert data["status"] == "active"


def test_production_secret_key_guard(monkeypatch):
    """Verify production configuration refuses weak or default JWT SECRET_KEY."""
    import os
    import pytest
    from app.core.config import get_secret_key

    # 1. Under production with default insecure key, must raise ValueError
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "change-this-insecure-key-to-a-secure-256-bit-random-secret")
    # Temporarily bypass the test guard detection to simulate production runtime
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("NILEOPS_TEST_MODE", raising=False)
    import sys
    orig_pytest = sys.modules.get("pytest")
    try:
        sys.modules.pop("pytest", None)
        with pytest.raises(ValueError) as excinfo:
            get_secret_key()
        assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)
        assert "SECRET_KEY" in str(excinfo.value)

        # 2. Under production with short/weak key (< 32 chars)
        monkeypatch.setenv("SECRET_KEY", "weak-short-key")
        with pytest.raises(ValueError):
            get_secret_key()

        # 3. Under production with strong 32+ char key
        strong_key = "a-cryptographically-secure-production-secret-key-32chars"
        monkeypatch.setenv("SECRET_KEY", strong_key)
        assert get_secret_key() == strong_key
    finally:
        if orig_pytest:
            sys.modules["pytest"] = orig_pytest
