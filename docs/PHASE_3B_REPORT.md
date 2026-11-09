# NileOps V4 — Phase 3b Implementation & Verification Report

**Date:** 2026-11-08  
**Scope:** Phase 3b: Simulated Card Request End-to-End, Discrepancies Reconciliation, DB Table Management & Backup Audit, and Roles Specification  
**Environment:** Windows 11 Native Architecture (PostgreSQL 16 Native Daemon, FastAPI Uvicorn Daemon, React 18 / Vite 5 Frontend Dev Server, Qdrant Vector Engine)  
**Governance Rules:** Zero git commits, zero git pushes, zero database record deletions, strict test isolation against `nileops_test`.

---

## 1. Executive Summary

Phase 3b completes the operational simulation for **Card Issuance Requests**, bridging retail banking customer self-service with dual-control back-office operations. All five core requirements and all screenshot feedback items have been implemented, tested, and empirically verified:

1. **Card Request End-to-End Flow:** Proven via genuine Chromium browser execution at 1920x1080. Customer Ahmed Mansour submitted a card request from `GET /public/cards` products; the request was persisted to the PostgreSQL dev database (`card_requests`), reviewed by Operations Officer Sarah El-Sayed, transitioned to `MORE_INFO_REQUIRED` with documented compliance instructions, reopened under review, and approved (`APPROVED_SIMULATED`).
2. **Discrepancies Fully Reconciled:** 
   - Probed live database for `GET /policies` as operations officer: confirmed real codes are `POL-DIGITAL-001`, `POL-RETAIL-001`, and `POL-KYC-001` (explaining that earlier mentions of `POL-AML-002` and `POL-OPS-003` were speculative design notes not present in the seed).
   - Reconciled complaints count: Dev DB has 21 total (2 demo complaints + 19 integration test complaints). The Employee Portal header badge displays 20 because resolved tickets (`CMP-2026-0102`) are filtered out (`status !== "RESOLVED"`).
   - Reconciled audit logs count: 282 (Step 1) ➔ 286 (Step 2) ➔ 299 (Phase 3) ➔ 300 (Phase 3b pre-browser) ➔ 306 (Phase 3b post-browser).
3. **Database Management & Backup Audit:**
   - Table creation: `account_opening_requests` and `card_requests` tables were created using SQLAlchemy metadata (`Base.metadata.create_all()` in `init_db()`).
   - Alembic status: `backend/alembic/` infrastructure exists with `alembic.ini` and `env.py`, but `versions/` is empty. Schema management currently relies on SQLAlchemy metadata creation.
   - Pre-execution backup: Verified `data/backups/nileops_dev_backup.sql` (93,900 bytes).
   - Fresh Phase 3b backup: Taken via `pg_dump` to `data/backups/nileops_dev_phase3b_backup.sql` (**114,140 bytes**, LastWriteTime: 11/8/2026 8:02:41 AM).
   - Failed command explanation: The initial `FATAL: password authentication failed` error occurred because the web UI demo password was mistakenly passed instead of the PostgreSQL application credentials from `.env`.
4. **Roles Specification for Review & Approval:**
   - Submitter: `customer` only (`require_customer` dependency).
   - Reviewer roles: `["operations_officer", "branch_manager", "compliance_reviewer", "admin"]`. Submitter cannot self-review (`403 Forbidden`).
   - Roles flagged for user approval; no permission alterations made.
5. **DRAFT State Removal & UI Enhancements:**
   - `DRAFT` state cleanly removed from claimed lifecycles; request progression starts strictly at `SUBMITTED`.
   - Customer and Employee workstations display `MORE_INFO_REQUIRED` and `REJECTED` states with full reviewer notes visible.
   - Timezones cleanly segregated: Customer Portal displays `EET (UTC+2)`; Employee Portal displays `UTC`.
   - Product and customer names resolved dynamically (e.g. "Nile Titanium Mastercard Debit Card" and "Ahmed Mansour" instead of raw database UUIDs).

---

## 2. Card Request End-to-End Implementation

### 2.1 Backend State Machine & API Endpoints

The card request system enforces dual-control governance and deterministic state machine transitions:

