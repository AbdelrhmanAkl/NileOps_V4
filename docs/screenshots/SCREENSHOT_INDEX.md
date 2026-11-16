# NileOps Demo Bank — Visual Screenshot Index & Audit Registry

This index catalogues all visual inspection screenshots captured across the NileOps platform runtime at 1920×1080 resolution on Windows. Every screenshot has been directly viewed and scanned for data privacy compliance, RBAC boundaries, and regulatory invariants.

---

## 1. Directory Inventory Summary

| Classification | Location | Image Count | Description |
|---|---|:---:|---|
| **FINAL** | `docs/screenshots/` | 14 | Canonical browser E2E test suite captures covering English (LTR) and Arabic (RTL) journeys for retail customer and employee personas. |
| **EVIDENCE** | `docs/screenshots/` | 25 | Target phase test verification evidence (Phase 1b Document AI, Phase 3b Account/Card Workflows, Phase 4b Complaints, Phase 6 RAG Governance, Phase 8b KPIs/Mismatch, and Phase 8c Ops Assistant & Rate Limiting). |
| **ARCHIVED** | `docs/screenshots/archive/` | 28 | Deprecated or superseded screenshots from earlier development phases (duplicate test tickets, initial baseline captures, intermediate debug captures). |
| **TOTAL** | — | **67** | **100% accounted for (39 kept in root, 28 moved to archive, 0 deleted).** |

---

## 2. Final Browser E2E Screenshots (14 Images — Root)

| # | Filename | Viewport | Language | Portal / Screen | What It Shows | Status |
|---|---|---|---|---|---|---|
| 01 | `01_login_screen_en.png` | 1920×1080 | English (LTR) | Authentication / Login | Public login screen with amber simulation notice, credential inputs, and 6 one-click demo role buttons. | `FINAL` |
| 02 | `02_customer_accounts_en.png` | 1920×1080 | English (LTR) | Customer / Accounts & Balances | Customer portfolio dashboard showing 3 active deposit accounts, balances in EGP, masked IBANs, statement table, and floating RAG assistant launcher. | `FINAL` |
| 03 | `03_customer_accounts_ar.png` | 1920×1080 | Arabic (RTL) | Customer / Accounts & Balances | Fully localized Arabic RTL portfolio overview, Egyptian Pound (`ج.م`) currency badges, translated navigation tabs, and RTL transaction statements. | `FINAL` |
| 04 | `04_customer_complaints_en.png` | 1920×1080 | English (LTR) | Customer / Complaints & Yield | Customer complaints tracking showing exactly 2 production complaints (`CMP-2026-0101` and `CMP-2026-0102`) with test tickets filtered out; includes CD yield calculator. | `FINAL` |
| 05 | `05_customer_rag_widget_ar.png` | 1920×1080 | Arabic (RTL) | Customer / RAG Assistant Widget | Floating `PUBLIC KB` RAG policy assistant widget open on the customer portal in Arabic RTL, showing query input for minimum account balance policy. | `FINAL` |
| 06 | `06_customer_account_request_en.png` | 1920×1080 | English (LTR) | Customer / Apply for Account | Simulated account application form with product selection, initial deposit amount, monthly income threshold, branch selector, and compliance notice. | `FINAL` |
| 07 | `07_customer_card_request_ar.png` | 1920×1080 | Arabic (RTL) | Customer / Request Tracking | Customer request tracking timeline in Arabic RTL showing two submitted requests (`REQ-ACC-B68ACF82` at Step 1 and `REQ-CRD-06A6E643` approved at Step 3). | `FINAL` |
| 08 | `08_employee_dashboard_en.png` | 1920×1080 | English (LTR) | Employee / Operations Dashboard | Staff operations dashboard showing operational KPIs: 20 open complaints, 1 pending policy, 2 pending KYC cases, 2 total customers, and 4 active accounts. | `FINAL` |
| 09 | `09_employee_requests_queue_en.png` | 1920×1080 | English (LTR) | Employee / Requests Management | Four-Eyes requests management queue showing rule engine evaluation (KYC verification, deposit threshold, income check) and `APPROVE_SIMULATED` recommendation. | `FINAL` |
| 10 | `10_employee_complaints_drawer_en.png` | 1920×1080 | English (LTR) | Employee / Complaints Drawer | Complaint drawer for `CMP-2026-0101` displaying breached SLA (23.9h elapsed vs 12h threshold), deterministic rules suggestion, staff notes, and draft customer reply. | `FINAL` |
| 11 | `11_employee_complaints_drawer_ar.png` | 1920×1080 | Arabic (RTL) | Employee / Complaints Drawer | Arabic RTL complaint management drawer showing translated SLA status (`تجاوزت المهلة`), keyword match chips, Arabic category recommendations, and review checkbox. | `FINAL` |
| 12 | `12_employee_kyc_queue_en.png` | 1920×1080 | English (LTR) | Employee / KYC Review Queue | Synthetic Document AI & KYC workspace showing `NOT VERIFIED` compliance invariant banner, masked 14-digit IDs (`2960****1234`), case list, and card preview. | `FINAL` |
| 13 | `13_employee_policy_assistant_ar.png` | 1920×1080 | Arabic (RTL) | Employee / Policy Assistant | Internal staff Policy Assistant tab in Arabic RTL (`PORTAL: EMPLOYEE`), showing suggested questions and query entry for National ID verification rules. | `FINAL` |
| 14 | `14_employee_audit_trail_compliance_en.png` | 1920×1080 | English (LTR) | Employee / Audit Trail | Immutable security & governance audit trail under `compliance_reviewer` role (Nourhan Kamel), displaying sorted audit entries with UTC timestamps, actor emails, and JSON details. | `FINAL` |

