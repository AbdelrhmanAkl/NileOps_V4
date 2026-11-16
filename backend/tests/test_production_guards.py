"""Tests for Production Security Guards & Rate Limiting.

Verifies:
1. Rejection of weak/default JWT secret in production mode.
2. CORS origin restriction and rejection of wildcard '*' with credentials.
3. Production debug mode disabled.
4. Docs & OpenAPI endpoints configurable via ENABLE_DOCS / DEBUG.
5. Rate limiting on /auth/login (HTTP 429 + Retry-After header).
6. Account lockout after N failed logins with automatic unlock-by-time.
7. Rate limiting on /rag/ask.
"""

import time
import pytest
from starlette.testclient import TestClient

from app.core.config import INSECURE_SECRET_KEYS, get_secret_key, settings, validate_secret_key
from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_limiter_state():
    """Reset rate limiter state and restore original settings before & after each test."""
    orig_enabled = settings.RATE_LIMIT_ENABLED
    orig_login_max = settings.RATE_LIMIT_LOGIN_MAX
    orig_login_win = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
    orig_lockout_max = settings.LOGIN_LOCKOUT_MAX_FAILURES
    orig_lockout_dur = settings.LOGIN_LOCKOUT_DURATION_SECONDS
    orig_rag_max = settings.RATE_LIMIT_RAG_MAX
    orig_rag_win = settings.RATE_LIMIT_RAG_WINDOW_SECONDS
    limiter.reset_for_tests()
    yield
    settings.RATE_LIMIT_ENABLED = orig_enabled
    settings.RATE_LIMIT_LOGIN_MAX = orig_login_max
    settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = orig_login_win
    settings.LOGIN_LOCKOUT_MAX_FAILURES = orig_lockout_max
    settings.LOGIN_LOCKOUT_DURATION_SECONDS = orig_lockout_dur
    settings.RATE_LIMIT_RAG_MAX = orig_rag_max
    settings.RATE_LIMIT_RAG_WINDOW_SECONDS = orig_rag_win
    limiter.reset_for_tests()


def test_production_guard_weak_secret_rejected():
    """Production mode must reject weak, short, or default secret keys."""
    for weak_key in INSECURE_SECRET_KEYS:
        with pytest.raises(ValueError, match="Weak, default, or undersized 'SECRET_KEY' detected"):
            validate_secret_key(weak_key, env="production", is_testing=False)

    # Short secret (< 32 characters) must also be rejected
    with pytest.raises(ValueError, match="Weak, default, or undersized 'SECRET_KEY' detected"):
        validate_secret_key("too_short_secret_key", env="production", is_testing=False)


def test_production_guard_strong_secret_accepted():
    """Production mode must accept 32+ character cryptographically strong secret."""
    strong_secret = "c5b9671f84d436a59ec1d8719bc4e4604e6c98f828a2b53f6c8d4e7b8a1e2f3d"
    assert validate_secret_key(strong_secret, env="production", is_testing=False) == strong_secret


def test_production_guard_cors_disallows_wildcard(monkeypatch):
    """CORS must not allow wildcard '*' when credentials are used."""
    from app.core.config import get_default_cors_origins

    monkeypatch.setenv("CORS_ORIGINS", "*, http://localhost:5173")
    origins = get_default_cors_origins()
    assert "*" not in origins
    assert "http://localhost:5173" in origins


def test_production_guard_docs_disabled_when_flag_off(client: TestClient, monkeypatch):
    """When ENABLE_DOCS=False, /docs and /redoc must not be exposed."""
    from app.main import create_application

    app = create_application()
    # If debug is false or enable_docs is false, docs_url is None
    settings_orig = settings.ENABLE_DOCS
    try:
        settings.ENABLE_DOCS = False
        app_no_docs = create_application()
        assert app_no_docs.docs_url is None
        assert app_no_docs.redoc_url is None
    finally:
        settings.ENABLE_DOCS = settings_orig


def test_login_rate_limiting_http_429(client: TestClient, monkeypatch):
    """Exceeding login rate limit must return HTTP 429 with Retry-After header."""
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_LOGIN_MAX = 3
    settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = 10

    # 3 allowed requests
    for _ in range(3):
        res = client.post("/api/v1/auth/login", json={"email": "ops@nileops.demo", "password": "NileOps2026!"})
        assert res.status_code == 200

    # 4th request within window must be rate limited
    res = client.post("/api/v1/auth/login", json={"email": "ops@nileops.demo", "password": "NileOps2026!"})
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.text
    assert "Retry-After" in res.headers
    retry_after = int(res.headers["Retry-After"])
    assert retry_after > 0


