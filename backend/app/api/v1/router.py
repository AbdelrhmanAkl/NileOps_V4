"""NileOps API v1 Master Router."""

from fastapi import APIRouter

api_v1_router = APIRouter()

# Phase 1: Router placeholder
# Domain routers (auth, users, kyc, kb, conversations, workflows) will be included here in Phases 2-10

@api_v1_router.get("/status", tags=["Status"])
async def v1_status():
    """Version 1 API status check."""
    return {
        "api_version": "v1",
        "status": "active",
        "phase": "Phase 1 - Scaffolding"
    }
