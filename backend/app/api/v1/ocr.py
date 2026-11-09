"""NileOps OCR & National ID Verification Endpoints."""

import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.services.ocr import (
    NationalIDValidationPublicResponse,
    OCRDocumentService,
    WorkflowContext,
    ocr_service,
)

router = APIRouter(prefix="/ocr", tags=["OCR Document Intelligence"])


class ValidateNationalIDRequest(BaseModel):
    raw_national_id: str = Field(..., min_length=14, max_length=30, description="14-digit Egyptian National ID")
    workflow_context: WorkflowContext = Field(default=WorkflowContext.STRUCTURED_INTAKE)
    document_profile: str = Field(default="EGY_NID_FRONT_V1")
    comparison_id: Optional[str] = None


@router.post("/validate-national-id", response_model=NationalIDValidationPublicResponse)
async def validate_national_id(payload: ValidateNationalIDRequest):
    """Validate 14-digit Egyptian National ID under deterministic 9-dimensional rules."""
    case_id = f"case-{uuid.uuid4().hex[:8]}"
    result = ocr_service.process_national_id(
        case_id=case_id,
        raw_id_input=payload.raw_national_id,
        workflow_context=payload.workflow_context,
        document_profile=payload.document_profile,
        comparison_id=payload.comparison_id,
    )
    return result


@router.post("/process-synthetic-card", response_model=NationalIDValidationPublicResponse)
async def process_synthetic_card(
    synthetic_id: str = Form(..., description="Synthetic Egyptian National ID for testing"),
    ocr_confidence: float = Form(default=0.96),
    document_profile: str = Form(default="EGY_NID_FRONT_V1"),
):
    """Simulate OCR extraction on synthetic Egyptian National ID card."""
    case_id = f"case-{uuid.uuid4().hex[:8]}"
    result = ocr_service.process_national_id(
        case_id=case_id,
        raw_id_input=synthetic_id,
        workflow_context=WorkflowContext.DOCUMENT_AI,
        document_profile=document_profile,
        ocr_confidence=ocr_confidence,
    )
    return result


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit
JPEG_MAGIC = b"\xFF\xD8\xFF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
WEBP_RIFF = b"RIFF"
WEBP_MAGIC = b"WEBP"


def is_valid_image_header(content: bytes) -> bool:
    """Validate image magic bytes for JPEG, PNG, or WebP without trusting RIFF alone."""
    if len(content) < 12:
        return False
    if content.startswith(JPEG_MAGIC):
        return True
    if content.startswith(PNG_MAGIC):
        return True
    if content[:4] == WEBP_RIFF and content[8:12] == WEBP_MAGIC:
        return True
    return False


@router.post("/process-image-card")
async def process_image_card(
    file: UploadFile = File(..., description="JPEG/PNG/WebP image of Egyptian National ID front"),
    comparison_id: Optional[str] = Form(None, description="Optional comparison National ID for cross-field consistency check"),
):
    """Process an image file through real computer vision OCR and 9D validation with strict security guards."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum permitted limit of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    if len(content) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is too small to be a valid image.",
        )

    if not is_valid_image_header(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Expected verified JPEG, PNG, or WebP magic bytes.",
        )

    case_id = f"case-{uuid.uuid4().hex[:8]}"
    from app.services.image_pipeline import image_ocr_pipeline
    result = image_ocr_pipeline.process_image(
        image_input=content,
        case_id=case_id,
        comparison_id=comparison_id,
    )

    if result.get("ingestion_status") == "FAIL":
        err_msg = result.get("error", "Image decoding failed.")
        if "dimensions" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    return result


