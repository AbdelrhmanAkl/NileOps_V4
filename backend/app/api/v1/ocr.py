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