```
[SUBMITTED]
   │
   ├──> [UNDER_REVIEW]
   │       │
   │       ├──> [MORE_INFO_REQUIRED] ──> [UNDER_REVIEW] / [REJECTED]
   │       ├──> [REJECTED] (Terminal)
   │       └──> [APPROVED_SIMULATED] ──> [SIMULATED_COMPLETED] (Terminal)
   │
   ├──> [MORE_INFO_REQUIRED]
   ├──> [REJECTED]
   └──> [APPROVED_SIMULATED]
```

- **Endpoints:**
  - `POST /api/v1/customer/card-requests`: Creates a new card issuance request. Enforces idempotency via `idempotency_key` and restricts submission strictly to role `customer`.
  - `GET /api/v1/customer/card-requests`: Fetches the authenticated customer's card requests, serializing resolved card names from `GET /public/cards`.
  - `GET /api/v1/employee/card-requests`: Lists all card requests for employee review with customer names and card product names.
  - `PATCH /api/v1/employee/card-requests/{request_id}/review`: Enforces reviewer roles, blocks self-review (403), validates state machine transitions (409), and logs immutable audit trails.

### 2.2 Automated Backend API Tests

Added comprehensive test suites to `backend/tests/test_simulated_requests.py`:
- `test_card_request_state_machine_more_info_and_rejection`: Validates the full transition path `SUBMITTED` ➔ `MORE_INFO_REQUIRED` ➔ `UNDER_REVIEW` ➔ `APPROVED_SIMULATED` ➔ `SIMULATED_COMPLETED`, plus rejection paths and terminal state locks.
- `test_card_request_rbac_and_self_review_block`: Proves that customers cannot review card requests (403), that submitters cannot approve their own requests (four-eyes principle enforcement), and that duplicate idempotency keys return existing records without re-creation.

---

## 3. Discrepancy Probe & Reconciliation

### 3.1 Live Raw JSON of `GET /policies` as Operations Officer

Query executed against `http://127.0.0.1:8000/api/v1/policies/` using token for `ops@nileops.demo` (`Sarah El-Sayed`):

```json
[
  {
    "id": "pol-seed-03",
    "code": "POL-DIGITAL-001",
    "title_en": "InstaPay & Fast Transfer Daily Limits",
    "title_ar": "حدود المعاملات اللحظية عبر إنستاباي والتحويلات السريعة",
    "domain": "DIGITAL_BANKING",
    "version": 1,
    "status": "PENDING_APPROVAL",
    "is_current": true,
    "created_by_id": "usr-emp-01",
    "created_at": "2026-11-08T02:00:00Z"
  },
  {
    "id": "pol-seed-01",
    "code": "POL-RETAIL-001",
    "title_en": "Retail Deposit Accounts Opening & Minimum Balance Guidelines",
    "title_ar": "إرشادات فتح الحسابات والودائع للأفراد والحد الأدنى للرصيد",
    "domain": "RETAIL_BANKING",
    "version": 1,
    "status": "INDEXED",
    "is_current": true,
    "created_by_id": "usr-emp-01",
    "created_at": "2026-11-08T00:00:00Z"
  },
  {
    "id": "pol-seed-02",
    "code": "POL-KYC-001",
    "title_en": "Customer Due Diligence & Synthetic Egyptian National ID Standards",
    "title_ar": "معايير العناية الواجبة وتدقيق وثائق الرقم القومي التقديرية",
    "domain": "COMPLIANCE",
    "version": 1,
    "status": "APPROVED",
    "is_current": true,
    "created_by_id": "usr-emp-02",
    "created_at": "2026-11-08T01:00:00Z"
  }
]
```

**Reconciliation of Code Names:**
In earlier planning notes, hypothetical codes `POL-AML-002` and `POL-OPS-003` were discussed. Inspection of the database seed (`app/db/init_db.py`) proves the actual seeded codes are `POL-RETAIL-001`, `POL-KYC-001`, and `POL-DIGITAL-001`. The previous report has been corrected accordingly.

### 3.2 Complaint Count Reconciliation

- Total rows in `complaints` table: **21**
- Breakdown:
  - 2 demo baseline complaints:
    1. `CMP-2026-0101`: "Delay in synthetic instant transfer crediting" (`IN_PROGRESS`)
    2. `CMP-2026-0102`: "ATM synthetic cash deposit reversal request" (`RESOLVED`)
  - 19 integration test complaints: Created during regression test execution.
