"""Internal Allowlisted Operations Assistant Agent Endpoints.

Employee-only advisory copilot endpoints with rate limiting, server-side RBAC,
deterministic tool execution, prompt-injection defense, and audit logging.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_employee, require_roles
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User
from app.services.ops_agent import (
    ALLOWLISTED_TOOLS,
    FORBIDDEN_TOOLS,
    ops_agent_service,
)

router = APIRouter(prefix="/agent", tags=["Internal Ops Agent"])

ALLOWED_EMPLOYEE_ROLES = [
    "admin",
    "operations_officer",
    "customer_service",
    "compliance_reviewer",
    "branch_manager",
    "ops_analyst",
]


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Employee question or prompt")
    context_reference: Optional[str] = Field(None, max_length=100, description="Optional ticket or request reference")
    language: str = Field("ar", pattern="^(ar|en)$", description="Language preference (ar or en)")


class AgentToolCallRequest(BaseModel):
    tool: str = Field(..., description="Tool name to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class AgentChatResponse(BaseModel):
    reply: str
    tool_trace: List[Dict[str, Any]]
    draft: Optional[Dict[str, Any]] = None
    review_flag: Optional[Dict[str, Any]] = None
    fallback_used: bool
    injection_detected: bool


class AgentToolsInfoResponse(BaseModel):
    allowlisted_tools: Dict[str, str]
    forbidden_tools: Dict[str, str]


@router.get("/tools", response_model=AgentToolsInfoResponse)
async def get_agent_tools(
    current_user: User = Depends(require_employee),
    role_user: User = Depends(require_roles(ALLOWED_EMPLOYEE_ROLES)),
):
    """Retrieve operational dictionary of allowlisted and explicitly forbidden tools."""
    return {
        "allowlisted_tools": ALLOWLISTED_TOOLS,
        "forbidden_tools": FORBIDDEN_TOOLS,
    }


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    payload: AgentChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employee),
    role_user: User = Depends(require_roles(ALLOWED_EMPLOYEE_ROLES)),
):
    """Staff-facing chat endpoint with prompt-injection defense and tool routing."""
    # 1. Rate limiting check
    await limiter.check_rate_limit(
        request=request,
        endpoint_tag="agent_chat",
        max_requests=settings.RATE_LIMIT_AGENT_MAX,
        window_seconds=settings.RATE_LIMIT_AGENT_WINDOW_SECONDS,
    )

    client_ip = request.client.host if request.client else "127.0.0.1"

    # 2. Process via OpsAssistantAgent service
    result = await ops_agent_service.process_chat(
        message=payload.message,
        actor=current_user,
        db=db,
        context_reference=payload.context_reference,
        language=payload.language,
        ip_address=client_ip,
    )

    return result


@router.post("/tool", response_model=Dict[str, Any])
async def execute_direct_tool(
    payload: AgentToolCallRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employee),
    role_user: User = Depends(require_roles(ALLOWED_EMPLOYEE_ROLES)),
):
    """Direct invocation of allowlisted tools (Denies unallowlisted or forbidden tools)."""
    await limiter.check_rate_limit(
        request=request,
        endpoint_tag="agent_tool",
        max_requests=settings.RATE_LIMIT_AGENT_MAX,
        window_seconds=settings.RATE_LIMIT_AGENT_WINDOW_SECONDS,
    )

    client_ip = request.client.host if request.client else "127.0.0.1"

    result = await ops_agent_service.execute_tool(
        tool_name=payload.tool,
        parameters=payload.parameters,
        actor=current_user,
        db=db,
        ip_address=client_ip,
    )

    return result
