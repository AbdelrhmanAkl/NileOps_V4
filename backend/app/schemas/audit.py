"""Audit Log Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details_json: str
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

