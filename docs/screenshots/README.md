# NileOps V4 — Visual Verification Screenshots & Audit Gallery

This directory contains authentic visual inspection screenshots captured directly from the live running NileOps application at 1920×1080 resolution using headless Chromium CDP automation.

---

## 1. Initial Visual Inspection Gallery (Phase 0 Audit)

Captured 2026-11-08 from initial baseline state:

1. `01_customer_dashboard.png` — **Customer Portal: Main Dashboard**: Overview displaying welcome header (`Tarek Nour`), summary metric cards (Total Balance, Active Accounts, Pending Inquiries), Quick Transfer widget, and Bill Payment action block.
2. `02_customer_accounts.png` — **Customer Portal: Accounts & Balances**: Two deposit account cards (Current Account `EG...1001` and Savings Account `EG...1002`) with balances, currency badges, and masked IBAN numbers.
3. `03_customer_transactions.png` — **Customer Portal: Transaction History**: Statement table displaying categorized synthetic transactions with transaction type icons, counterparty names, timestamps, and status badges.
4. `04_customer_complaint_submission.png` — **Customer Portal: Complaint Submission Modal**: Dialog form allowing customers to log inquiries and disputes, with bilingual category selectors and priority options.
5. `05_customer_rag_assistant.png` — **Customer Portal: Customer Complaints Section**: Section displaying customer complaint cards (`Card captured by ATM machine at branch`, `ATM Cash Retained Issue`). *(See Formal Correction Note below)*.
6. `06_employee_dashboard.png` — **Employee Portal: Executive Dashboard**: Operations overview displaying SLA compliance metrics, pending queues, active case counters, and system health status.
7. `07_employee_customer_search.png` — **Employee Portal: Customer Search**: Customer account search and KYC profile inspection drawer.
8. `08_employee_complaint_management.png` — **Employee Portal: Complaint Lifecycle Queue**: Internal triage station for managing customer dispute tickets, reassignment, and status resolution.
9. `09_employee_policy_governance.png` — **Employee Portal: Policy Governance**: Internal policy draft creation, four-eyes approval workflow, and active bank policy library.
10. `10_employee_kyc_audit.png` — **Employee Portal: Synthetic KYC Review (Initial)**: Initial baseline state of KYC verification queue before Phase 1b Document AI integration.

### Formal Correction Note Regarding Image 05
> **Correction Note (2026-11-08):**
> In the prior visual inspection submission, image `05_customer_rag_assistant.png` was initially labeled as *"Customer Portal — AI Banking Policy Assistant (RAG Chat)"*, and then erroneously described in a subsequent note as the Yield Calculator.
>
> In reality, the Customer Portal frontend does not yet mount a dedicated customer-facing RAG chat widget. When screenshot automation navigated to vertical offset y=950, image 05 actually captured the **"My Complaints & Service Requests" (`#customer-complaints`)** section of the customer dashboard, displaying duplicated complaint cards created during earlier test runs. A dedicated conversational RAG UI component for retail customers is scheduled for future frontend development phases.

---

## 2. Phase 0 Step 2 UI Fixes Gallery

Captured 2026-11-08 after applying targeted UI defect fixes (D-01 through D-06):

1. `step2_after_footer.png` — **Dynamic Database Health Footer (D-01)**: Demonstrates footer displaying dynamic database engine (`PostgreSQL (asyncpg)`) queried from `/health`, replacing static hardcoded text.
2. `step2_before_modal.png` — **Complaint Modal Header Overlay Bug (D-03 Baseline)**: Reproduces defect D-03 in English LTR where the fixed application header (`z-20`) was rendering on top of the complaint modal backdrop (`z-50`).
3. `step2_after_modal.png` — **Complaint Modal Header Overlay Fix (D-03 Resolution)**: Demonstrates modal overlay elevated to `z-50` with sticky header adjusted to `z-20`, rendering modal correctly over all underlying elements without clipping.
4. `step2_after_policies.png` — **Policy Document Filtering (D-06)**: Demonstrates policy governance table cleanly excluding synthetic test policies matching `POL-TEST-*` from normal operational view.
5. `step2_after_audit.png` — **Audit Trail Tab (RBAC Restricted View)**: 
   > **Note on `step2_after_audit.png`:** Captured while logged in as `operations_officer` (`Sarah Fahmy`). In NileOps RBAC policy, access to `/api/v1/employee/audit-logs` is strictly restricted to `compliance_reviewer`, `branch_manager`, and `admin`. Because the tab was opened under an operations officer, the table returned an empty state. See `phase1b_audit_trail_utc.png` below for the fully populated audit trail under authorized compliance reviewer `Nourhan Kamel`.

