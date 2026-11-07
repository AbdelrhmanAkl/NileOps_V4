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
