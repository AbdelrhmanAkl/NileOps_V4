# NileOps V4 — Phase 3: Simulated Account Opening & Card Request Delivery Report

**Date**: 2026-11-08  
**Author**: Staff Full-Stack Architect & Quality Assurance Lead  
**Scope**: Simulated Retail Account Opening, Payment Card Requests, Deterministic Rule Engine, Dual-Control Workflow, and Operations Officer RBAC Diagnosis  
**Runtime**: Native Windows 11 | PostgreSQL 16 (`nileops` dev, `nileops_test` test) | FastAPI 0.115 | React 18 / Vite / Tailwind CSS  

---

## 1. Executive Summary & Verification Metrics

Phase 3 introduces simulated retail account opening and debit card requests to NileOps V4, governed by a deterministic compliance rule engine, a strict state machine, and dual-control review (four-eyes principle). In strict adherence to Egyptian and central banking regulations, **no actual bank accounts, payment cards, or authentic IBANs are issued**; all workflows are simulated with persistent visual invariants and role boundaries.

### Key Verification Metrics
- **Automated Backend Test Suite**: **64 passed, 4 warnings in 51.92s** against isolated `nileops_test` PostgreSQL database.
- **Frontend Production Build**: `tsc && vite build` compiled cleanly with **0 errors in 843ms**.
- **Dev Database Integrity**: Zero records deleted (`users: 7, accounts: 4, transactions: 4, complaints: 21, policy_documents: 21, kyc_verifications: 3`).
- **Audit Log Trail**: 299 immutable audit entries recorded, capturing logins, account request submission, and rule evaluations.
- **Evidence Captured**: 5 high-resolution (1920×1080) real browser screenshots captured via headless Chromium CDP.

---

## 2. Priority Diagnosis: Operations Officer Workspace Data Rendering

### 2.1 The Issue Investigated
When logging in as `Sarah El-Sayed` (`operations_officer`, `ops@nileops.demo`), the Employee Portal initially showed Complaints (0), an empty Audit Trail, and an empty Policy KB, whereas `admin` displayed full data.

### 2.2 Live API Probe & Evidence
We performed live HTTP requests with Sarah's authenticated JWT token against all three endpoints:

1. **Complaints Endpoint**:
   - `GET /api/v1/employee/complaints`
   - **HTTP Status**: `200 OK`
   - **Response**: Array of 21 complaints (18 synthetic tickets + 3 demo baselines).
2. **Policy KB Endpoint**:
   - `GET /api/v1/policies`
   - **HTTP Status**: `200 OK`
   - **Response**: Array of 3 active policies (`POL-DIGITAL-001`, `POL-AML-002`, `POL-OPS-003`). All 18 `POL-TEST-*` test policies were cleanly filtered out as intended by D-06.
3. **Audit Trail Endpoint**:
   - `GET /api/v1/employee/audit-logs`
   - **HTTP Status**: `403 Forbidden`
   - **Response Body**:
     ```json
     {
       "detail": "Role 'operations_officer' is not authorized. Required: admin, compliance_reviewer, branch_manager"
     }
     ```

### 2.3 Root Cause Analysis
- **Intended RBAC**: The `403 Forbidden` on `/api/v1/employee/audit-logs` is **intended central banking RBAC policy**. Operations officers are retail line staff; regulatory audit log inspection is restricted to compliance reviewers, branch managers, and system administrators.
- **Frontend Failure Mode (The Bug)**: In `EmployeePortal.tsx`, `loadInitialData` was executed using `Promise.all([..., fetchAuditLogs()])`. When `fetchAuditLogs()` rejected with `403`, the entire `Promise.all` promise chain threw an unhandled error, halting state execution before `setComplaints` or `setPolicies` could update their respective state hooks. Furthermore, `useEffect` was bound to `[]`, preventing state reload upon switching between user profiles without a hard page reload.

### 2.4 Resolution Applied
1. Refactored `loadInitialData` to use `Promise.allSettled`, allowing complaints and policies to populate regardless of whether audit logs succeed.
2. Bound `useEffect` to `[user?.id]`, guaranteeing automatic data refetching upon switching demo users.
3. Added explicit UI banners in `EmployeePortal.tsx` for restricted and empty states:
   - **Audit Trail**: Displays `🔒 Audit Trail Access Restricted: Your role (operations_officer) does not have compliance audit inspection privileges. Access requires: admin, compliance_reviewer, or branch_manager.`
   - **Complaints & Policies**: Clear empty state cards rather than blank silent surfaces.

---

## 3. Phase 3 Architecture & Functional Implementation