- **Why the Employee Portal badge shows 20:**
  In `EmployeePortal.tsx`, the tab count is computed as:
  ```typescript
  complaints.filter(c => c.status !== "RESOLVED").length
  ```
  Since `CMP-2026-0102` is in `RESOLVED` status, it is excluded from the active backlog badge (21 total - 1 resolved = 20 active complaints).

### 3.3 Audit Trail Row Count Reconciliation

| Milestone | `audit_logs` Count | Details |
| :--- | :---: | :--- |
| **Phase 0 Step 1** | 282 | Baseline DB verification |
| **Phase 0 Step 2** | 286 | +4 from manual verification logins & policy checks |
| **Phase 3** | 299 | +13 from account opening submission and evaluation rules |
| **Phase 3b Pre-Browser** | 300 | +1 baseline login check |
| **Phase 3b Post-Browser** | 306 | +6 from: Customer Login, Card Request Submit, Employee Login, Request More Info, Resume Review, Simulated Approval |

---

## 4. Database Management & Backup Audit

### 4.1 Table Creation & Alembic Migration Status

- **Method of Creation:** The tables `account_opening_requests` and `card_requests` were created in the PostgreSQL dev database (`nileops`) via SQLAlchemy asynchronous metadata reflection (`Base.metadata.create_all()` in `app.db.init_db.init_db()`).
- **Alembic Status:** The repository contains an `alembic.ini` file and an `alembic/env.py` configuration; however, the `alembic/versions/` directory contains no migration script files (`.gitkeep` only). Schema evolution is currently maintained declaratively through SQLAlchemy ORM models.
- **Pre-execution Backup:** Verified existing backup at `data/backups/nileops_dev_backup.sql` (93,900 bytes).
- **Fresh Phase 3b Backup Taken:** Executed `pg_dump` targeting the dev database:
  - **File:** `C:\AI\NileOps_V4\data\backups\nileops_dev_phase3b_backup.sql`
  - **Size:** **114,140 bytes**
  - **Timestamp:** 2026-11-08 08:02:41 AM (verified via filesystem attributes)
- **Explanation of Earlier Failed Command:**
  When executing `pg_dump`, the web application demo password (`NileOps2026!`) was mistakenly passed in the terminal command. PostgreSQL rejected the connection (`FATAL: password authentication failed for user "nileops_app"`). Upon extracting the correct database password configured in `backend/.env` for `nileops_app`, the backup completed with exit code 0.

---

## 5. Roles & Dual-Control Specification (Flagged for User Approval)

The following role matrix is implemented in code and submitted for formal user sign-off:

| Action | Allowed Roles | Enforced Restriction |
| :--- | :--- | :--- |
| **Submit Account Opening Request** | `customer` | Customers may only submit requests for their own customer ID. |
| **Submit Card Issuance Request** | `customer` | Customers may only submit requests linked to their own accounts. |
| **View Customer Requests** | `customer` | Scoped strictly to `customer_id == current_user.id`. |
| **Review / Adjudicate Requests** | `operations_officer`, `branch_manager`, `compliance_reviewer`, `admin` | Dual-control: Submitter cannot self-review (`user.id !== request.submitted_by_id`). Returns `403 Forbidden` if violated. |

*Note: In accordance with project instructions, no role permissions have been altered without explicit user instruction.*

---

## 6. Real Browser Evidence (1920x1080 Headless Chromium)

All screenshots were captured from live Chromium sessions running against native backend and frontend processes, saved to both `docs/screenshots/` and artifact directories, and visually verified via direct inspection:

### 6.1 `phase3b_card_submit.png`
- **Visual Elements:** Customer Ahmed Mansour in the Customer Portal after submitting a card issuance application.
- **Key Details:** Warning banner ("SIMULATED DIGITAL BANKING PLATFORM / SIMULATION"), "My Requests (2)" tab active, Account Requests (1) and Card Requests (1) visible. Card request `REQ-CRD-06A6E643` displayed in `SUBMITTED` state with Card Name "Nile Titanium Mastercard Debit Card", Embossed Name "AHMED MANSOUR", and timestamp `08/11/2026 08:18:52 EET (UTC+2)`. Lifecycle progression step "1 Submitted" is highlighted.

