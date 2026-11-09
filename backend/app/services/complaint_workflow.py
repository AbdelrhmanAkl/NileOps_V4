"""NileOps Complaint Workflow State Machine & Transition Rules.

Enforces valid status transitions, terminal state locks, and team definitions.
Invalid transitions immediately return HTTP 409 Conflict.
"""

from typing import Dict, List
from fastapi import HTTPException, status

ALLOWED_COMPLAINT_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN": ["IN_PROGRESS", "REJECTED"],
    "IN_PROGRESS": ["RESOLVED", "REJECTED", "OPEN"],
    "RESOLVED": [],  # Terminal state
    "REJECTED": [],  # Terminal state
}

VALID_COMPLAINT_TEAMS = [
    "OPERATIONS",
    "CUSTOMER_SERVICE",
    "CARDS_PAYMENTS",
    "COMPLIANCE",
    "BRANCH_NETWORK",
]

VALID_COMPLAINT_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]

VALID_COMPLAINT_CATEGORIES = [
    "ATM_CARD",
    "TRANSFER",
    "ACCOUNT_FEES",
    "MOBILE_BANKING",
    "GENERAL_INQUIRY",
]


def validate_complaint_transition(current_status: str, target_status: str) -> None:
    """Validate that complaint transition is permitted by the state machine.
    
    Raises:
        HTTPException(status_code=409) if the transition is disallowed.
    """
    if current_status == target_status:
        return

    allowed = ALLOWED_COMPLAINT_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid complaint status transition: '{current_status}' -> '{target_status}'. "
                f"Allowed transitions from '{current_status}' are: {allowed or 'None (Terminal state)'}."
            ),
        )

