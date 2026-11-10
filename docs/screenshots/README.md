# NileOps V4 — Screenshot Gallery & Visual Verification Registry

This directory contains visual inspection screenshots captured directly from the live NileOps banking application at `1920×1080` resolution using headless Chromium CDP automation on Windows.

---

## 1. Directory Structure & Inventory

The screenshot assets are organized into two tiers: active root screenshots (canonical E2E + per-phase evidence) and archived legacy captures.

```
docs/screenshots/
├── README.md                                    # This document
├── SCREENSHOT_INDEX.md                          # Tabular registry with status, viewports, and descriptions
├── 01_login_screen_en.png ... 14_...            # 14 Canonical Browser E2E captures (Root)
├── phase1b_*.png, phase3b_*.png, ...            # 18 Active Per-Phase Evidence captures (Root)
└── archive/                                     # 28 Deprecated / Superseded legacy captures
    ├── 01_customer_dashboard.png ...
    ├── step2_after_*.png ...
    ├── phase1_kyc_*.png ...
    └── phase3_*.png, phase4_*.png ...
```

### Inventory Counts
- **Total Audited PNG Images:** 60
- **Kept in `docs/screenshots/`:** 32 (14 Final E2E + 18 Phase Evidence)
- **Moved to `docs/screenshots/archive/`:** 28 (0 deleted)
- **Files Flagged for Manual Review:** 5 (synthetic test vector ID on card preview canvas)

---

## 2. Canonical Browser E2E Gallery (14 Final Screenshots)

These 14 screenshots represent the verified end-to-end user journeys for both retail customer and employee personas across English (LTR) and Arabic (RTL) locales at `1920×1080`:

1. `01_login_screen_en.png` — **Authentication & Simulation Banner**: Public login interface displaying prominent amber simulation disclaimer, credential inputs, and 6 one-click demo role selector buttons.
2. `02_customer_accounts_en.png` — **Customer Accounts & Balances (EN)**: Retail customer dashboard showing 3 active deposit accounts, balances formatted in EGP, masked IBANs (`EG...1001`), transaction statement, and floating RAG widget trigger.
3. `03_customer_accounts_ar.png` — **Customer Accounts & Balances (AR)**: Full right-to-left layout (`dir="rtl"`) with localized currency formatting (`ج.م`), translated navigation tabs, and Arabic transaction statement table.
4. `04_customer_complaints_en.png` — **Customer Complaints & Yield Calculator**: Customer complaints view displaying exactly 2 production complaints (`CMP-2026-0101` and `CMP-2026-0102`), confirming strict segregation from the 19 test complaints (`is_test=False`), plus interactive CD yield calculator.
5. `05_customer_rag_widget_ar.png` — **Customer Floating RAG Assistant (AR)**: Active conversational RAG assistant modal in Arabic RTL answering retail customer queries against public bank policies.
6. `06_customer_account_request_en.png` — **Simulated Account Opening Form**: Retail application form with product selection, initial deposit amount, monthly income threshold, preferred branch, and regulatory notice.
7. `07_customer_card_request_ar.png` | **Customer Request Timeline (AR)**: RTL lifecycle progression showing submitted account request (`REQ-ACC-B68ACF82` at Step 1) and approved debit card request (`REQ-CRD-06A6E643` at Step 3).
8. `08_employee_dashboard_en.png` — **Operations Executive Dashboard**: Operations overview showing real-time operational counters: 20 open complaints, 1 pending policy, 2 pending KYC cases, 2 total customers, and 4 active accounts.
9. `09_employee_requests_queue_en.png` — **Four-Eyes Requests Management**: Staff queue showing rule engine evaluations (KYC status, deposit threshold, income verification) and `APPROVE_SIMULATED` recommendation.
10. `10_employee_complaints_drawer_en.png` — **Complaint Management Drawer (EN)**: Internal triage modal for `CMP-2026-0101` displaying breached SLA (23.9h elapsed vs 12h limit), deterministic AI category recommendations, staff notes, and draft customer response.
11. `11_employee_complaints_drawer_ar.png` — **Complaint Management Drawer (AR)**: Full Arabic RTL complaint drawer showing translated SLA status (`تجاوزت المهلة`), keyword match chips, Arabic team recommendations, and mandatory reviewer confirmation checkbox.
12. `12_employee_kyc_queue_en.png` — **Synthetic KYC Queue & Document AI**: Staff KYC workspace displaying persistent `NOT VERIFIED` compliance banner, masked 14-digit IDs (`2960****1234`), case list, and card preview stage.
13. `13_employee_policy_assistant_ar.png` — **Internal Staff Policy Assistant (AR)**: Verified internal Policy Assistant tab in Arabic RTL (`PORTAL: EMPLOYEE`), showing suggested questions and query entry for National ID verification rules.
14. `14_employee_audit_trail_compliance_en.png` — **Immutable Governance Audit Trail**: Chronological audit log stream under `compliance_reviewer` role (`Nourhan Kamel`), displaying immutable records with standard UTC timestamps (`YYYY-MM-DD HH:MM:SS UTC`), actor emails, and JSON change payloads.

---

## 3. Active Per-Phase Evidence Gallery (18 Screenshots)

These screenshots provide technical verification for core milestones and edge cases:

