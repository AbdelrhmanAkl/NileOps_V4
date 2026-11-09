"""Tests for IBAN / Account Number Masking and Customer Data Protection."""

import pytest
from starlette.testclient import TestClient
from app.schemas.banking import AccountOut
from datetime import datetime, timezone


def test_account_out_schema_masks_iban():
    """Verify AccountOut schema strictly masks middle digits of account number."""
    raw_iban = "EG980001000100000000112233"
    acc = AccountOut(
        id="acc-test-01",
        account_number=raw_iban,
        account_type="savings",
        currency="EGP",
        balance=1000.0,
        interest_rate=10.0,
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
    )
    # Must preserve prefix and suffix
    assert acc.account_number.startswith("EG98")
    assert acc.account_number.endswith("2233")
    # Must NOT expose full middle digits
    assert "0001000100000000" not in acc.account_number
    assert "•" in acc.account_number
    assert len(acc.account_number) == len(raw_iban)


def test_customer_accounts_endpoint_returns_masked_iban(client: TestClient):
    """Verify /api/v1/customer/accounts never exposes raw unmasked IBANs."""
    # Login as customer 1
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "customer1@nileops.demo", "password": "Customer2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch accounts
    acc_resp = client.get("/api/v1/customer/accounts", headers=headers)
    assert acc_resp.status_code == 200
    accounts = acc_resp.json()
    assert len(accounts) > 0

    for acc in accounts:
        num = acc["account_number"]
        assert "•" in num, f"Account number {num} was not masked!"
        # Assert full raw seed IBANs are never exposed verbatim
        assert num != "EG980001000100000000112233"
        assert num != "EG980001000100000000223344"
        assert num != "EG980001000100000000334455"