---

## 3. Phase 1b Document AI & KYC Workspace Gallery

Captured 2026-11-08 verifying Document AI OCR pipeline, synthetic card previews, and governance workflows:

1. `phase1b_clean_upload_results.png` — **Clean Synthetic Card Upload & OCR Inspection Station**:
   - **User**: `Nourhan Kamel` (`compliance_reviewer`).
   - **Case**: `KYC-E4CD2BC6` (Synthetic National ID `2950****1234`).
   - **Visual Preview**: Genuine synthetic ID card rendered inside the dark inspection viewport (`ProtectedImage` authenticated blob loader), displaying synthetic photo placeholder, factory code `ED2676749`, fake 14-digit national ID `29505140101234`, and disclaimer banner.
   - **Extracted Attributes**: Real PaddleOCR extraction with labeled engine confidence: National ID (`100.0%`, `FORMAT_VALID`), Factory Code (`99.9%`, `EXTRACTED`), Derived Birth Date (`1995-05-14`, `CALENDAR_VALID`), Derived Governorate (`القاهرة`, `GOV_MATCHED`). Missing name and residential address are flagged with `MISSING` badges and amber warnings.
   - **Compliance Invariant**: Persistent warning banner: *"MANDATORY COMPLIANCE INVARIANT: NOT VERIFIED — OCR extraction does not constitute official identity verification. All synthetic cases require authorized four-eyes compliance review."*

2. `phase1b_blurred_upload_warnings.png` — **Blurred Synthetic Card Quality Degradation & Warnings**:
   - **User**: `Nourhan Kamel` (`compliance_reviewer`).
   - **Case**: `KYC-B30BDB23` (Synthetic National ID `2960****1234`).
   - **Visual Preview**: Blurred synthetic card displayed in preview stage showing degraded text contrast and soft edges.
   - **OCR Confidence**: Demonstrates severe confidence degradation under Gaussian blur: Citizen Full Name confidence drops to `28.0%`, Residential Address drops to `0.0%`.
   - **Governance Warnings**: Yellow warning callout: *"Citizen name is missing or unextracted. Address is incomplete or missing geographic structural tokens."*

3. `phase1b_request_more_info.png` — **Request More Information Compliance Workflow**:
   - **User**: `Nourhan Kamel` (`compliance_reviewer`).
   - **Case**: `KYC-B30BDB23`.
   - **Modal Dialog**: Open modal *"Request Info: KYC-B30BDB23"* with reviewer notes input: *"Image quality alert: National ID scan is severely blurred with low confidence (27.9%); please upload a sharp, high-contrast scan of the card."* Actions: *Cancel* and *Send Information Request* (`INFO_REQUESTED`).

4. `phase1b_audit_trail_utc.png` — **Immutable Audit Trail with Standard UTC Timestamps**:
   - **User**: `Nourhan Kamel` (`compliance_reviewer`).
   - **Table View**: Live audit log stream demonstrating complete timestamps in `YYYY-MM-DD HH:MM:SS UTC` format (e.g., `2026-11-08 04:50:29 UTC`, `2026-11-08 04:50:28 UTC`).
   - **Events Captured**: Immutable log records for user logins (`LOGIN`), synthetic card uploads (`UPLOAD_KYC_DOCUMENT`), and status transitions with full JSON details.

5. `phase1b_arabic_kyc_workspace.png` — **Bilingual Arabic RTL KYC & Document AI Workspace**:
   - **User**: `Nourhan Kamel` (`compliance_reviewer`).
   - **Interface**: Full right-to-left layout (`dir="rtl"`) with high-fidelity Arabic typography and localized terminology:
     - Header: `محطة عمل تدقيق وثائق الهوية (Document AI & KYC)`
     - Mandatory Invariant: `تنبيه إلزامي للرقابة والمطابقة المصرفية: NOT VERIFIED — استخراج OCR لا يشكل بأي حال تحققا رسميا من الهوية...`
     - Badges: `أرقام قومية محجوبة افتراضيا`, `بيئة اصطناعية 100%`
     - Attribute Table: `السمات المستخرجة وثقة المحرك (OCR Engine Confidence)`
     - Column Headers: `الحقل`, `القيمة المستخرجة`, `ثقة محرك OCR`, `حالة الحقل`
     - Field Rows: `الرقم القومي`, `الاسم بالكامل` (`مفقود من الوثيقة`), `محل الإقامة` (`مفقود من الوثيقة`), `كود المصنع`, `تاريخ الميلاد المحسوب`, `المحافظة المحسوبة`.


