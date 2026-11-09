"""Unit and Security Tests for NileOps OCR Phase 2.1:
- Expanded Egyptian Address Extraction & Disambiguation
- Multi-Layer WebP Decoding and Security Validation
"""

import io
import pytest
from PIL import Image

from app.services.image_pipeline import (
    ImageOCRPipeline,
    image_ocr_pipeline,
    is_valid_image_header,
    JPEG_MAGIC,
    PNG_MAGIC,
    WEBP_RIFF,
    WEBP_MAGIC,
)


# ==============================================================================
# 1. Address Extraction & Disambiguation Tests
# ==============================================================================

class TestAddressExtraction:
    """Test the expanded Egyptian address parser for precision and false-positive immunity."""

    def test_valid_urban_street_address(self):
        """Verify standard urban street address is correctly classified."""
        tokens = ["١٥ شارع طلعت حرب - قصر النيل - القاهرة"]
        scores = [0.94]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is not None
        assert "طلعت حرب" in fields["address"]
        assert fields["address_conf"] == 0.94
        assert fields["name"] is None

    def test_valid_rural_center_village_address(self):
        """Verify rural center and village address is correctly classified."""
        tokens = ["قرية الدير مركز طوخ القليوبية"]
        scores = [0.89]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is not None
        assert "طوخ" in fields["address"]
        assert fields["address_conf"] == 0.89
        assert fields["name"] is None

    def test_valid_building_and_block_address(self):
        """Verify multi-unit residential building and block address is recognized."""
        tokens = ["عمارة 14 بلوك 5 مساكن العبور الحي الاول"]
        scores = [0.92]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is not None
        assert "عمارة" in fields["address"]
        assert fields["name"] is None

    def test_multi_line_address_continuation(self):
        """Verify address spanning multiple OCR tokens is joined with mean confidence."""
        tokens = ["١٢ شارع الجمهورية", "قسم قصر النيل", "القاهرة"]
        scores = [0.90, 0.85, 0.95]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is not None
        assert "شارع الجمهورية" in fields["address"]
        assert "القاهرة" in fields["address"]
        assert round(fields["address_conf"], 2) == 0.90

    def test_reject_ambiguous_name_with_address_keyword(self):
        """Verify personal name containing common address word ('السلام') is NOT classified as address."""
        tokens = ["محمد عبد السلام علي إبراهيم"]
        scores = [0.91]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is None
        assert fields["name"] == "محمد عبد السلام علي إبراهيم"
        assert fields["name_conf"] == 0.91

    def test_reject_ambiguous_personal_name_with_city_word(self):
        """Verify citizen name starting with 'مدينة' or 'قاسم' without location structure is preserved as name."""
        tokens = ["مدينة مصطفى كامل عبد الله"]
        scores = [0.88]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is None
        assert fields["name"] is not None

    def test_reject_isolated_incomplete_address_fragments(self):
        """Verify isolated single-word fragments like 'ش' or 'مدينة' are rejected as addresses."""
        tokens = ["ش"]
        scores = [0.70]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["address"] is None

        tokens_single_word = ["مدينة"]
        fields2 = image_ocr_pipeline.extract_fields_from_ocr(tokens_single_word, scores)
        assert fields2["address"] is None

    def test_filter_administrative_national_headers(self):
        """Verify civil registry and republic headers are completely ignored and not added to name or address."""
        tokens = [
            "جمهورية مصر العربية",
            "وزارة الداخلية",
            "قطاع مصلحة الاحوال المدنية",
            "بطاقة تحقيق الشخصية",
            "أحمد حسن علي",
            "١٠ شارع النيل الجيزة",
        ]
        scores = [0.99, 0.99, 0.98, 0.99, 0.95, 0.92]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert fields["name"] == "أحمد حسن علي"
        assert "شارع النيل" in fields["address"]
        assert "جمهورية" not in (fields["name"] or "")
        assert "الداخلية" not in (fields["address"] or "")

    def test_preserve_raw_tokens_and_metadata(self):
        """Verify original OCR tokens and confidence scores are fully preserved in output dictionary."""
        tokens = ["أحمد محمود", "شارع النيل القاهرة"]
        scores = [0.88, 0.94]
        fields = image_ocr_pipeline.extract_fields_from_ocr(tokens, scores)
        assert len(fields["raw_tokens"]) == 2
        assert fields["raw_tokens"][0]["text"] == "أحمد محمود"
        assert fields["raw_tokens"][0]["score"] == 0.88
        assert fields["raw_tokens"][1]["text"] == "شارع النيل القاهرة"
        assert fields["raw_tokens"][1]["score"] == 0.94