### Phase 1b: Document AI & KYC Verification
- `phase1b_clean_upload_results.png` — Clean synthetic card inspection station with PaddleOCR extraction confidences, masked ID `2950****1234`, factory code, and `NOT VERIFIED` invariant banner.
- `phase1b_blurred_upload_warnings.png` — Blurred synthetic card showing degradation in OCR confidence scores and amber governance warnings for missing citizen name and address.
- `phase1b_request_more_info.png` — Compliance reviewer modal requesting customer resubmission with reviewer notes for blurred card case `KYC-B30BDB23`.
- `phase1b_audit_trail_utc.png` — Immutable security audit log stream under `compliance_reviewer` displaying standard UTC timestamps.
- `phase1b_arabic_kyc_workspace.png` — Bilingual Arabic RTL Document AI & KYC workspace with translated field headers, confidence metrics, and localized regulatory disclaimers.

### Phase 3b: Simulated Card Lifecycle & Dual Control
- `phase3b_card_submit.png` — Customer debit card application modal with card product selection (`Gold Debit Mastercard`), linked account dropdown, and spending limit.
- `phase3b_customer_card_timeline.png` — Customer request tracking timeline showing simulated debit card request lifecycle progression through submission and review states.
- `phase3b_employee_card_review.png` — Operations officer dual-control card review drawer showing deterministic rule evaluation results and action buttons (`Approve`, `Reject`, `Request Info`).
- `phase3b_employee_card_more_info.png` — Card request review dialog showing "Request More Information" modal with reviewer reason notes input.
- `phase3b_arabic_card_workspace.png` — Arabic RTL simulated card request tracking workspace showing translated card lifecycle states, product names, and action buttons.

### Phase 4b: Complaint Segregation & SLA Triage
- `phase4b_customer_complaints_en.png` — Customer complaints view confirming exact 2 production complaints displayed with strict filtering of synthetic test batch tickets (`is_test=False`).
- `phase4b_employee_complaints_en.png` — Staff complaint management table showing SLA indicators, category badges, priority levels, and the "Show Test Tickets" toggle.
- `phase4b_employee_complaints_ar.png` — Arabic RTL complaint management table with translated SLA statuses (`ضمن المهلة`, `تجاوزت المهلة`), categories, and internal priority tags.

### Phase 6: RAG Policy Assistant & Governance Guardrails
- `rag_customer_en.png` — Customer portal RAG assistant answering retail banking inquiry with extractive policy snippets and citation chips.
- `rag_employee_en.png` — Employee portal Policy Assistant tab answering staff compliance inquiry with verified internal policy citations.
- `rag_arabic_portal_ar.png` — Arabic RTL employee Policy Assistant query interface showing bilingual policy search and citation grounding.
- `rag_fallback_state.png` — RAG assistant extractive fallback state triggered on LLM generation timeout, returning verified grounding excerpts without hallucination.
- `rag_abstention_state.png` — RAG assistant abstention state triggered when similarity threshold is not met (score < 0.15), displaying safe out-of-scope guidance.

---

## 4. Archived Screenshots (`docs/screenshots/archive/`)

The 28 superseded images were moved to `docs/screenshots/archive/` using plain move semantics. None were deleted.

| Category | Count | Files | Archival Reason |
|---|:---:|---|---|
| **Phase 0 Baselines** | 10 | `01_customer_dashboard.png` through `10_employee_kyc_audit.png` | Superseded by canonical 14 final E2E captures. Contained early defects (e.g. `05_customer_rag_assistant.png` showing duplicate complaints rather than RAG). |
| **Step 2 Fix Verification** | 5 | `d03_reproduce_before.png`, `step2_after_*.png` | Intermediate debug captures testing individual UI bug fixes (modal z-index, empty audit table under unauthorized role). |
| **Phase 1 Early** | 3 | `phase1_kyc_*.png` | Superseded by comprehensive Phase 1b Document AI workspace captures. |
| **Phase 3 Early** | 5 | `phase3_*.png` | Contained raw internal identifiers (`prod-02`, `usr-cust-01`); superseded by Phase 3b normalized captures. |
| **Phase 4 Early** | 5 | `phase4_*.png` | Intermediate complaint views captured prior to advisory drawer styling and test ticket filtering; superseded by Phase 4b. |

---

## 5. Security & Privacy Inspection Summary

Every screenshot in this repository underwent automated OCR analysis (using PaddleOCR Arabic + English across downscaled 1280px representations) and manual visual inspection.

### Key Privacy & Compliance Findings:
- **Full 14-Digit National IDs:** 0 real national IDs detected. 5 synthetic test vector IDs (`29505140101234`, `29605140101234`) are rendered on the raw canvas preview of synthetic card fixtures in KYC queues (`12_employee_kyc_queue_en.png`, `phase1b_*`). All table columns and metadata display strictly masked IDs (`2950****1234`, `2960****1234`).
- **Full IBANs:** 0 unmasked IBANs detected across all 60 screenshots. All account numbers are masked (`EG...1001` or `EG98••••••••••••••••5678`).
- **JWT Tokens & Passwords:** 0 JWT tokens or passwords detected anywhere in viewports, URL bars, or devtools.
- **Emails Detected:** 80 occurrences across 5 views. All detected emails are synthetic demo persona addresses (`customer@nileops.eg`, `fatma.almasri@nileops.internal`, `nourhan.kamel@nileops.internal`, etc.) displayed on public demo login buttons, customer search tables, or immutable audit logs.
- **Mandatory Invariant Banner:** Prominently displayed across all Document AI views: `NOT VERIFIED — OCR extraction does not constitute official identity verification. All synthetic cases require authorized four-eyes compliance review.`
