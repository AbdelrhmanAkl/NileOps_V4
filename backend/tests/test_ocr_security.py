"""Upload Security & Hardening Tests for Image OCR Endpoint."""

import io
import pytest
from PIL import Image
from starlette.testclient import TestClient


def test_reject_upload_exceeding_max_size(client: TestClient):
    """Verify uploads > 10MB are rejected with HTTP 413."""
    oversized_content = b"\xFF\xD8\xFF" + b"\x00" * (10 * 1024 * 1024 + 100)
    resp = client.post(
        "/api/v1/ocr/process-image-card",
        files={"file": ("huge_card.jpg", oversized_content, "image/jpeg")},
    )
    assert resp.status_code == 413
    assert "exceeds maximum permitted limit" in resp.json()["detail"]


def test_reject_invalid_magic_bytes(client: TestClient):
    """Verify non-JPEG/PNG/WebP content with fake extension is rejected with HTTP 400."""
    fake_content = b"<html><script>alert(1)</script></html>"
    resp = client.post(
        "/api/v1/ocr/process-image-card",
        files={"file": ("malicious.jpg", fake_content, "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "Expected verified JPEG, PNG, or WebP magic bytes" in resp.json()["detail"]


def test_reject_undersized_content(client: TestClient):
    """Verify file content < 12 bytes is rejected with HTTP 400."""
    resp = client.post(
        "/api/v1/ocr/process-image-card",
        files={"file": ("empty.jpg", b"\xFF\xD8", "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "too small" in resp.json()["detail"]


def test_reject_corrupted_image(client: TestClient):
    """Verify corrupted image with valid SOI but truncated stream returns HTTP 400."""
    corrupted_jpeg = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30
    resp = client.post(
        "/api/v1/ocr/process-image-card",
        files={"file": ("corrupted.jpg", corrupted_jpeg, "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "decoding failed" in resp.json()["detail"].lower()


def test_reject_decompression_bomb_dimensions(client: TestClient):
    """Verify synthetic image exceeding 4096px dimension limit returns HTTP 422."""
    buf = io.BytesIO()
    # Create 5000 x 10 image (exceeds 4096 max dimension)
    img = Image.new("RGB", (5000, 10), color="white")
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/v1/ocr/process-image-card",
        files={"file": ("wide_bomb.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert resp.status_code == 422
    assert "exceed maximum permitted limit of 4096x4096" in resp.json()["detail"]


def test_response_pii_masking_invariant(client: TestClient):
    """Verify that National ID is always masked in the public API response."""
    import os
    synthetic_card_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_cards", "card_01_clean.png")
    )
    if not os.path.exists(synthetic_card_path):
        synthetic_card_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_cards", "clean_synthetic_card.png")
        )
    with open(synthetic_card_path, "rb") as f:
        resp = client.post(
            "/api/v1/ocr/process-image-card",
            files={"file": ("synthetic_card.png", f.read(), "image/png")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "****" in data["masked_national_id"]
    # Ensure raw 14-digit unmasked sequences are never exposed in the response
    import re
    assert not re.search(r"\b\d{14}\b", str(data))
    assert data["identity_verification_status"] == "NOT_VERIFIED"
