"""Pytest Configuration and Fixtures for NileOps Backend."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client fixture for FastAPI app."""
    return TestClient(app)