---

## 4. Phase 3 Simulated Account Opening & Card Requests Gallery

Captured 2026-11-08 verifying simulated retail account opening, debit card issuance requests, deterministic rule evaluation, state machines, and dual-control governance:

1. `phase3_customer_submit.png` — **Customer Account Opening Form & Simulation Invariant**:
   - **User**: `Ahmed Mansour` (`customer1@nileops.demo`).
   - **View**: Customer Portal "Apply for Account" tab.
   - **Prominent Banner**: High-visibility amber simulation banner: *"SIMULATED DIGITAL BANKING PLATFORM — SIMULATION — No real bank account or payment card is created. All products and numbers are simulated for operational demo purposes."* with badge `100% Synthetic Demo`.
   - **Form Configuration**: Product dropdown (`Classic Current Account (2,500 EGP)`), Initial Deposit (`5,000.00 EGP`), Declared Monthly Income (`12,000.00 EGP`), Employment Status (`Employed (Salaried)`), Preferred Branch (`Zamalek Main Branch — Cairo`).
   - **Policy Summary**: Clear bullet points reminding customer of synthetic KYC requirement and four-eyes review controls.

2. `phase3_customer_timeline.png` — **Customer Request Timeline & Real-Time Lifecycle Progression**:
   - **User**: `Ahmed Mansour` (`customer1@nileops.demo`).
   - **View**: Customer Portal "My Requests (1)" tab.
   - **Card & Milestone Progression**: Submitted account request `REQ-ACC-B68ACF82` for `prod-02 (savings)` with `15,000.00 EGP` initial deposit.
   - **Lifecycle Timeline**: 4-stage progression track (`Submitted` highlighted as active milestone #1 in amber -> `Under Review` -> `Approved` -> `Completed`).
   - **Footer Verification**: Dynamic health footer confirming `PostgreSQL 16` connectivity without hardcoded assumptions.

3. `phase3_employee_review.png` — **Employee Review Station & Four-Eyes Governance**:
   - **User**: `Sarah El-Sayed` (`operations_officer`).
   - **View**: Operations Workspace "Requests Queue (1)" tab.
   - **Queue Selection**: Account request `REQ-ACC-B68ACF82` selected from the left queue list (`SUBMITTED`, `15,000 EGP`, `2026-11-08 05:54:17 UTC`).
   - **Review Station**: Right pane detailing Customer ID `usr-cust-01`, Product ID `prod-02 (savings)`, Employment Status `EMPLOYED`, Branch `CAI-01`.
   - **Deterministic Rules & Action Toolbar**: "Re-evaluate Rules" trigger and 4 distinct role-gated action buttons: `Start Review` (blue), `Approve (Simulated)` (emerald), `Request More Info` (purple), `Reject (with Reason)` (crimson).

4. `phase3_employee_rejection.png` — **Mandatory Rejection Reason Modal**:
   - **User**: `Sarah El-Sayed` (`operations_officer`).
   - **View**: Centered modal overlay *"Execute Review Decision: REQ-ACC-B68ACF82"*.
   - **State Machine Enforcement**: Badge `Action: REJECTED`.
   - **Mandatory Justification**: Red highlighted input *"Mandatory Rejection Reason:"* containing entered explanation: *"Simulated Test: Incomplete source of funds documentation provided."*
   - **Dual-Control Documentation**: Reviewer notes & decision memo textarea for internal compliance archiving. Actions: `Cancel` and `Confirm Decision`.

5. `phase3_arabic_requests.png` — **Bilingual Arabic RTL Operations Workspace**:
   - **User**: `Sarah El-Sayed` (`operations_officer`).
   - **Interface**: Full Right-to-Left layout (`dir="rtl"`) with complete Arabic terminology:
     - Header: `مساحة عمل العمليات — Sarah El-Sayed`
     - Tab: `طلبات الحسابات والبطاقات (1)`
     - Simulation Warning: `محطة مراجعة طلبات فتح الحسابات والبطاقات التقديرية — SIMULATION — تخضع جميع طلبات الحسابات والبطاقات لقواعد الفحص الآلية ومبدأ المراجعة المزدوجة (Four-Eyes Principle)...`
     - Filter Bar: `الكل`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED_SIMULATED`, `MORE_INFO_REQUIRED`, `REJECTED`, `SIMULATED_COMPLETED`
     - Action Buttons: `بدء المراجعة`, `اعتماد المحاكاة (Approve)`, `طلب استيفاء بيانات`, `رفض الطلب مع السبب`.
