"""NileOps Internal Allowlisted Operations Assistant Agent.

Advisory-only internal agent with deterministic tool router, strict deny-by-default allowlist,
prompt-injection interception, output redaction guardrails, and immutable audit logging.
"""

import base64
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import log_audit_event
from app.core.config import settings
from app.models.audit import AuditLog
from app.models.banking import Account
from app.models.complaint import Complaint
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User
from app.services.rag import RAGService

# ---------------------------------------------------------------------------
# Allowlist & Forbidden Tool Definitions
# ---------------------------------------------------------------------------

ALLOWLISTED_TOOLS = {
    "read_request_status": "Lookup account opening or card request status by reference (returns names, never internal IDs)",
    "read_complaint": "Lookup complaint details by ticket number (excludes other customer data)",
    "search_policy": "Search bank compliance & operational policies (respects POL-TEST guard)",
    "create_reply_draft": "Draft advisory response for a customer complaint (marked AI suggestion - requires human review)",
    "suggest_queue_route": "Suggest operational team queue based on complaint or issue description (suggestion only, no state change)",
    "request_human_review": "Escalate case for human review with specific operational or security reason",
}

FORBIDDEN_TOOLS = {
    "execute_sql": "Arbitrary SQL query execution",
    "transfer_funds": "Financial balance movement or payment execution",
    "approve_request": "Direct approval of account or card requests",
    "reject_request": "Direct rejection of account or card requests",
    "change_user_role": "Modification of user or employee security roles",
    "export_database": "Raw database dumping or export",
    "delete_complaint": "Deletion of customer complaints",
    "modify_balance": "Direct adjustment of ledger balances",
    "grant_permission": "Granting administrative or operational privileges",
    "bypass_kyc": "Bypassing KYC or identity verification requirements",
    "execute_command": "Executing operating system or shell commands",
}

# ---------------------------------------------------------------------------
# Prompt Injection Patterns (Bilingual: Arabic + English)
# ---------------------------------------------------------------------------

INJECTION_PATTERNS = [
    # English override patterns
    r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+(instructions|rules|prompts|directions)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|system)\s+(instructions|rules)\b",
    r"(?i)\bforget\s+(all\s+)?(previous|prior|system)\s+(instructions|rules)\b",
    r"(?i)\boverride\s+(system|safety|security)\s+(rules|prompts|guidelines)\b",
    # System prompt leakage
    r"(?i)\b(reveal|show|print|tell\s+me|display)\s+(the\s+)?(hidden\s+)?(system\s+prompt|developer\s+instructions|initial\s+prompt)\b",
    r"(?i)\bwhat\s+(is|are)\s+(your\s+)?(initial\s+|system\s+)?(prompt|instructions)\b",
    # Jailbreaks / Personas
    r"(?i)\byou\s+are\s+now\s+(dan|jailbreak|unrestricted|godmode|in\s+developer\s+mode)\b",
    r"(?i)\bdo\s+anything\s+now\b",
    # Arabic override patterns
    r"تجاهل\s+(كل\s+)?(التعليمات|القواعد|الأوامر|التوجيهات)\s+السابقة",
    r"انس[ىي]\s+(كل\s+)?(التعليمات|القواعد|الأوامر)",
    r"تخط[ىي]\s+(قواعد|إجراءات|ضوابط)\s+الأمان",
    r"(اكشف|أظهر|اعرض|ما\s+هو|ما\s+هي)\s+(عن\s+)?(برومبت|تعليمات|أوامر)\s+(النظام|المطور|الأصلية)",
    r"أنت\s+الآن\s+(في\s+وضع\s+المطور|بدون\s+قيود|دان)",
    # SQL injection syntax attempts in text
    r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into|\bselect\s+\*\s+from\b|--|;\s*drop)",
    # Forbidden actions attempted via natural language
    r"(?i)\b(transfer\s+funds|approve\s+this\s+request\s+directly|grant\s+me\s+admin|change\s+my\s+role)\b",
    r"(حول\s+الأموال|وافق\s+على\s+الطلب\s+مباشرة|امنحني\s+صلاحية\s+مسؤول|غير\s+صلاحيتي)",
]

COMPILED_INJECTIONS = [re.compile(p) for p in INJECTION_PATTERNS]