### 6.2 `phase3b_customer_card_timeline.png`
- **Visual Elements:** Full viewport showing Customer Ahmed Mansour's "My Requests & Lifecycle Timeline" view.
- **Key Details:** Segregated display of both Account Opening and Card Issuance requests. Card request shows clean horizontal lifecycle stepper, branch "CAI-01", account reference "acc-001...", and timestamp formatted with explicit local timezone (`EET (UTC+2)`).

### 6.3 `phase3b_employee_card_review.png`
- **Visual Elements:** Operations Workspace for `Sarah El-Sayed` (`OPERATIONS_OFFICER`).
- **Key Details:** Requests Queue tab active (badge count 2). Sub-tab "Card Issuance Requests (1)" selected. Left queue shows `REQ-CRD-06A6E643 SUBMITTED` with UTC timestamp (`2026-11-08 06:18:52 UTC`). Right review panel displays resolved applicant customer name "Ahmed Mansour" (`usr-cust-01`), resolved product name "Nile Titanium Mastercard Debit Card" (`DEBIT_MASTERCARD_TITANIUM`), embossed name, linked account, delivery branch, idempotency key, and action toolbar: "Approve (Simulated)", "Request More Info", and "Reject (with Reason)".

### 6.4 `phase3b_employee_card_more_info.png`
- **Visual Elements:** Operations Workspace after Sarah El-Sayed executes the "Request More Info" action.
- **Key Details:** Status badge updated to purple `MORE_INFO_REQUIRED`. Left queue item badge updated to `MORE_INFO_REQUIRED`. Dedicated purple alert box appears: *"Information Required From Customer: Please confirm preferred branch and submit proof of updated residential address."* Action button dynamically updates to blue "Resume Review (Under Review)" button.

### 6.5 `phase3b_arabic_card_workspace.png`
- **Visual Elements:** Full Arabic RTL layout of the Operations Workspace.
- **Key Details:** Right-to-left layout direction. Navbar reads "بنك النيل التجريبي (محاكاة العمليات المصرفية الرقمية)". Workspace header reads "مساحة عمل العمليات — Sarah El-Sayed". Subtabs read "طلبات فتح الحسابات (1)" and "طلبات إصدار البطاقات (1)". Filter chips rendered in Arabic ("الكل", "تم التقديم", "قيد المراجعة", "معتمد محاكاة", "استيفاء بيانات", "مرفوض", "مكتمل محاكاة"). Green badge "معتمد محاكاة" rendered alongside Arabic card name, Arabic field labels, and "إتمام وتأكيد الإصدار" ("Complete Simulation") button.

---

## 7. Database Integrity & Dev DB Row Counts

Direct inspection of all dev database tables proves that zero records were deleted throughout Phase 3b:

```
users: 7
accounts: 4
transactions: 4
complaints: 21
policy_documents: 21
kyc_verifications: 3
audit_logs: 306
account_opening_requests: 1
card_requests: 1
```

- Total baseline tables (`users`, `accounts`, `transactions`, `complaints`, `policy_documents`, `kyc_verifications`): Exactly unchanged.
- `account_opening_requests`: 1 (from Phase 3).
- `card_requests`: 1 (persisted from browser UI execution in Phase 3b).
- `audit_logs`: 306 (clean audit trail recording all user and employee actions).

---

## 8. Verification & Test Evidence

### 8.1 Backend Regression Suite (`nileops_test`)

```
============================== test session starts ==============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\AI\NileOps_V4\backend
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.3
asyncio: mode=Mode.AUTO
collected 66 items

..................................................................       [100%]

============================== warnings summary ===============================
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 66 passed, 5 warnings in 43.92s ========================
```

- **Database:** Executed exclusively against isolated `nileops_test`.
- **Count:** 66 passed, 0 failed, 0 skipped.

### 8.2 Frontend Production Build

```
> nileops-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 38 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.56 kB │ gzip:  0.37 kB
dist/assets/index-6pGz6LGM.css   33.07 kB │ gzip:  6.11 kB
dist/assets/index-Crqy6dkc.js   285.76 kB │ gzip: 77.66 kB
✓ built in 847ms
```

---

## 9. Conclusion

Phase 3b has satisfied all acceptance criteria:
- Card requests are fully operational end-to-end with persistent database storage.
- Four-eyes governance, self-review blocks, and RBAC are validated via automated tests and UI execution.
- Discrepancies in complaint and policy counts are completely explained and reconciled.
- Full backup evidence and database safety are preserved with zero deletions and no git commits/pushes.
