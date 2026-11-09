"""NileOps Complaint SLA (Service Level Agreement) Engine.

Defines deterministic, configurable SLA calculation rules based on complaint priority.
All SLA tracking is explicitly labeled as a Simulated Banking Operations Policy.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
from pydantic import BaseModel

# Configurable SLA Resolution Windows (Hours)
SLA_POLICY_HOURS: Dict[str, float] = {
    "URGENT": 4.0,     # Critical payment failure / ATM card retention: 4 hours
    "HIGH": 12.0,      # Dispute / delay / pending transfer: 12 hours
    "MEDIUM": 24.0,    # General fee / account maintenance: 24 hours (1 business day)
    "LOW": 48.0,       # Inquiries and informational tickets: 48 hours (2 business days)
}

SLA_POLICY_NAME = "NileOps Simulated Retail Banking SLA Policy v1.0"


class SLAEvaluation(BaseModel):
    """Calculated SLA metrics for a complaint ticket."""
    policy_name: str = SLA_POLICY_NAME
    target_hours: float
    due_at: datetime
    is_breached: bool
    remaining_hours: float
    status_label: str  # ON_TRACK, APPROACHING_BREACH, BREACHED, RESOLVED_ON_TIME, RESOLVED_BREACHED


def calculate_sla_due_at(created_at: datetime, priority: str) -> datetime:
    """Calculate SLA due date and time from ticket creation and priority."""
    target_hours = SLA_POLICY_HOURS.get(priority.upper(), 24.0)
    # Ensure timezone aware
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at + timedelta(hours=target_hours)


def evaluate_sla(
    created_at: datetime,
    priority: str,
    status: str,
    due_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
    resolved_at: Optional[datetime] = None,
) -> SLAEvaluation:
    """Evaluate SLA performance against policy."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    target_hours = SLA_POLICY_HOURS.get(priority.upper(), 24.0)
    if due_at is None:
        due_at = created_at + timedelta(hours=target_hours)
    elif due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)

    # If ticket is resolved or rejected
    if status in ("RESOLVED", "REJECTED"):
        effective_resolution = resolved_at or now
        if effective_resolution.tzinfo is None:
            effective_resolution = effective_resolution.replace(tzinfo=timezone.utc)
        
        is_breached = effective_resolution > due_at
        diff_hours = (due_at - effective_resolution).total_seconds() / 3600.0
        return SLAEvaluation(
            policy_name=SLA_POLICY_NAME,
            target_hours=target_hours,
            due_at=due_at,
            is_breached=is_breached,
            remaining_hours=round(diff_hours, 1),
            status_label="RESOLVED_ON_TIME" if not is_breached else "RESOLVED_BREACHED",
        )

    # Active ticket
    diff_seconds = (due_at - now).total_seconds()
    remaining_hours = diff_seconds / 3600.0
    is_breached = diff_seconds < 0

    if is_breached:
        status_label = "BREACHED"
    elif remaining_hours <= (target_hours * 0.25):  # Less than 25% of SLA window remains
        status_label = "APPROACHING_BREACH"
    else:
        status_label = "ON_TRACK"

    return SLAEvaluation(
        policy_name=SLA_POLICY_NAME,
        target_hours=target_hours,
        due_at=due_at,
        is_breached=is_breached,
        remaining_hours=round(remaining_hours, 1),
        status_label=status_label,
    )

