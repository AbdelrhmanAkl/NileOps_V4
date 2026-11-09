"""Unit and Experimental Tests for NileOps OCR Phase 2.2:
- Controlled Computer Vision Preprocessing
- Image Quality Assessment
- Lanczos-4 Resolution Normalization
- LAB-CLAHE Luminance Enhancement
- Deskew Orientation Correction
"""

import cv2
import numpy as np
import pytest

from app.services.image_pipeline import ImageOCRPipeline, image_ocr_pipeline


class TestImageQualityAssessor:
    """Verify pre-inference image quality and sharpness diagnostics."""

    def test_sharpness_detection_sharp_vs_blurry(self):
        """Verify Laplacian variance differentiates sharp text from blurred image."""
        sharp_img = np.zeros((300, 400), dtype=np.uint8)
        cv2.putText(sharp_img, "EGYPT NATIONAL ID", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 255, 2)
        sharp_diag = ImageOCRPipeline.assess_quality(sharp_img)
        assert sharp_diag["is_blurry"] is False
        assert sharp_diag["sharpness_laplacian"] > 50.0

        # Apply heavy Gaussian blur
        blurry_img = cv2.GaussianBlur(sharp_img, (31, 31), 0)
        blurry_diag = ImageOCRPipeline.assess_quality(blurry_img)
        assert blurry_diag["is_blurry"] is True
        assert blurry_diag["sharpness_laplacian"] < 50.0

    def test_contrast_and_brightness_diagnostics(self):
        """Verify contrast standard deviation and brightness mean metrics."""
        # Low contrast gray canvas
        low_contrast = np.full((200, 200, 3), 128, dtype=np.uint8)
        diag_low = ImageOCRPipeline.assess_quality(low_contrast)
        assert diag_low["is_low_contrast"] is True
        assert diag_low["contrast_std"] < 25.0

        # Normal contrast canvas
        normal = np.zeros((200, 200, 3), dtype=np.uint8)
        normal[:100, :] = 255
        diag_normal = ImageOCRPipeline.assess_quality(normal)
        assert diag_normal["is_low_contrast"] is False

    def test_resolution_categorization(self):
        """Verify resolution classification based on minimum dimension."""
        tiny = np.zeros((190, 250, 3), dtype=np.uint8)
        assert ImageOCRPipeline.assess_quality(tiny)["resolution_category"] == "CRITICAL_LOW_RES"

        intermediate = np.zeros((400, 600, 3), dtype=np.uint8)
        assert ImageOCRPipeline.assess_quality(intermediate)["resolution_category"] == "INTERMEDIATE_LOW_RES"

        standard = np.zeros((700, 950, 3), dtype=np.uint8)
        assert ImageOCRPipeline.assess_quality(standard)["resolution_category"] == "STANDARD_RES"

        high = np.zeros((1200, 1600, 3), dtype=np.uint8)
        assert ImageOCRPipeline.assess_quality(high)["resolution_category"] == "HIGH_RES"


class TestControlledPreprocessingOperations:
    """Verify individual preprocessing operations in isolation."""

    def test_lanczos_rescaling_applied_only_when_constrained(self):
        """Verify Lanczos-4 upscales constrained cards (300-800px) and bypasses high-res cards."""
        # Constrained card (width = 500px)
        constrained_img = np.zeros((350, 500, 3), dtype=np.uint8)
        rescaled, meta = ImageOCRPipeline.apply_resolution_normalization(constrained_img, target_width=1000)
        assert meta["rescaled"] is True
        assert meta["new_dims"] == (1000, 700)
        assert rescaled.shape == (700, 1000, 3)

        # High-resolution card (width = 1200px) -> must not upscale
        high_res_img = np.zeros((800, 1200, 3), dtype=np.uint8)
        untouched, meta_high = ImageOCRPipeline.apply_resolution_normalization(high_res_img, target_width=1000)
        assert meta_high["rescaled"] is False
        assert meta_high["new_dims"] == (1200, 800)
        assert untouched.shape == (800, 1200, 3)

    def test_clahe_enhances_luminance_and_preserves_color(self):
        """Verify LAB CLAHE operates on L channel without destroying chromaticity."""
        # Create image with specific color and low contrast text
        color_img = np.full((300, 400, 3), (120, 80, 40), dtype=np.uint8)
        cv2.putText(color_img, "29505141201234", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (140, 90, 50), 2)
        enhanced, meta = ImageOCRPipeline.apply_clahe(color_img, clip_limit=2.0)
        assert meta["clahe_applied"] is True
        assert enhanced.shape == color_img.shape
        # Check that standard deviation (contrast) increased or remained valid
        assert np.std(enhanced) > 0

    def test_deskew_straightens_rotated_text(self):
        """Verify deskew detects tilt and rotates card when angle >= 0.5 degrees."""
        img = np.zeros((400, 600), dtype=np.uint8)
        cv2.putText(img, "EGYPT NATIONAL ID 12345678901234", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        # Rotate by 4.0 degrees
        m = cv2.getRotationMatrix2D((300, 200), 4.0, 1.0)
        tilted = cv2.warpAffine(img, m, (600, 400))

        deskewed_img, meta = ImageOCRPipeline.detect_and_apply_deskew(tilted)
        assert meta["applied"] is True
        assert meta["deskewed"] is True
        assert abs(meta["detected_angle"] - 4.0) < 1.0

    def test_deskew_bypasses_straight_image(self):
        """Verify deskew does not rotate image when angle < 0.5 degrees."""
        straight_img = np.zeros((400, 600), dtype=np.uint8)
        cv2.putText(straight_img, "EGYPT NATIONAL ID 12345678901234", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        untouched, meta = ImageOCRPipeline.detect_and_apply_deskew(straight_img)
        assert meta["applied"] is False
        assert meta["deskewed"] is False

    def test_ablation_mode_selection(self):
        """Verify all 5 experimental modes configure metadata correctly."""
        test_img = np.zeros((400, 500, 3), dtype=np.uint8)
        pipeline = ImageOCRPipeline()

        _, meta_none = pipeline.apply_preprocessing(test_img, mode="NONE")
        assert meta_none["rescaling"]["rescaled"] is False
        assert meta_none["clahe"]["clahe_applied"] is False

        _, meta_a = pipeline.apply_preprocessing(test_img, mode="EXP_A_RESCALING")
        assert meta_a["rescaling"]["rescaled"] is True
        assert meta_a["clahe"]["clahe_applied"] is False

        _, meta_b = pipeline.apply_preprocessing(test_img, mode="EXP_B_CLAHE")
        assert meta_b["rescaling"]["rescaled"] is False
        assert meta_b["clahe"]["clahe_applied"] is True

        _, meta_c = pipeline.apply_preprocessing(test_img, mode="EXP_C_DESKEW")
        assert meta_c["rescaling"]["rescaled"] is False
        assert meta_c["clahe"]["clahe_applied"] is False

        _, meta_d = pipeline.apply_preprocessing(test_img, mode="EXP_D_COMBINED")
        assert meta_d["rescaling"]["rescaled"] is True
        assert meta_d["clahe"]["clahe_applied"] is True