# ---------------------------------------------------------------------------
# Output Guardrail Patterns (PII, Secrets, Tokens)
# ---------------------------------------------------------------------------

RE_NATIONAL_ID = re.compile(r"\b([23]\d{3})(\d{6})(\d{4})\b")
RE_IBAN = re.compile(r"\bEG\d{2}[A-Z0-9]{25}\b|\bEG\d{26,27}\b")
RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
RE_SECRET_VAR = re.compile(r"(?i)(SECRET_KEY|API_KEY|PASSWORD)\s*=\s*['\"]?[^\s'\"]+['\"]?")


def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Scan input string and potential base64 strings for prompt injection attempts."""
    if not text:
        return False, None

    # 1. Direct regex scan on raw input
    for pattern in COMPILED_INJECTIONS:
        if pattern.search(text):
            return True, f"Pattern matched: {pattern.pattern}"

    # 2. Check for base64 obfuscated payloads (detect valid base64 substrings >= 16 chars)
    b64_candidates = re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text)
    for cand in b64_candidates:
        try:
            decoded = base64.b64decode(cand).decode("utf-8", errors="ignore")
            for pattern in COMPILED_INJECTIONS:
                if pattern.search(decoded):
                    return True, f"Base64 obfuscated injection detected: {pattern.pattern}"
        except Exception:
            continue

    return False, None


def apply_output_guardrails(text: str) -> str:
    """Mask National IDs, IBANs, JWT tokens, and secrets from any agent output."""
    if not text:
        return ""

    # Mask 14-digit National IDs: e.g. 29501011234567 -> 2950****4567
    def mask_id(match: re.Match) -> str:
        prefix = match.group(1)
        suffix = match.group(3)
        return f"{prefix}****{suffix}"

    redacted = RE_NATIONAL_ID.sub(mask_id, text)

    # Mask IBAN: e.g. EG380002000100000012345678901 -> EG********************8901
    def mask_iban(match: re.Match) -> str:
        full = match.group(0)
        return f"EG{'*' * (len(full) - 6)}{full[-4:]}"

    redacted = RE_IBAN.sub(mask_iban, redacted)

    # Redact JWT tokens
    redacted = RE_JWT.sub("[REDACTED_JWT_TOKEN]", redacted)

    # Redact secrets
    redacted = RE_SECRET_VAR.sub(r"\1=[REDACTED_SECRET]", redacted)

    return redacted


# ---------------------------------------------------------------------------
# OpsAssistantAgent Service Class
# ---------------------------------------------------------------------------

class OpsAssistantAgent:
    """Internal Ops Assistant Agent adhering strictly to Phase 8 C requirements."""

    def __init__(self, ollama_url: str = settings.OLLAMA_URL, model: str = settings.OLLAMA_MODEL):
        self.ollama_url = ollama_url
        self.model = model
        self.rag_service = RAGService(ollama_url=ollama_url, model=model)

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        actor: User,
        db: AsyncSession,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Execute a tool with deny-by-default allowlist, parameter masking, and audit logging."""
        tool_name_clean = tool_name.strip().lower()

        # Check for forbidden or non-allowlisted tool
        if tool_name_clean in FORBIDDEN_TOOLS or tool_name_clean not in ALLOWLISTED_TOOLS:
            # Audit log DENIED event immediately
            await log_audit_event(
                db=db,
                action="AGENT_TOOL_CALL",
                resource_type="OPS_AGENT",
                resource_id=tool_name_clean,
                user=actor,
                details={
                    "tool": tool_name_clean,
                    "status": "DENIED",
                    "reason": "Tool is forbidden or not allowlisted",
                    "actor_role": actor.role,
                    "actor_email": actor.email,
                },
                ip_address=ip_address,
            )
            return {
                "status": "DENIED",
                "tool": tool_name_clean,
                "error": f"Tool '{tool_name_clean}' is not permitted. Only allowlisted advisory tools are supported.",
                "allowed": False,
            }

        # Mask sensitive arguments for audit logging
        masked_params = {}
        for k, v in parameters.items():
            if isinstance(v, str):
                masked_params[k] = apply_output_guardrails(v)
            else:
                masked_params[k] = v

        try:
            # Execute specific allowlisted tool
            if tool_name_clean == "read_request_status":
                result = await self._tool_read_request_status(parameters.get("reference_number", ""), db)
            elif tool_name_clean == "read_complaint":
                result = await self._tool_read_complaint(parameters.get("ticket_number", ""), db)
            elif tool_name_clean == "search_policy":
                result = await self._tool_search_policy(
                    query=parameters.get("query", ""),
                    language=parameters.get("language", "ar"),
                )
            elif tool_name_clean == "create_reply_draft":
                result = await self._tool_create_reply_draft(
                    ticket_number=parameters.get("ticket_number", ""),
                    draft_text=parameters.get("draft_text", ""),
                    db=db,
                    actor=actor,
                )
            elif tool_name_clean == "suggest_queue_route":
                result = await self._tool_suggest_queue_route(
                    category=parameters.get("category", ""),
                    text=parameters.get("text", "") or parameters.get("description", ""),
                )
            elif tool_name_clean == "request_human_review":
                result = await self._tool_request_human_review(
                    case_reference=parameters.get("case_reference", ""),
                    reason=parameters.get("reason", ""),
                    db=db,
                    actor=actor,
                    ip_address=ip_address,
                )
            else:
                result = {"status": "ERROR", "message": "Unknown allowlisted tool"}

            # Log ALLOWED audit event
            await log_audit_event(
                db=db,
                action="AGENT_TOOL_CALL",
                resource_type="OPS_AGENT",
                resource_id=tool_name_clean,
                user=actor,
                details={
                    "tool": tool_name_clean,
                    "status": "ALLOWED",
                    "masked_args": masked_params,
                    "result_status": result.get("status", "SUCCESS"),
                },
                ip_address=ip_address,
            )

            return {
                "status": "ALLOWED",
                "tool": tool_name_clean,
                "result": result,
                "allowed": True,
            }

        except Exception as exc:
            await log_audit_event(
                db=db,
                action="AGENT_TOOL_CALL",
                resource_type="OPS_AGENT",
                resource_id=tool_name_clean,
                user=actor,
                details={
                    "tool": tool_name_clean,
                    "status": "ERROR",
                    "error": str(exc),
                },
                ip_address=ip_address,
            )
            return {
                "status": "ERROR",
                "tool": tool_name_clean,
                "error": str(exc),
                "allowed": True,
            }

    # -----------------------------------------------------------------------
    # Tool Implementations
    # -----------------------------------------------------------------------

    async def _tool_read_request_status(self, reference_number: str, db: AsyncSession) -> Dict[str, Any]:
        """Lookup account or card request by reference. Never returns internal DB IDs."""
        ref = reference_number.strip()
        if not ref:
            return {"status": "NOT_FOUND", "message": "Reference number is required."}

        # Check account opening requests
        stmt_acc = (
            select(AccountOpeningRequest, User.full_name)
            .join(User, AccountOpeningRequest.customer_id == User.id)
            .where(AccountOpeningRequest.reference_number == ref)
        )
        res_acc = await db.execute(stmt_acc)
        row_acc = res_acc.first()

        if row_acc:
            req, customer_name = row_acc
            return {
                "status": "FOUND",
                "request_type": "ACCOUNT_OPENING",
                "reference_number": req.reference_number,
                "customer_name": customer_name,
                "product_type": req.account_type,
                "currency": req.currency,
                "request_status": req.status,
                "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
                "reviewer_notes": req.reviewer_notes or "None",
            }

        # Check card requests
        stmt_crd = (
            select(CardRequest, User.full_name)
            .join(User, CardRequest.customer_id == User.id)
            .where(CardRequest.reference_number == ref)
        )
        res_crd = await db.execute(stmt_crd)
        row_crd = res_crd.first()

        if row_crd:
            req, customer_name = row_crd
            return {
                "status": "FOUND",
                "request_type": "CARD_ISSUANCE",
                "reference_number": req.reference_number,
                "customer_name": customer_name,
                "product_type": req.card_type,
                "delivery_branch": req.delivery_branch,
                "request_status": req.status,
                "submitted_at": req.created_at.isoformat() if req.created_at else None,
                "reviewer_notes": req.reviewer_notes or "None",
            }

        return {"status": "NOT_FOUND", "message": f"No request found matching reference '{ref}'."}

    async def _tool_read_complaint(self, ticket_number: str, db: AsyncSession) -> Dict[str, Any]:
        """Lookup complaint by ticket number. Excludes other customer data and internal IDs."""
        t_num = ticket_number.strip()
        if not t_num:
            return {"status": "NOT_FOUND", "message": "Ticket number is required."}

        stmt = (
            select(Complaint, User.full_name)
            .join(User, Complaint.customer_id == User.id)
            .where(Complaint.ticket_number == t_num)
        )
        res = await db.execute(stmt)
        row = res.first()

        if not row:
            return {"status": "NOT_FOUND", "message": f"No complaint found matching ticket '{t_num}'."}

        complaint, customer_name = row
        return {
            "status": "FOUND",
            "ticket_number": complaint.ticket_number,
            "customer_name": customer_name,
            "category": complaint.category,
            "category_ar": complaint.category_ar,
            "subject": complaint.subject,
            "details": complaint.details,
            "complaint_status": complaint.status,
            "priority": complaint.priority,
            "assigned_team": complaint.assigned_team or "UNASSIGNED",
            "sla_breached": bool(complaint.sla_breached),
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "existing_draft": complaint.ai_draft_reply or None,
            "draft_status": complaint.ai_draft_status or None,
        }

    async def _tool_search_policy(self, query: str, language: str = "ar") -> Dict[str, Any]:
        """Search policy knowledge base under employee portal scope (respects POL-TEST guard)."""
        rag_res = await self.rag_service.retrieve_and_generate(
            query=query,
            portal_type="employee",
            language=language,
        )
        return {
            "status": "SUCCESS",
            "query": query,
            "language": language,
            "answer": rag_res.get("answer", ""),
            "citations": rag_res.get("citations", []),
            "abstained": rag_res.get("abstained", False),
            "confidence_score": rag_res.get("confidence_score", 0.0),
        }

    async def _tool_create_reply_draft(
        self,
        ticket_number: str,
        draft_text: str,
        db: AsyncSession,
        actor: User,
    ) -> Dict[str, Any]:
        """Save advisory reply draft for complaint. Marked with mandatory human review disclaimer."""
        t_num = ticket_number.strip()
        cleaned_draft = draft_text.strip()

        stmt = select(Complaint).where(Complaint.ticket_number == t_num)
        res = await db.execute(stmt)
        complaint = res.scalar_one_or_none()

        if not complaint:
            return {"status": "NOT_FOUND", "message": f"Complaint '{t_num}' not found for drafting."}

        # Store draft strictly with PENDING_REVIEW / DRAFT status
        complaint.ai_draft_reply = cleaned_draft
        complaint.ai_draft_status = "DRAFT"
        await db.commit()

        return {
            "status": "DRAFT_SAVED",
            "ticket_number": t_num,
            "draft_text": cleaned_draft,
            "disclaimer": "AI suggestion - requires human review",
            "disclaimer_ar": "اقتراح استشاري من الذكاء الاصطناعي - يتطلب مراجعة بشرية معتمدة",
            "requires_human_approval": True,
        }

    async def _tool_suggest_queue_route(
        self,
        category: str = "",
        text: str = "",
    ) -> Dict[str, Any]:
        """Deterministic queue routing suggestion. No state modification."""
        combined = f"{category} {text}".lower()

        if any(w in combined for w in ["احتيال", "سرقة", "مسروقة", "اختراق", "غير مصرح", "fraud", "stolen", "hack", "unauthorized"]):
            return {
                "status": "SUGGESTION",
                "suggested_team": "fraud_operations",
                "suggested_priority": "URGENT",
                "rationale": "Security and fraud indicators detected. High urgency triage recommended.",
            }
        elif any(w in combined for w in ["atm", "صراف", "ماكينة", "كارت", "بطاقة", "card", "atm_card", "سحب"]):
            return {
                "status": "SUGGESTION",
                "suggested_team": "card_disputes",
                "suggested_priority": "HIGH",
                "rationale": "Card or ATM dispute detected. Routed to Card Operations & Disputes team.",
            }
        elif any(w in combined for w in ["تحويل", "transfer", "سويفت", "swift", "حوالة", "instapay", "انستاباي"]):
            return {
                "status": "SUGGESTION",
                "suggested_team": "payment_operations",
                "suggested_priority": "HIGH",
                "rationale": "Funds transfer inquiry/dispute routed to Payment Operations.",
            }
        elif any(w in combined for w in ["رسوم", "مصاريف", "عمولة", "fees", "account_fees", "خصم"]):
            return {
                "status": "SUGGESTION",
                "suggested_team": "retail_banking",
                "suggested_priority": "MEDIUM",
                "rationale": "Account fee and charging structure dispute routed to Retail Branch Operations.",
            }
        elif any(w in combined for w in ["غسيل", "aml", "امتثال", "compliance", "قائمة سوداء", "sanctions"]):
            return {
                "status": "SUGGESTION",
                "suggested_team": "compliance_aml",
                "suggested_priority": "URGENT",
                "rationale": "Compliance, KYC, or AML regulatory matter routed to Compliance Unit.",
            }
        else:
            return {
                "status": "SUGGESTION",
                "suggested_team": "customer_care",
                "suggested_priority": "MEDIUM",
                "rationale": "General inquiry routed to Primary Customer Care Desk.",
            }

    async def _tool_request_human_review(
        self,
        case_reference: str,
        reason: str,
        db: AsyncSession,
        actor: User,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Flag case for human review with reason and immutable audit log entry."""
        case_ref = case_reference.strip() or "GENERAL_CASE"
        reason_clean = reason.strip() or "Manual review requested by Ops Assistant"

        await log_audit_event(
            db=db,
            action="CASE_ESCALATED_HUMAN_REVIEW",
            resource_type="CASE",
            resource_id=case_ref,
            user=actor,
            details={
                "case_reference": case_ref,
                "reason": reason_clean,
                "escalated_by": actor.email,
                "escalated_at": datetime.now(timezone.utc).isoformat(),
            },
            ip_address=ip_address,
        )

        return {
            "status": "ESCALATED",
            "case_reference": case_ref,
            "reason": reason_clean,
            "escalated_by": actor.full_name,
            "requires_human_intervention": True,
            "message": f"Case '{case_ref}' has been formally escalated for human review. Reason: {reason_clean}",
        }

    # -----------------------------------------------------------------------
    # End-to-End Chat & Orchestration Pipeline
    # -----------------------------------------------------------------------

    async def process_chat(
        self,
        message: str,
        actor: User,
        db: AsyncSession,
        context_reference: Optional[str] = None,
        language: str = "ar",
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Full end-to-end processing of staff inquiry with prompt injection interception."""
        # 1. Delimiter-separated packaging
        wrapped_user_query = f"<user_data>\n{message}\n</user_data>"
        wrapped_context = f"<document_data>\n{context_reference or ''}\n</document_data>"

        # 2. Check for Prompt Injection Attacks in user query & context
        is_injection, matched_pattern = detect_prompt_injection(message)
        if not is_injection and context_reference:
            is_injection, matched_pattern = detect_prompt_injection(context_reference)

        if is_injection:
            # Audit log security incident
            await log_audit_event(
                db=db,
                action="PROMPT_INJECTION_BLOCKED",
                resource_type="SECURITY_GUARDRAIL",
                resource_id=actor.email,
                user=actor,
                details={
                    "actor_role": actor.role,
                    "matched_pattern": matched_pattern,
                    "masked_query": apply_output_guardrails(message[:120]),
                },
                ip_address=ip_address,
            )

            # Escalate automatically to human review
            escalation_result = await self._tool_request_human_review(
                case_reference=context_reference or "SECURITY_INCIDENT",
                reason=f"PROMPT_INJECTION_SUSPECTED: {matched_pattern}",
                db=db,
                actor=actor,
                ip_address=ip_address,
            )

            refusal_text = (
                "تم اعتراض الطلب: تم رصد محاولة حقن تعليمات أو أمر غير مصرح به. "
                "تم تسجيل هذه الواقعة فوراً في سجل التدقيق الأمني وإحالتها للمراجعة البشرية."
                if language == "ar"
                else "Request intercepted: Prompt injection or unauthorized instruction detected. "
                "This incident has been logged in the security audit trail and escalated for human review."
            )

            return {
                "reply": refusal_text,
                "tool_trace": [
                    {
                        "tool": "security_guardrail",
                        "status": "INTERCEPTED",
                        "pattern": matched_pattern,
                    },
                    {
                        "tool": "request_human_review",
                        "status": "ESCALATED",
                        "details": escalation_result,
                    },
                ],
                "draft": None,
                "review_flag": {
                    "flagged": True,
                    "reason": "PROMPT_INJECTION_SUSPECTED",
                    "details": matched_pattern,
                },
                "fallback_used": True,
                "injection_detected": True,
            }

        # 3. Intent Detection & Tool Execution
        tool_traces = []
        draft_result = None
        review_flag = None

        # Check if user query references a ticket number (e.g. CMP-2026-...)
        cmp_match = re.search(r"\b(CMP-[0-9A-Z-]+)\b", message, re.IGNORECASE)
        # Check if user query references an account/card request (e.g. REQ-..., CRD-...)
        req_match = re.search(r"\b((REQ|CRD)-[0-9A-Z-]+)\b", message, re.IGNORECASE)

        target_ref = None
        if cmp_match:
            target_ref = cmp_match.group(1).upper()
            trace = await self.execute_tool("read_complaint", {"ticket_number": target_ref}, actor, db, ip_address)
            tool_traces.append(trace)
        elif req_match:
            target_ref = req_match.group(1).upper()
            trace = await self.execute_tool("read_request_status", {"reference_number": target_ref}, actor, db, ip_address)
            tool_traces.append(trace)
        elif context_reference and context_reference.startswith("CMP-"):
            target_ref = context_reference
            trace = await self.execute_tool("read_complaint", {"ticket_number": target_ref}, actor, db, ip_address)
            tool_traces.append(trace)
        elif context_reference and (context_reference.startswith("REQ-") or context_reference.startswith("CRD-")):
            target_ref = context_reference
            trace = await self.execute_tool("read_request_status", {"reference_number": target_ref}, actor, db, ip_address)
            tool_traces.append(trace)

        # Check if query requests queue suggestion
        if any(w in message.lower() for w in ["توجيه", "مسار", "قسم", "فريق", "route", "queue", "team"]):
            route_trace = await self.execute_tool(
                "suggest_queue_route",
                {"text": message, "category": "GENERAL"},
                actor,
                db,
                ip_address,
            )
            tool_traces.append(route_trace)

        # Check if query requests drafting
        if any(w in message.lower() for w in ["مسودة", "صياغة", "رد", "draft", "reply"]) and target_ref:
            # Deterministic draft synthesis
            draft_text = (
                f"عزيزي العميل، بخصوص طلبكم/شكواكم رقم ({target_ref})، نود إفادتكم بأنه جاري العمل على مراجعة التفاصيل "
                f"مع الفريق المختص وفقاً للإجراءات البنكية المتبعة، وسنوافيكم بالرد النهائي خلال وقت وجيز."
                if language == "ar"
                else f"Dear Customer, regarding your request/ticket ({target_ref}), we are reviewing the details "
                f"with the relevant department according to banking regulations. We will update you shortly."
            )
            draft_trace = await self.execute_tool(
                "create_reply_draft",
                {"ticket_number": target_ref, "draft_text": draft_text},
                actor,
                db,
                ip_address,
            )
            tool_traces.append(draft_trace)
            draft_result = draft_trace.get("result")

        # In all cases, query RAG policy engine for grounding context
        policy_trace = await self.execute_tool(
            "search_policy",
            {"query": message, "language": language},
            actor,
            db,
            ip_address,
        )
        tool_traces.append(policy_trace)

        # 4. Synthesize Advisory Response with 2s LLM Timeout & Fallback
        advisory_reply, fallback_used = await self._synthesize_advisory_reply(
            message=message,
            tool_traces=tool_traces,
            language=language,
        )

        # 5. Apply Output Guardrails (PII & Secrets Scrubbing)
        sanitized_reply = apply_output_guardrails(advisory_reply)

        return {
            "reply": sanitized_reply,
            "tool_trace": tool_traces,
            "draft": draft_result,
            "review_flag": review_flag,
            "fallback_used": fallback_used,
            "injection_detected": False,
        }

    async def _synthesize_advisory_reply(
        self,
        message: str,
        tool_traces: List[Dict[str, Any]],
        language: str,
    ) -> Tuple[str, bool]:
        """Synthesize employee advisory answer. Uses Ollama if available <= 2.0s, else deterministic template."""
        # Check if Ollama is accessible with strict 2.0s timeout
        fallback_used = True
        llm_answer = None

        prompt_context = []
        for t in tool_traces:
            if t.get("status") == "ALLOWED" and "result" in t:
                prompt_context.append(json.dumps(t["result"], ensure_ascii=False))

        context_str = "\n".join(prompt_context)

        system_instruction = (
            "You are NileOps Ops Assistant, an internal advisory copilot for bank operations staff. "
            "You provide factual policy lookups, draft suggestions, and ticket summaries. "
            "You NEVER make final decisions, transfer money, or approve requests. "
            "All recommendations must include a reminder that employee review is required."
        )

        user_prompt = (
            f"<document_data>\n{context_str}\n</document_data>\n"
            f"<user_data>\n{message}\n</user_data>\n"
            f"Provide a helpful advisory response in {'Arabic' if language == 'ar' else 'English'}."
        )

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=0.2, read=2.0, write=1.0, pool=1.0)) as client:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": user_prompt,
                        "system": system_instruction,
                        "stream": False,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    out = data.get("response", "").strip()
                    if out:
                        llm_answer = out
                        fallback_used = False
        except Exception:
            fallback_used = True

        if llm_answer and not fallback_used:
            return llm_answer, False

        # Deterministic Template Fallback
        lines = []
        if language == "ar":
            lines.append("مساعد العمليات الاستشاري (NileOps Ops Assistant):")
            for t in tool_traces:
                tool_name = t.get("tool")
                res = t.get("result", {})
                if tool_name == "read_request_status" and res.get("status") == "FOUND":
                    lines.append(
                        f"\n• حالة الطلب ({res.get('reference_number')}): "
                        f"العميل: {res.get('customer_name')}, النوع: {res.get('product_type')}, "
                        f"الحالة الحالية: {res.get('request_status')}."
                    )
                elif tool_name == "read_complaint" and res.get("status") == "FOUND":
                    lines.append(
                        f"\n• تفاصيل الشكوى ({res.get('ticket_number')}): "
                        f"العميل: {res.get('customer_name')}, الفئة: {res.get('category_ar')}, "
                        f"الحالة: {res.get('complaint_status')}, الأولوية: {res.get('priority')}."
                    )
                elif tool_name == "suggest_queue_route" and res.get("status") == "SUGGESTION":
                    lines.append(
                        f"\n• توجيه مقترح للفريق: {res.get('suggested_team')} "
                        f"(الأولوية: {res.get('suggested_priority')}). السبب: {res.get('rationale')}"
                    )
                elif tool_name == "search_policy" and res.get("answer"):
                    lines.append(f"\n• استرشاد السياسات البنكية:\n{res.get('answer')}")

            lines.append("\n⚠️ تنبيه استشاري: هذه المخرجات استشارية فقط وتتطلب مراجعة واعتماد الموظف المسؤول.")
        else:
            lines.append("NileOps Advisory Ops Assistant:")
            for t in tool_traces:
                tool_name = t.get("tool")
                res = t.get("result", {})
                if tool_name == "read_request_status" and res.get("status") == "FOUND":
                    lines.append(
                        f"\n• Request Status ({res.get('reference_number')}): "
                        f"Customer: {res.get('customer_name')}, Type: {res.get('product_type')}, "
                        f"Current Status: {res.get('request_status')}."
                    )
                elif tool_name == "read_complaint" and res.get("status") == "FOUND":
                    lines.append(
                        f"\n• Complaint Details ({res.get('ticket_number')}): "
                        f"Customer: {res.get('customer_name')}, Category: {res.get('category')}, "
                        f"Status: {res.get('complaint_status')}, Priority: {res.get('priority')}."
                    )
                elif tool_name == "suggest_queue_route" and res.get("status") == "SUGGESTION":
                    lines.append(
                        f"\n• Suggested Queue Route: {res.get('suggested_team')} "
                        f"(Priority: {res.get('suggested_priority')}). Rationale: {res.get('rationale')}"
                    )
                elif tool_name == "search_policy" and res.get("answer"):
                    lines.append(f"\n• Banking Policy Reference:\n{res.get('answer')}")

            lines.append("\n⚠️ Advisory Notice: These recommendations are advisory only and require authorized employee review.")

        return "\n".join(lines), True


# Global Singleton Instance
ops_agent_service = OpsAssistantAgent()