---

## 3. Active Per-Phase Evidence Screenshots (18 Images — Root)

| Filename | Phase / Feature | Viewport | Language | What It Shows | Status |
|---|---|---|---|---|---|
| `phase1b_clean_upload_results.png` | Phase 1b Document AI | 1920×1080 | English (LTR) | Clean synthetic card inspection station with PaddleOCR extraction confidences, masked ID `2950****1234`, factory code, and `NOT VERIFIED` invariant banner. | `EVIDENCE` |
| `phase1b_blurred_upload_warnings.png` | Phase 1b Document AI | 1920×1080 | English (LTR) | Blurred synthetic card showing degradation in OCR confidence scores and amber governance warnings for missing citizen name and residential address. | `EVIDENCE` |
| `phase1b_request_more_info.png` | Phase 1b Document AI | 1920×1080 | English (LTR) | Compliance reviewer modal dialog requesting customer resubmission with reviewer notes for blurred card case `KYC-B30BDB23`. | `EVIDENCE` |
| `phase1b_audit_trail_utc.png` | Phase 1b Governance | 1920×1080 | English (LTR) | Immutable security audit log stream under `compliance_reviewer` displaying standard UTC timestamps (`YYYY-MM-DD HH:MM:SS UTC`) and event details. | `EVIDENCE` |
| `phase1b_arabic_kyc_workspace.png` | Phase 1b Bilingual | 1920×1080 | Arabic (RTL) | Full Arabic RTL Document AI & KYC workspace with translated field headers, confidence metrics, and localized regulatory disclaimers. | `EVIDENCE` |
| `phase3b_card_submit.png` | Phase 3b Card Lifecycle | 1920×1080 | English (LTR) | Customer debit card application modal with card product selection (`Gold Debit Mastercard`), linked account dropdown, and spending limit. | `EVIDENCE` |
| `phase3b_customer_card_timeline.png` | Phase 3b Card Lifecycle | 1920×1080 | English (LTR) | Customer request tracking timeline showing simulated debit card request lifecycle progression through submission and review states. | `EVIDENCE` |
| `phase3b_employee_card_review.png` | Phase 3b Dual Control | 1920×1080 | English (LTR) | Operations officer dual-control card review drawer showing deterministic rule evaluation results and action buttons (`Approve`, `Reject`, `Request Info`). | `EVIDENCE` |
| `phase3b_employee_card_more_info.png` | Phase 3b Dual Control | 1920×1080 | English (LTR) | Card request review dialog showing "Request More Information" modal with reviewer reason notes input. | `EVIDENCE` |
| `phase3b_arabic_card_workspace.png` | Phase 3b Bilingual | 1920×1080 | Arabic (RTL) | Arabic RTL simulated card request tracking workspace showing translated card lifecycle states, product names, and action buttons. | `EVIDENCE` |
| `phase4b_customer_complaints_en.png` | Phase 4b Complaints | 1920×1080 | English (LTR) | Customer complaints view confirming exact 2 production complaints displayed with strict filtering of synthetic test batch tickets (`is_test=False`). | `EVIDENCE` |
| `phase4b_employee_complaints_en.png` | Phase 4b Complaints | 1920×1080 | English (LTR) | Staff complaint management table showing SLA indicators, category badges, priority levels, and the "Show Test Tickets" toggle. | `EVIDENCE` |
| `phase4b_employee_complaints_ar.png` | Phase 4b Complaints | 1920×1080 | Arabic (RTL) | Arabic RTL complaint management table with translated SLA statuses (`ضمن المهلة`, `تجاوزت المهلة`), categories, and internal priority tags. | `EVIDENCE` |
| `15_employee_kpi_dashboard_en.png` | Phase 8b Handbook KPIs | 1920×1080 | English (LTR) | Employee Operations KPI Dashboard displaying real operational metrics, compliance audit scores, and synthetic seeded workload notice. | `EVIDENCE` |
| `16_employee_kpi_dashboard_ar.png` | Phase 8b Handbook KPIs | 1920×1080 | Arabic (RTL) | Localized Arabic RTL operations KPI dashboard showing compliance SLA breaches, audit coverage metrics, and status badges. | `EVIDENCE` |
| `17_employee_kyc_mismatch_inspector_en.png` | Phase 8b KYC Checks | 1920×1080 | English (LTR) | Document AI KYC Inspector displaying deterministic cross-field mismatch rules (birthdate vs ID, governorate match, OCR confidence thresholds). | `EVIDENCE` |
| `18_ops_assistant_normal_en.png` | Phase 8c Ops Assistant | 1920×1080 | English (LTR) | Allowlisted Ops Assistant copilot answering request status inquiry with grounded policy citations and allowlisted tool traces (`read_request_status [ALLOWED]`). | `EVIDENCE` |
| `19_ops_assistant_draft_human_review_en.png` | Phase 8c Ops Assistant | 1920×1080 | English (LTR) | Allowlisted Ops Assistant retrieving customer complaint and generating draft reply card with "MANDATORY HUMAN REVIEW" badge and AI suggestion disclaimer. | `EVIDENCE` |
| `20_ops_assistant_injection_denied_en.png` | Phase 8c Adversarial Defense | 1920×1080 | English (LTR) | Security guardrail intercepting adversarial prompt injection ("Ignore previous instructions"), denying unauthorized action, and escalating to human review. | `EVIDENCE` |
| `21_ops_assistant_rate_limited_ar.png` | Phase 8c Rate Limiting | 1920×1080 | Arabic (RTL) | Localized Arabic RTL rate-limiting alert banner (`HTTP 429 Too Many Requests`) displaying `Retry-After: 30s` with sliding-window protection. | `EVIDENCE` |
| `rag_customer_en.png` | Phase 6 RAG Governance | 1920×1080 | English (LTR) | Customer portal RAG assistant answering retail banking inquiry with extractive policy snippets and citation chips. | `EVIDENCE` |
| `rag_employee_en.png` | Phase 6 RAG Governance | 1920×1080 | English (LTR) | Employee portal Policy Assistant tab answering staff compliance inquiry with verified internal policy citations. | `EVIDENCE` |
| `rag_arabic_portal_ar.png` | Phase 6 RAG Governance | 1920×1080 | Arabic (RTL) | Arabic RTL employee Policy Assistant query interface showing bilingual policy search and citation grounding. | `EVIDENCE` |
| `rag_fallback_state.png` | Phase 6 RAG Governance | 1920×1080 | English (LTR) | RAG assistant extractive fallback state triggered on LLM generation timeout, returning verified grounding excerpts without hallucination. | `EVIDENCE` |
| `rag_abstention_state.png` | Phase 6 RAG Governance | 1920×1080 | English (LTR) | RAG assistant abstention state triggered when similarity threshold is not met (score < 0.15), displaying safe out-of-scope guidance. | `EVIDENCE` |

