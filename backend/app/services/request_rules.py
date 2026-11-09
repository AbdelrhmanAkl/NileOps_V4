"""Deterministic Evaluation Rules & State Machine for Banking Requests.

Strictly rule-based (NO LLM involved in decisions).
Provides automated compliance verification for simulated account opening & card requests.
"""

from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kyc import KycVerification
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.schemas.requests import RequestRuleEvaluationResult, RuleDetail

# Product Minimum Balances (Aligned with app.api.v1.public.PRODUCTS_DATA)
PRODUCT_MIN_BALANCES: Dict[str, float] = {
    "prod-01": 2500.0,   # Classic Current Account
    "prod-02": 10000.0,  # High-Yield Monthly Savings Account
    "prod-03": 1000.0,   # Nile Platinum 3-Year Certificate
}

# Strict State Machine Transition Map (Clean lifecycle starting at SUBMITTED)
ALLOWED_REQUEST_TRANSITIONS: Dict[str, List[str]] = {
    "SUBMITTED": ["UNDER_REVIEW", "APPROVED_SIMULATED", "REJECTED", "MORE_INFO_REQUIRED"],
    "UNDER_REVIEW": ["APPROVED_SIMULATED", "REJECTED", "MORE_INFO_REQUIRED"],
    "MORE_INFO_REQUIRED": ["SUBMITTED", "UNDER_REVIEW", "REJECTED"],
    "APPROVED_SIMULATED": ["SIMULATED_COMPLETED"],
    "SIMULATED_COMPLETED": [],  # Terminal state
    "REJECTED": [],             # Terminal state
}


def validate_transition(current_status: str, target_status: str) -> bool:
    """Check whether status transition is permitted by the state machine."""
    allowed = ALLOWED_REQUEST_TRANSITIONS.get(current_status, [])
    return target_status in allowed


async def evaluate_account_opening_rules(
    request: AccountOpeningRequest,
    customer: User,
    db: AsyncSession,
) -> RequestRuleEvaluationResult:
    """Evaluate deterministic banking business rules for account opening.

    Rule 1: KYC Verification Status (Mandatory dual-control Document AI check)
    Rule 2: Minimum Initial Deposit (Product threshold)
    Rule 3: Minimum Declared Monthly Income (Retail threshold: 3,000 EGP)
    Rule 4: Customer Contact Completeness (Verified mobile phone)
    """
    rules: List[RuleDetail] = []

    # 1. Rule: Approved KYC Verification Check
    kyc_stmt = (
        select(KycVerification)
        .where(KycVerification.customer_id == customer.id)
        .order_by(KycVerification.created_at.desc())
    )
    kyc_result = await db.execute(kyc_stmt)
    latest_kyc = kyc_result.scalars().first()

    kyc_approved = bool(
        latest_kyc
        and latest_kyc.status in ["APPROVED_SIMULATED", "VERIFIED_SYNTHETIC"]
    )
    if kyc_approved:
        rules.append(
            RuleDetail(
                code="RULE_KYC_VERIFICATION",
                name="KYC National ID Verification",
                passed=True,
                message=f"Verified synthetic KYC case #{latest_kyc.tracking_number} on file.",
            )
        )
    else:
        status_note = latest_kyc.status if latest_kyc else "NO_RECORD"
        rules.append(
            RuleDetail(
                code="RULE_KYC_VERIFICATION",
                name="KYC National ID Verification",
                passed=False,
                message=(
                    f"Customer lacks an approved KYC verification record (Current status: {status_note}). "
                    "Approved synthetic Document AI verification is mandatory prior to account opening."
                ),
            )
        )

    # 2. Rule: Minimum Initial Deposit Threshold
    required_min = PRODUCT_MIN_BALANCES.get(request.product_id, 1000.0)
    min_balance_passed = request.initial_deposit >= required_min
    if min_balance_passed:
        rules.append(
            RuleDetail(
                code="RULE_MIN_BALANCE",
                name="Minimum Initial Deposit",
                passed=True,
                message=f"Initial deposit ({request.initial_deposit:,.2f} EGP) meets or exceeds requirement ({required_min:,.2f} EGP).",
            )
        )
    else:
        rules.append(
            RuleDetail(
                code="RULE_MIN_BALANCE",
                name="Minimum Initial Deposit",
                passed=False,
                message=f"Initial deposit ({request.initial_deposit:,.2f} EGP) is below minimum opening balance ({required_min:,.2f} EGP) for product '{request.product_id}'.",
            )
        )

    # 3. Rule: Minimum Declared Monthly Income
    income_threshold = 3000.0
    income_passed = request.monthly_income >= income_threshold
    if income_passed:
        rules.append(
            RuleDetail(
                code="RULE_MONTHLY_INCOME",
                name="Income Verification Threshold",
                passed=True,
                message=f"Declared income ({request.monthly_income:,.2f} EGP) satisfies standard retail threshold (3,000.00 EGP).",
            )
        )
    else:
        rules.append(
            RuleDetail(
                code="RULE_MONTHLY_INCOME",
                name="Income Verification Threshold",
                passed=False,
                message=f"Declared income ({request.monthly_income:,.2f} EGP) is below retail onboarding guideline (3,000.00 EGP). Additional income verification required.",
            )
        )

    # 4. Rule: Customer Profile Completeness
    phone_passed = bool(customer.phone_number and len(customer.phone_number.strip()) >= 8)
    if phone_passed:
        rules.append(
            RuleDetail(
                code="RULE_CUSTOMER_CONTACT",
                name="Contact Profile Completeness",
                passed=True,
                message="Customer profile contains valid contact phone number.",
            )
        )
    else:
        rules.append(
            RuleDetail(
                code="RULE_CUSTOMER_CONTACT",
                name="Contact Profile Completeness",
                passed=False,
                message="Customer profile lacks registered contact telephone number.",
            )
        )

    # Synthesize outcome
    all_passed = all(r.passed for r in rules)
    if all_passed:
        recommendation = "APPROVE_SIMULATED"
    elif not kyc_approved or not min_balance_passed:
        recommendation = "MORE_INFO_REQUIRED"
    else:
        recommendation = "MORE_INFO_REQUIRED"

    return RequestRuleEvaluationResult(
        eligible=all_passed,
        recommendation=recommendation,
        rules=rules,
    )

