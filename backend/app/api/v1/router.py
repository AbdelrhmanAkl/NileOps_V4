"""NileOps API v1 Master Router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.customer import router as customer_router
from app.api.v1.employee import router as employee_router
from app.api.v1.policy import router as policy_router
from app.api.v1.public import router as public_router
from app.api.v1.rag import router as rag_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.kpi import router as kpi_router

api_v1_router = APIRouter()

# Mount feature domain routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(customer_router)
api_v1_router.include_router(employee_router)
api_v1_router.include_router(policy_router)
api_v1_router.include_router(public_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(ocr_router)
api_v1_router.include_router(kpi_router)


@api_v1_router.get("/status", tags=["Status"])
async def v1_status():
    """Version 1 API status check."""
    return {
        "api_version": "v1",
        "status": "active",
        "phase": "PostgreSQL & Qdrant & Production RAG",
        "database": "PostgreSQL 16.15 (Scram-SHA-256)",
        "vector_store": "Qdrant 1.12.5 (Windows Native)",
        "simulation": "NileOps Demo Bank",
    }
