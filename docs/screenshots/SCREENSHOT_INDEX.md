# NileOps Demo Bank — Browser E2E Screenshot Index

This index catalogues the 14 high-resolution (1920×1080) browser end-to-end screenshots captured directly from the live NileOps runtime on Windows. All customer and employee workflows were exercised across both English (LTR) and Arabic (RTL) locales, confirming visual layout, data segregation, RBAC boundaries, and compliance invariants.

---

## Screenshot Inventory Summary

| # | Filename | Viewport | Language | Portal / Role | File Size | Description |
|---|---|---|---|---|---|---|
| 01 | `01_login_screen_en.png` | 1920×1080 | English (LTR) | Public / Unauth | 71,175 B | Login page with simulation notice, credential inputs, and 6 one-click demo role buttons. |
| 02 | `02_customer_accounts_en.png` | 1920×1080 | English (LTR) | Customer (`customer1`) | 165,040 B | Retail customer overview showing 3 active accounts, balances, masked IBANs, recent transactions statement, and floating RAG assistant launcher. |
| 03 | `03_customer_accounts_ar.png` | 1920×1080 | Arabic (RTL) | Customer (`customer1`) | 156,428 B | Full Arabic RTL layout showing portfolio overview, Egyptian Pound (`ج.م`) formatting, translated navigation tabs, and RTL transaction statement. |
| 04 | `04_customer_complaints_en.png` | 1920×1080 | English (LTR) | Customer (`customer1`) | 181,361 B | Customer complaints tracking showing exactly 2 production complaints (`CMP-2026-0101` and `CMP-2026-0102`) with the 19 test complaints filtered out via `is_test=False`. Includes CD yield calculator. |
| 05 | `05_customer_rag_widget_ar.png` | 1920×1080 | Arabic (RTL) | Customer (`customer1`) | 175,884 B | Floating `PUBLIC KB` RAG assistant open on the customer portal in Arabic RTL, showing query input for minimum account balance policy. |
| 06 | `06_customer_account_request_en.png` | 1920×1080 | English (LTR) | Customer (`customer1`) | 149,557 B | Simulated account opening application form with product selection, initial deposit amount, monthly income threshold, branch selector, and compliance notice. |
| 07 | `07_customer_card_request_ar.png` | 1920×1080 | Arabic (RTL) | Customer (`customer1`) | 87,385 B | Customer request tracking timeline in Arabic RTL showing two submitted requests (`REQ-ACC-B68ACF82` at Step 1 and `REQ-CRD-06A6E643` approved at Step 3). |
| 08 | `08_employee_dashboard_en.png` | 1920×1080 | English (LTR) | Employee (`operations_officer`) | 72,473 B | Staff operations dashboard showing operational KPIs: 20 open complaints, 1 pending policy, 2 pending KYC cases, 2 total customers, and 4 active accounts. |
| 09 | `09_employee_requests_queue_en.png` | 1920×1080 | English (LTR) | Employee (`operations_officer`) | 105,630 B | Four-Eyes requests management queue showing rule engine evaluation (KYC verification, deposit threshold, income check) and `APPROVE_SIMULATED` recommendation. |
| 10 | `10_employee_complaints_drawer_en.png` | 1920×1080 | English (LTR) | Employee (`operations_officer`) | 186,535 B | Complaint management modal drawer for `CMP-2026-0101` displaying breached SLA (23.9h elapsed vs 12h threshold), deterministic rules AI suggestion, staff notes, and templated customer reply draft. |
| 11 | `11_employee_complaints_drawer_ar.png` | 1920×1080 | Arabic (RTL) | Employee (`operations_officer`) | 185,769 B | Arabic RTL complaint management modal drawer showing translated SLA status (`تجاوزت المهلة`), keyword match chips, Arabic category/team recommendations, and mandatory human review checkbox. |
| 12 | `12_employee_kyc_queue_en.png` | 1920×1080 | English (LTR) | Employee (`operations_officer`) | 117,076 B | Synthetic Document AI & KYC workspace showing `NOT VERIFIED` compliance invariant banner, masked 14-digit IDs (`2960****1234`), case list, and card preview. |
| 13 | `13_employee_policy_assistant_ar.png` | 1920×1080 | Arabic (RTL) | Employee (`operations_officer`) | 65,898 B | Internal staff verified Policy Assistant tab in Arabic RTL (`PORTAL: EMPLOYEE`), showing suggested questions and query entry for National ID verification rules. |
| 14 | `14_employee_audit_trail_compliance_en.png` | 1920×1080 | English (LTR) | Employee (`compliance_reviewer`) | 126,172 B | Immutable security & governance audit trail under `compliance_reviewer` role (Nourhan Kamel), displaying chronologically sorted immutable audit entries with UTC timestamps, actor emails, actions, and JSON details. |

---

## Technical Observations & Verification Notes

1. **Resolution & Rendering:**
   - All screenshots captured at fixed `1920×1080` desktop viewport via Chrome DevTools Protocol (`Page.captureScreenshot`).
   - Font rendering cleanly preserves Latin (Inter) and Arabic (Cairo/system sans-serif) glyphs without overlap, clipping, or un-reshaped isolated characters.
2. **Data Privacy & Invariants:**
   - Bank accounts display masked IBAN formats (`EG98••••••••••••••••5678`).
   - Synthetic national IDs display masked formats (`2960****1234`).
   - Permanent invariant banner `NOT VERIFIED — OCR extraction does not constitute official identity verification` is prominently rendered across employee KYC views.
3. **RBAC & Data Segregation:**
   - Customer view displays strictly 2 complaints (`CMP-2026-0101` and `CMP-2026-0102`); all 19 synthetic batch test tickets are excluded via `is_test=False`.
   - Employee view displays all tickets with an explicit `Show Test Tickets` toggle.
   - Audit trail endpoint access is restricted to `admin`, `compliance_reviewer`, and `branch_manager`. A request attempted under `operations_officer` produces HTTP 403 Forbidden, whereas the `compliance_reviewer` view successfully streams the full log stream.