---

## 4. Archived Screenshots (28 Images — `docs/screenshots/archive/`)

| Filename | Original Phase | Viewport | Language | What It Shows | Status & Archival Rationale |
|---|---|---|---|---|---|
| `archive/01_customer_dashboard.png` | Phase 0 Baseline | 1920×1080 | English | Early customer dashboard baseline capture before Phase 3-7 features. | `ARCHIVED`: Superseded by canonical `02_customer_accounts_en.png`. |
| `archive/02_customer_accounts.png` | Phase 0 Baseline | 1920×1080 | English | Early customer accounts baseline showing initial deposit balances. | `ARCHIVED`: Superseded by canonical `02_customer_accounts_en.png`. |
| `archive/03_customer_transactions.png` | Phase 0 Baseline | 1920×1080 | English | Early customer transaction table baseline before statement enhancements. | `ARCHIVED`: Superseded by canonical `02_customer_accounts_en.png`. |
| `archive/04_customer_complaint_submission.png` | Phase 0 Baseline | 1920×1080 | English | Early complaint modal before layout and z-index overlay fixes. | `ARCHIVED`: Superseded by canonical `04_customer_complaints_en.png`. |
| `archive/05_customer_rag_assistant.png` | Phase 0 Baseline | 1920×1080 | English | Incorrect capture: erroneously labeled as RAG assistant, actually shows 20 duplicate test complaints. | `ARCHIVED`: Superseded by real RAG widget capture `05_customer_rag_widget_ar.png`. |
| `archive/06_employee_dashboard.png` | Phase 0 Baseline | 1920×1080 | English | Early operations officer dashboard capture before Phase 1-4 queues. | `ARCHIVED`: Superseded by canonical `08_employee_dashboard_en.png`. |
| `archive/07_employee_customer_search.png` | Phase 0 Baseline | 1920×1080 | English | Early customer search table showing initial seed customers. | `ARCHIVED`: Superseded by canonical `08_employee_dashboard_en.png`. |
| `archive/08_employee_complaint_management.png` | Phase 0 Baseline | 1920×1080 | English | Early staff complaint table before advisory drawer and SLA engine. | `ARCHIVED`: Superseded by canonical `10_employee_complaints_drawer_en.png`. |
| `archive/09_employee_policy_governance.png` | Phase 0 Baseline | 1920×1080 | English | Early policy governance table before test policy filtering. | `ARCHIVED`: Superseded by canonical `13_employee_policy_assistant_ar.png`. |
| `archive/10_employee_kyc_audit.png` | Phase 0 Baseline | 1920×1080 | English | Early KYC review table before Document AI OCR pipeline integration. | `ARCHIVED`: Superseded by canonical `12_employee_kyc_queue_en.png`. |
| `archive/d03_reproduce_before.png` | Step 2 Debugging | 1920×1080 | English | Defect reproduction capture showing complaint modal header clipping. | `ARCHIVED`: Debugging artifact; defect D-03 resolved in Phase 0. |
| `archive/step2_after_audit.png` | Step 2 Debugging | 1920×1080 | English | Audit trail table returning empty state under unauthorized role (`operations_officer`). | `ARCHIVED`: Superseded by authorized view `14_employee_audit_trail_compliance_en.png`. |
| `archive/step2_after_footer.png` | Step 2 Debugging | 1920×1080 | English | Isolated capture of dynamic PostgreSQL health footer. | `ARCHIVED`: Captured as single-element fix verification; integrated in final views. |
| `archive/step2_after_modal.png` | Step 2 Debugging | 1920×1080 | English | Isolated capture of complaint modal z-index fix. | `ARCHIVED`: Captured as single-element fix verification; integrated in final views. |
| `archive/step2_after_policies.png` | Step 2 Debugging | 1920×1080 | English | Isolated capture of policy table excluding `POL-TEST-*`. | `ARCHIVED`: Captured as single-element fix verification; integrated in final views. |
| `archive/phase1_kyc_extracted_fields.png` | Phase 1 Early | 1920×1080 | English | Early Document AI OCR extraction preview with synthetic card fixture. | `ARCHIVED`: Superseded by high-fidelity Phase 1b capture `phase1b_clean_upload_results.png`. |
| `archive/phase1_kyc_queue_and_upload.png` | Phase 1 Early | 1920×1080 | English | Early synthetic card upload modal dialog over KYC queue. | `ARCHIVED`: Superseded by canonical `12_employee_kyc_queue_en.png`. |
| `archive/phase1_kyc_review_action.png` | Phase 1 Early | 1920×1080 | English | Early rejection action dialog for synthetic KYC case `KYC-2026-0042`. | `ARCHIVED`: Superseded by Phase 1b workflow capture `phase1b_request_more_info.png`. |
| `archive/phase3_arabic_requests.png` | Phase 3 Early | 1920×1080 | Arabic | Early Arabic RTL requests queue before Phase 3b identifier normalization. | `ARCHIVED`: Superseded by normalized capture `phase3b_arabic_card_workspace.png`. |
| `archive/phase3_customer_submit.png` | Phase 3 Early | 1920×1080 | English | Early account opening application form before Phase 3b card workflows. | `ARCHIVED`: Superseded by canonical `06_customer_account_request_en.png`. |
| `archive/phase3_customer_timeline.png` | Phase 3 Early | 1920×1080 | English | Early request timeline showing raw internal product ID (`prod-02`). | `ARCHIVED`: Superseded by Phase 3b humanized timeline `phase3b_customer_card_timeline.png`. |
| `archive/phase3_employee_rejection.png` | Phase 3 Early | 1920×1080 | English | Early employee rejection action modal with internal product IDs. | `ARCHIVED`: Superseded by Phase 3b review drawer `phase3b_employee_card_review.png`. |
| `archive/phase3_employee_review.png` | Phase 3 Early | 1920×1080 | English | Early employee review drawer before Phase 3b debit card actions. | `ARCHIVED`: Superseded by canonical `09_employee_requests_queue_en.png`. |
| `archive/phase4_account_review_3b_fixes.png` | Phase 4 Early | 1920×1080 | English | Intermediate review drawer testing Phase 3b display fixes. | `ARCHIVED`: Superseded by canonical `09_employee_requests_queue_en.png`. |
| `archive/phase4_arabic_complaints_workspace.png` | Phase 4 Early | 1920×1080 | Arabic | Early Arabic RTL complaints table before advisory drawer integration. | `ARCHIVED`: Superseded by canonical `11_employee_complaints_drawer_ar.png`. |
| `archive/phase4_customer_complaint_segregation.png` | Phase 4 Early | 1920×1080 | English | Intermediate capture verifying exclusion of 19 test complaints. | `ARCHIVED`: Superseded by canonical `04_customer_complaints_en.png`. |
| `archive/phase4_employee_complaint_advisory_drawer.png` | Phase 4 Early | 1920×1080 | English | Intermediate capture of complaint advisory drawer during development. | `ARCHIVED`: Superseded by canonical `10_employee_complaints_drawer_en.png`. |
| `archive/phase4_employee_complaints_table.png` | Phase 4 Early | 1920×1080 | English | Intermediate employee complaints table before Phase 4b styling. | `ARCHIVED`: Superseded by Phase 4b evidence `phase4b_employee_complaints_en.png`. |