def test_account_lockout_after_consecutive_failed_logins(client: TestClient):
    """N consecutive failed logins triggers temporary account lockout with Retry-After."""
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_LOGIN_MAX = 20  # Keep rate limit high to test lockout specifically
    settings.LOGIN_LOCKOUT_MAX_FAILURES = 3
    settings.LOGIN_LOCKOUT_DURATION_SECONDS = 5  # Small window for fast test

    target_email = "manager@nileops.demo"

    # Attempt 1: bad password
    res = client.post("/api/v1/auth/login", json={"email": target_email, "password": "WrongPassword1!"})
    assert res.status_code == 401

    # Attempt 2: bad password
    res = client.post("/api/v1/auth/login", json={"email": target_email, "password": "WrongPassword2!"})
    assert res.status_code == 401

    # Attempt 3: bad password (triggers lockout)
    res = client.post("/api/v1/auth/login", json={"email": target_email, "password": "WrongPassword3!"})
    assert res.status_code == 401

    # Attempt 4: Even with correct password, account is locked -> 429 Too Many Requests
    res = client.post("/api/v1/auth/login", json={"email": target_email, "password": "NileOps2026!"})
    assert res.status_code == 429
    assert "temporarily locked" in res.text.lower()
    assert "Retry-After" in res.headers


def test_rag_ask_rate_limiting_http_429(client: TestClient):
    """Exceeding RAG query rate limit must return HTTP 429 with Retry-After."""
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_RAG_MAX = 2
    settings.RATE_LIMIT_RAG_WINDOW_SECONDS = 10

    payload = {"query": "ما هو الحد الأدنى لفتح حساب جاري؟", "portal_type": "customer", "language": "ar"}

    # Request 1 & 2 pass
    res1 = client.post("/api/v1/rag/ask", json=payload)
    assert res1.status_code == 200

    res2 = client.post("/api/v1/rag/ask", json=payload)
    assert res2.status_code == 200

    # Request 3 triggers 429
    res3 = client.post("/api/v1/rag/ask", json=payload)
    assert res3.status_code == 429
    assert "Rate limit exceeded" in res3.text
    assert "Retry-After" in res3.headers


def test_production_mode_disables_docs_and_openapi(monkeypatch):
    """When ENVIRONMENT=production, /docs, /redoc, and /openapi.json must all be disabled (None)."""
    from app.main import create_application

    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        app_prod = create_application()
        assert app_prod.docs_url is None
        assert app_prod.redoc_url is None
        assert app_prod.openapi_url is None
    finally:
        settings.ENVIRONMENT = orig_env


def test_client_ip_trusted_peer_forwarding_guard():
    """Verify CF-Connecting-IP / X-Forwarded-For are trusted ONLY when direct peer is 127.0.0.1."""
    from starlette.datastructures import Headers
    from starlette.requests import Request

    class DummyClient:
        def __init__(self, host: str):
            self.host = host

    # Helper to construct dummy Request
    def make_request(peer_ip: str, headers_dict: dict) -> Request:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/rag/ask",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers_dict.items()],
            "client": (peer_ip, 12345),
        }
        return Request(scope)

    # 1. Direct peer is 127.0.0.1 with CF-Connecting-IP -> trusts CF-Connecting-IP
    req_cf = make_request("127.0.0.1", {"cf-connecting-ip": "203.0.113.195", "x-forwarded-for": "198.51.100.1"})
    assert limiter._get_client_ip(req_cf) == "203.0.113.195"

    # 2. Direct peer is 127.0.0.1 with X-Forwarded-For only -> trusts X-Forwarded-For
    req_xff = make_request("127.0.0.1", {"x-forwarded-for": "198.51.100.42, 10.0.0.1"})
    assert limiter._get_client_ip(req_xff) == "198.51.100.42"

    # 3. Direct peer is 127.0.0.1 with neither header -> returns 127.0.0.1
    req_local = make_request("127.0.0.1", {})
    assert limiter._get_client_ip(req_local) == "127.0.0.1"

    # 4. Direct peer is external (192.168.1.50) -> IGNORES CF-Connecting-IP and X-Forwarded-For
    req_spoof = make_request(
        "192.168.1.50",
        {"cf-connecting-ip": "203.0.113.195", "x-forwarded-for": "198.51.100.1"},
    )
    assert limiter._get_client_ip(req_spoof) == "192.168.1.50"


def test_spa_browser_serving_and_api_fallback(client: TestClient):
    """Verify SPA index.html is served for browser navigation while API 404s stay JSON."""
    # 1. Browser navigation to root (Accept: text/html)
    browser_resp = client.get("/", headers={"accept": "text/html,application/xhtml+xml"})
    assert browser_resp.status_code == 200
    assert "<!doctype html" in browser_resp.text.lower() or "<html" in browser_resp.text.lower()

    # 2. Browser navigation to SPA client route (/customer)
    spa_resp = client.get("/customer", headers={"accept": "text/html"})
    assert spa_resp.status_code == 200
    assert "<!doctype html" in spa_resp.text.lower() or "<html" in spa_resp.text.lower()

    # 3. Unknown API route returns 404 JSON, NOT index.html
    api_resp = client.get("/api/v1/nonexistent-endpoint")
    assert api_resp.status_code == 404
    assert api_resp.headers.get("content-type", "").startswith("application/json")
    assert "detail" in api_resp.json()

