"""Operational & Risk KPI Endpoints.

Restricted to authorized bank employees (ops_analyst, branch_manager, compliance_officer, admin).
Strictly rejects retail customer sessions (RBAC 403).
"""

from datetime import datetime, timezone
import os
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_employee, require_roles
from app.models.user import User
from app.services.kpi_service import KpiMetric, KpiSummaryResponse, kpi_service

router = APIRouter(prefix="/kpi", tags=["Operational KPIs"])

EMPLOYEE_ROLES = [
    "ops_analyst",
    "operations_officer",
    "branch_manager",
    "compliance_officer",
    "compliance_reviewer",
    "admin",
    "customer_service",
]


@router.get(
    "/summary",
    response_model=KpiSummaryResponse,
    summary="Retrieve all operational and risk KPI metrics",
)
async def get_kpi_summary(
    current_user: User = Depends(require_roles(EMPLOYEE_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full operational KPI scorecard computed directly from persisted entities.

    Requires employee role. Customer access is strictly denied (403).
    """
    metrics = await kpi_service.get_all_kpis(db)
    raw_db = os.getenv("DATABASE_URL", "")
    env_mode = "test" if "_test" in raw_db else "development"

    return KpiSummaryResponse(
        calculated_at=datetime.now(timezone.utc).isoformat(),
        environment_mode=env_mode,
        metrics=metrics,
    )


@router.get(
    "/{key}",
    response_model=KpiMetric,
    summary="Retrieve a specific operational KPI metric by key",
)
async def get_kpi_by_key(
    key: str,
    current_user: User = Depends(require_roles(EMPLOYEE_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single operational KPI metric by key name."""
    metrics = await kpi_service.get_all_kpis(db)
    if key not in metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI metric '{key}' not found. Available keys: {', '.join(metrics.keys())}",
        )
    return metrics[key]