### 3.1 Data Models & State Machine
Authored [`backend/app/models/requests.py`](file:///c:/AI/NileOps_V4/backend/app/models/requests.py) defining:
- `AccountOpeningRequest`: `reference_number`, `customer_id`, `product_id`, `account_type`, `currency`, `initial_deposit`, `monthly_income`, `employment_status`, `branch_code`, `status`, `idempotency_key`, `submitted_by_id`, `reviewer_id`, `reviewer_notes`, `rejection_reason`, `submitted_at`, `reviewed_at`, `completed_at`.
- `CardRequest`: `reference_number`, `customer_id`, `linked_account_id`, `card_type`, `embossed_name`, `delivery_branch`, `status`, `idempotency_key`, `submitted_by_id`, `reviewer_id`, `reviewer_notes`, `rejection_reason`, `submitted_at`, `reviewed_at`, `completed_at`.

#### Strict State Machine Transitions
Defined in [`backend/app/services/request_rules.py`](file:///c:/AI/NileOps_V4/backend/app/services/request_rules.py):
- `DRAFT` ➔ `SUBMITTED`
- `SUBMITTED` ➔ `UNDER_REVIEW`, `APPROVED_SIMULATED`, `REJECTED`, `MORE_INFO_REQUIRED`
- `UNDER_REVIEW` ➔ `APPROVED_SIMULATED`, `REJECTED`, `MORE_INFO_REQUIRED`
- `MORE_INFO_REQUIRED` ➔ `SUBMITTED`, `UNDER_REVIEW`, `REJECTED`
- `APPROVED_SIMULATED` ➔ `SIMULATED_COMPLETED`
- `REJECTED` ➔ Terminal (Conflict 409 on subsequent transitions)
- `SIMULATED_COMPLETED` ➔ Terminal (Conflict 409 on subsequent transitions)

Any illegal transition returns `HTTP 409 Conflict`.

### 3.2 Deterministic Compliance Rule Engine
Implemented in [`backend/app/services/request_rules.py`](file:///c:/AI/NileOps_V4/backend/app/services/request_rules.py) — **100% rule-based logic; zero LLM hallucination or decision-making**:
1. `RULE_KYC_VERIFICATION`: Verifies customer has an approved synthetic KYC record (`status == "APPROVED_SIMULATED"`).
2. `RULE_MIN_BALANCE`: Validates `initial_deposit` meets product requirement (`prod-01`: 2,500 EGP, `prod-02`: 10,000 EGP, `prod-03`: 1,000 EGP).
3. `RULE_MONTHLY_INCOME`: Ensures declared monthly income meets standard retail threshold (>= 3,000 EGP).
4. `RULE_CUSTOMER_CONTACT`: Checks customer profile completeness (phone and contact details on file).

If any rule fails, the engine sets `eligible = False` and outputs recommendation `MORE_INFO_REQUIRED` or `REJECTED`.

### 3.3 RBAC & Four-Eyes Segregation of Duties
- **Customer Restrictions**: Customers can only view and submit requests for their own customer ID (`current_user.id == customer_id`). Attempting to view or modify other customer requests returns `HTTP 403 Forbidden`.
- **Dual-Control / Anti-Self-Review**: The employee who created or submitted a request (`submitted_by_id`) **cannot review or approve it**; attempting self-review raises `HTTP 403 Forbidden` (`Dual-control violation: Submitter cannot self-review`).
- **Idempotency Protection**: Re-submitting an identical `idempotency_key` returns `HTTP 409 Conflict`.

### 3.4 API Endpoints Delivered
- `POST /api/v1/customer/account-requests` (Create simulated account request)
- `GET /api/v1/customer/account-requests` (List customer requests)
- `GET /api/v1/customer/account-requests/{id}` (Get customer request)
- `POST /api/v1/customer/card-requests` (Create simulated card request)
- `GET /api/v1/customer/card-requests` (List customer card requests)
- `GET /api/v1/customer/card-requests/{id}` (Get customer card request)
- `GET /api/v1/public/cards` (Public list of simulated card products)
- `GET /api/v1/employee/account-requests` (Employee request queue)
- `GET /api/v1/employee/account-requests/{id}` (Employee request detail)
- `GET /api/v1/employee/account-requests/{id}/evaluate` (Deterministic rule evaluation)
- `PATCH /api/v1/employee/account-requests/{id}/review` (Employee four-eyes review)
- `GET /api/v1/employee/card-requests` (Employee card queue)
- `PATCH /api/v1/employee/card-requests/{id}/review` (Employee card review)

---

## 4. Requirement Verification & Status Matrix

| Requirement | Implementation Details | Status |
| :--- | :--- | :--- |
| **Ops Officer Blank Tabs Diagnosis** | Live HTTP diagnosis, root cause identification, `Promise.allSettled` refactor, explicit role restriction banner. | **BROWSER TESTED** |
| **Account Opening Models & Tables** | `account_opening_requests` & `card_requests` migration-safe schema via SQLAlchemy async engine. | **API TESTED** |
| **Strict State Machine** | Full lifecycle transitions with terminal status conflict enforcement (409). | **API TESTED** |
| **Deterministic Rule Engine** | 4 rule validators (KYC check, minimum balance, monthly income, contact profile); no LLM decisions. | **API TESTED** |
| **Four-Eyes Segregation of Duties** | Self-review blocked, customer role barred from approving, employee role gating. | **API TESTED** |
| **Idempotency Protection** | Unique idempotency key enforcement per submission to prevent duplicate requests. | **API TESTED** |
| **Customer Request Form & Simulation Warning** | Form with product selector, deposits, income, and high-visibility simulation banner. | **BROWSER TESTED** |
| **Customer Lifecycle Timeline** | Real-time 4-stage visual milestone progression (`Submitted` ➔ `Under Review` ➔ `Approved` ➔ `Completed`). | **BROWSER TESTED** |
| **Employee Review Station** | Operations Workspace queue, deterministic rules card, and four-eyes action toolbar. | **BROWSER TESTED** |
| **Mandatory Rejection Reason Modal** | Modal dialog requiring explicit compliance justification for any rejected application. | **BROWSER TESTED** |
| **Bilingual Arabic RTL Support** | Complete RTL mirrored interface with high-fidelity Arabic banking terminology. | **BROWSER TESTED** |
| **Audit Log Integration** | Immutable events recorded for request submission, status changes, and rule evaluations. | **API TESTED** |

---

## 5. Visual Evidence & Screenshots

All 5 screenshots were captured at 1920×1080 resolution from the live running application via headless Chromium CDP:

1. **`phase3_customer_submit.png`** (102,706 bytes):
   - **View**: Customer Portal "Apply for Account" tab.
   - **Visual Details**: Prominent amber simulation banner (*"SIMULATED DIGITAL BANKING PLATFORM — SIMULATION — No real bank account or payment card is created..."*), product selector, initial deposit input (`5,000.00 EGP`), income input (`12,000.00 EGP`), branch selector, and policy summary note.
2. **`phase3_customer_timeline.png`** (116,856 bytes):
   - **View**: Customer Portal "My Requests (1)" tab.
   - **Visual Details**: Submitted request `REQ-ACC-B68ACF82` for `prod-02 (savings)`, initial deposit `15,000.00 EGP`, and lifecycle milestone timeline with active milestone #1 (`Submitted`) highlighted in amber. Dynamic footer displays `PostgreSQL 16`.
3. **`phase3_employee_review.png`** (98,910 bytes):
   - **View**: Operations Workspace "Requests Queue (1)" tab under `Sarah El-Sayed`.
   - **Visual Details**: Queue showing `REQ-ACC-B68ACF82`, review station with customer and product metadata, rule evaluation trigger, and action buttons (`Start Review`, `Approve (Simulated)`, `Request More Info`, `Reject (with Reason)`).
4. **`phase3_employee_rejection.png`** (154,705 bytes):
   - **View**: Rejection decision modal overlay.
   - **Visual Details**: Centered modal with crimson border, mandatory rejection reason textarea populated with justification (*"Simulated Test: Incomplete source of funds documentation provided."*), reviewer decision memo textarea, and `Confirm Decision` button.
5. **`phase3_arabic_requests.png`** (94,889 bytes):
   - **View**: Full Arabic RTL mirrored Operations Workspace.
   - **Visual Details**: Mirrored navigation, translated simulation warning (*"محطة مراجعة طلبات فتح الحسابات والبطاقات التقديرية — SIMULATION..."*), Arabic request cards, metadata fields, and action buttons (*"بدء المراجعة"*, *"اعتماد المحاكاة"*, *"طلب استيفاء بيانات"*, *"رفض الطلب مع السبب"*).

---

## 6. Verification Commands & Evidence

### 6.1 Pytest Suite against Isolated Test Database (`nileops_test`)
```
PS C:\AI\NileOps_V4\backend> pytest -q
................................................................         [100%]
64 passed, 4 warnings in 51.92s
```
*(4 deprecation warnings from Starlette/FastAPI HTTP status code aliases and Paddle extension; zero failures).*

### 6.2 Frontend Production Build
```
PS C:\AI\NileOps_V4\frontend> npm.cmd run build
> nileops-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 38 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.56 kB │ gzip:  0.37 kB
dist/assets/index-ClP6i1pd.css   32.39 kB │ gzip:  6.04 kB
dist/assets/index-Bow3dGVn.js   278.47 kB │ gzip: 76.01 kB
✓ built in 843ms
```

### 6.3 Development Database Row Counts (Zero Deletions)
```
users: 7
accounts: 4
transactions: 4
complaints: 21
policy_documents: 21
kyc_verifications: 3
audit_logs: 299
account_opening_requests: 1
card_requests: 0
```
All baseline records from prior phases remain 100% intact. Zero record modifications or deletions occurred.