# ==============================================================================
# 2. WebP Validation & Decoding Security Tests
# ==============================================================================

class TestWebPSupportAndSecurity:
    """Test WebP format ingestion, magic-bytes verification, and tamper resistance."""

    @staticmethod
    def _create_synthetic_webp(width=200, height=150, color=(0, 128, 255)) -> bytes:
        img = Image.new("RGB", (width, height), color=color)
        buf = io.BytesIO()
        img.save(buf, format="WEBP")
        return buf.getvalue()

    def test_valid_webp_magic_bytes_detection(self):
        """Verify correct recognition of RIFF....WEBP format signature."""
        webp_bytes = self._create_synthetic_webp()
        assert is_valid_image_header(webp_bytes) is True
        assert webp_bytes[:4] == WEBP_RIFF
        assert webp_bytes[8:12] == WEBP_MAGIC

    def test_valid_webp_load_and_validate(self):
        """Verify valid in-memory WebP image decodes successfully with correct metadata."""
        webp_bytes = self._create_synthetic_webp(width=320, height=240)
        img, meta = ImageOCRPipeline.load_and_validate_image(webp_bytes)
        assert img is not None
        assert meta["is_valid"] is True
        assert meta["width"] == 320
        assert meta["height"] == 240
        assert meta["channels"] == 3
        assert meta["error"] is None

    def test_reject_spoofed_riff_not_webp(self):
        """Verify spoofed RIFF header with non-WEBP tag (e.g. RIFF....WAVE) is rejected."""
        spoofed_riff = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
        assert is_valid_image_header(spoofed_riff) is False
        img, meta = ImageOCRPipeline.load_and_validate_image(spoofed_riff)
        assert img is None
        assert meta["is_valid"] is False
        assert "Invalid image format" in meta["error"]

    def test_reject_malformed_truncated_webp(self):
        """Verify valid RIFF....WEBP header with truncated/corrupted payload fails decode safely."""
        corrupted_webp = b"RIFF\x20\x00\x00\x00WEBPVP8 \x10\x00\x00\x00" + b"\x00" * 8
        img, meta = ImageOCRPipeline.load_and_validate_image(corrupted_webp)
        assert img is None
        assert meta["is_valid"] is False
        assert "decoding failed" in meta["error"].lower()

    def test_reject_undersized_webp_header(self):
        """Verify WebP header shorter than 12 bytes is rejected."""
        short_header = b"RIFF\x00\x00"
        assert is_valid_image_header(short_header) is False
        img, meta = ImageOCRPipeline.load_and_validate_image(short_header)
        assert img is None
        assert meta["is_valid"] is False

    def test_reject_oversized_webp_file(self):
        """Verify WebP file exceeding 10MB limit is rejected."""
        oversized = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * (10 * 1024 * 1024 + 100)
        img, meta = ImageOCRPipeline.load_and_validate_image(oversized)
        assert img is None
        assert meta["is_valid"] is False
        assert "exceeds maximum permitted limit" in meta["error"]

    def test_reject_oversized_webp_dimensions(self):
        """Verify WebP exceeding 4096px dimension limit is rejected as decompression bomb defense."""
        # 4200 x 100 pixels
        wide_webp = self._create_synthetic_webp(width=4200, height=100)
        img, meta = ImageOCRPipeline.load_and_validate_image(wide_webp)
        assert img is None
        assert meta["is_valid"] is False
        assert "exceed maximum permitted limit" in meta["error"]

    def test_preserve_jpeg_and_png_validation(self):
        """Verify JPEG and PNG validation behavior remains completely intact."""
        # JPEG
        jpeg_buf = io.BytesIO()
        Image.new("RGB", (100, 100), color="red").save(jpeg_buf, format="JPEG")
        jpeg_bytes = jpeg_buf.getvalue()
        assert is_valid_image_header(jpeg_bytes) is True
        img_j, meta_j = ImageOCRPipeline.load_and_validate_image(jpeg_bytes)
        assert img_j is not None and meta_j["is_valid"] is True

        # PNG
        png_buf = io.BytesIO()
        Image.new("RGB", (100, 100), color="blue").save(png_buf, format="PNG")
        png_bytes = png_buf.getvalue()
        assert is_valid_image_header(png_bytes) is True
        img_p, meta_p = ImageOCRPipeline.load_and_validate_image(png_bytes)
        assert img_p is not None and meta_p["is_valid"] is True

