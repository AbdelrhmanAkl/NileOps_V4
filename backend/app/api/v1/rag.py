"""NileOps RAG & Knowledge Base Retrieval Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, get_optional_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User
from app.services.rag import rag_service
from app.services.vector_store import qdrant_service

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Base"])


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Customer or employee inquiry")
    portal_type: str = Field(default="customer", pattern="^(customer|employee)$")
    language: str = Field(default="ar", pattern="^(ar|en)$")
    threshold: Optional[float] = Field(default=0.15, ge=0.0, le=1.0)


class CitationItem(BaseModel):
    code: str
    title: str
    domain: str
    version: str
    portal_access: str
    score: float
    passage: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    portal_type: str
    language: str
    answer: str
    confidence_score: float
    abstained: bool
    fallback_used: bool = False
    citations: List[CitationItem]


@router.post("/ask", response_model=RAGQueryResponse)
async def ask_banking_assistant(
    payload: RAGQueryRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Ask the NileOps RAG banking assistant with strict portal isolation, RBAC, and citations."""
    # Rate limit RAG queries
    await limiter.check_rate_limit(
        request,
        endpoint_tag="rag_ask",
        max_requests=settings.RATE_LIMIT_RAG_MAX,
        window_seconds=settings.RATE_LIMIT_RAG_WINDOW_SECONDS,
    )

    # RBAC: Access to internal employee policies strictly requires employee authentication
    if payload.portal_type == "employee":
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication required: Employee session needed to access internal staff policies.",
            )
        if current_user.user_type != "employee":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Customers are strictly forbidden from querying employee policies.",
            )

    response = await rag_service.retrieve_and_generate(
        query=payload.query,
        portal_type=payload.portal_type,
        language=payload.language,
        threshold=payload.threshold or 0.15,
    )
    return response


@router.get("/health")
async def rag_health():
    """Check Qdrant vector database health and point count."""
    health = qdrant_service.check_health()
    return {
        "status": health.get("status", "unknown"),
        "qdrant": health,
    }


@router.post("/reconcile")
async def reconcile_knowledge_base(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Reconcile Qdrant vector index with PostgreSQL policy records (Employees only)."""
    if current_user.user_type != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can trigger vector index reconciliation.",
        )
    result = await qdrant_service.reconcile_with_postgres(db)
    return {
        "message": "Knowledge base reconciliation complete",
        "result": result,
    }
