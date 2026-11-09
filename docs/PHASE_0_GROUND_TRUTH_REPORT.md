# NileOps V4 — Phase 0 Step 0: Ground Truth Report

**Date & Time:** 2026-11-08 05:35:00 UTC  
**Inspection Mode:** Strictly READ-ONLY (No code, database, or configuration mutations)  
**Lead Auditor:** Senior Banking Solutions Architect & QA Lead

---

## 1. Executive Summary

This ground-truth audit was conducted to resolve critical discrepancies between historical project documentation and the actual runtime behavior of NileOps V4. Prior reports made conflicting assertions regarding the backend database engine (PostgreSQL 16 vs. SQLite 3), reported baseline test counts without database isolation verification, and failed to account for severe data pollution in the complaints and policy queues.

### Key Audit Conclusions:
1. **Database Identity Resolved:** The active, running backend is connected to **PostgreSQL 16.15**, not SQLite. The `SQLite 3` label in the frontend footer was an unmaintained hardcoded string in `frontend/src/App.tsx`.
2. **Baseline Testing Blocked:** Pytest fixtures in `backend/tests/conftest.py` directly instantiate `app.main:app` with the production/development database URL, lacking test database isolation. Running the test suite against the active development database would cause further data pollution and violates audit safety rules; baseline tests are truthfully marked **BLOCKED**.
3. **Data Pollution Root Cause Identified:** The 21 total complaints and 21 policy records in the database stem from `backend/tests/test_mvp.py` executing test mutations against the shared development database without a separate test schema or rollback fixtures.
4. **IBAN Exposure Leak Confirmed:** While account cards truncate IBANs in the UI, the backend endpoint `/api/v1/customer/accounts` returns full unmasked account numbers, and the Transaction Statement header in `CustomerPortal.tsx` renders full unmasked IBANs (`EG98000100010000000012345678`).
5. **No Modifications Made:** Zero code, configuration, or database mutations occurred during this step.

---

## 2. Actual Database Identity & Connection Configuration

### Effective Masked Connection URL
- **Configured Variable:** `DATABASE_URL` in `backend/.env`
- **Masked URL:** `postgresql+asyncpg://nileops_app:***@127.0.0.1:5432/nileops`
- **Dialect:** `postgresql` (Driver: `asyncpg`)
- **Backend Service Config (`backend/app/core/config.py`):** Loads from `.env` via Pydantic `BaseSettings`. Fallback default is `sqlite+aiosqlite:///./nileops_mvp.db` if `DATABASE_URL` is unset, but the active process loads the PostgreSQL URL.

### Live Database Query Evidence
Executed directly through SQLAlchemy AsyncEngine bound to the active backend configuration:
```sql
SELECT version();
```
**Actual Query Output:**
```text
PostgreSQL 16.15, compiled by Visual C++ build 1944, 64-bit
```

---

## 3. Baseline Test Suite Status

### Status: <badge color="danger">BLOCKED</badge>

### Truthful Explanation:
- Inspection of `backend/tests/conftest.py`:
  ```python
  from starlette.testclient import TestClient
  from app.main import app

  @pytest.fixture(scope="session")
  def client() -> TestClient:
      return TestClient(app)
  ```
- **Finding:** The test harness directly uses the application engine pointing to `DATABASE_URL` in `backend/.env`.
- **Destructive Mutation Proof:** `test_mvp.py` lines 86–114 submit live complaints via `client.post("/api/v1/customer/complaints")`, and lines 118–164 create and approve live policies with unique codes (`POL-TEST-*`) that persist in PostgreSQL.
- **Safety Rule Enforced:** Under Section 5 (Phase 0 Step 0): *"If test isolation is not possible: Do not run the suite against the development database. Mark baseline tests BLOCKED. Explain what prevents isolation."*
- Running the test suite would further pollute customer demo records; execution is strictly held until Step 1 establishes a genuine test database or transaction rollback fixture.

---

## 4. Service Health & Runtime Verification

All four local daemons were probed live:

| Subsystem | Configured Local URI | Live HTTP / Network Response | Operational State | In Active Use by Backend/Frontend |
| :--- | :--- | :--- | :---: | :---: |
| **PostgreSQL 16** | `127.0.0.1:5432` | TCP Established, `SELECT version()` passed | **HEALTHY** | **YES** (Primary persistence engine) |
| **Qdrant Vector DB** | `http://127.0.0.1:6333` | `GET /collections` $\to$ `200 OK`<br>`{"collections":[{"name":"nileops_kb"}]}` | **HEALTHY** | **YES** (Vector index for policy RAG) |
| **FastAPI Backend** | `http://127.0.0.1:8000` | `GET /health` $\to$ `200 OK`<br>`{"status":"healthy","database":"PostgreSQL 16"}` | **HEALTHY** | **YES** (Serving API v1) |
| **Vite Dev Server** | `http://127.0.0.1:5173` | `GET /` $\to$ `200 OK` (HMR active, Tailwind CSS v3) | **HEALTHY** | **YES** (Serving React 18 SPA) |

---

## 5. Git Repository State

- **Current Branch:** `master`
- **Configured Remotes:**  
  `origin  https://github.com/AbdelrhmanAkl/NileOps_V4.git (fetch)`  
  `origin  https://github.com/AbdelrhmanAkl/NileOps_V4.git (push)`
- **Working Tree State:** Dirty (Existing uncommitted work from previous phases).
- **Unstaged Modified Files (9 files):**
  - `.gitignore`
  - `backend/app/api/v1/ocr.py`
  - `backend/app/core/config.py`
  - `backend/app/main.py`
  - `backend/requirements.txt`
  - `docs/GITHUB_RELEASE_REPORT.md`
  - `frontend/src/api/client.ts`
  - `frontend/src/main.tsx`
  - `frontend/vite.config.ts`
- **Untracked Files:**
  - `backend/app/scripts/capture_10_screenshots.py`
  - `backend/app/scripts/evaluate_rag_quality.py`
  - `backend/app/scripts/rag_eval_results.json`
  - `backend/app/scripts/run_full_integration_test.py`
  - `backend/app/scripts/run_image_ocr_batch.py`
  - `backend/app/scripts/run_pilot_eval_15.py`
  - `backend/app/scripts/run_preprocessing_ablation.py`
  - `backend/app/scripts/test_ocr_deep.py`
  - `backend/app/scripts/test_rag_deep.py`
  - `backend/app/services/image_pipeline.py`
  - `backend/tests/test_ocr_phase_2_1.py`
  - `backend/tests/test_ocr_phase_2_2.py`
  - `backend/tests/test_ocr_security.py`
  - `docs/FINAL_DEMO_READINESS_REPORT.md`
  - `docs/FULL_SYSTEM_TEST_REPORT.md`
  - `docs/ocr/`
  - `docs/screenshots/`
  - `frontend/.env.example`
  - `frontend/src/index.css`
  - `frontend/src/vite-env.d.ts`
- **Last 3 Commits on `master`:**
  - `d66730b` — *docs: add official GitHub release audit report*
  - `2ece794` — *release: complete NileOps banking operations platform MVP*
  - `e4e920c` — *feat(phase1): initial monorepo scaffolding, docker environment, and health check*
- **User Work Preservation:** All existing unstaged files are intact and uncommitted.

---

## 6. Data Pollution Investigation

Live database inspection was conducted via `SELECT` queries across `complaints` and `policy_documents`:

### A. Customer Complaints (21 Records Total)
- **Canonical Demo Records (2):**
  - `cmp-001` (`CMP-2026-0101`): Seeded at `20:45:51 UTC` for `usr-cust-01` (ATM debit without dispensing cash).
  - `cmp-002` (`CMP-2026-0102`): Seeded at `20:45:51 UTC` for `usr-cust-01` (Delayed InstaPay transfer).
- **Test-Polluted Records (19):**
  - 19 records with auto-generated UUIDs created between `20:47:00 UTC` and `01:24:07 UTC`.
  - All assigned to `usr-cust-01`.
  - Exactly 11 copies with subject `"Card captured by ATM machine at branch"`.
  - Exactly 8 copies with subject `"ATM Cash Retained Issue"`.
  - **Origin:** Direct invocations of `test_complaint_lifecycle` in `test_mvp.py` and `run_full_integration_test.py` running against the development database.

### B. Policy Knowledge Base (21 Records Total)
- **Canonical Demo Policies (3):**
  - `pol-001` (`POL-RETAIL-001`): Retail Deposit Accounts Opening (`INDEXED`).
  - `pol-002` (`POL-KYC-001`): Customer Due Diligence (`APPROVED`).
  - `pol-003` (`POL-DIGITAL-001`): InstaPay Daily Limits (`PENDING_APPROVAL`).
- **Test-Polluted Policies (18):**
  - 18 records with codes matching pattern `POL-TEST-*` created between `20:47:00 UTC` and `01:24:07 UTC`.
  - Examples: `POL-TEST-001`, `POL-TEST-38C190`, `POL-TEST-B1852B`, `POL-TEST-10043C`.
  - **Origin:** Generated by `test_policy_four_eyes_approval` in `test_mvp.py` (`unique_code = f"POL-TEST-{uuid.uuid4().hex[:6].upper()}"`).

---

## 7. IBAN & PII Masking Audit

- **Customer Accounts API (`GET /api/v1/customer/accounts`):**
  - Schema: `AccountOut` in `backend/app/schemas/banking.py` defines `account_number: str`.
  - **Vulnerability:** Serializes raw unmasked account numbers (e.g., `EG98000100010000000012345678`) over HTTP.
- **Frontend Account Cards:**
  - `frontend/src/portals/customer/CustomerPortal.tsx` line 185 applies partial frontend masking:  
    `{acc.account_number.slice(0, 10)}...{acc.account_number.slice(-4)}`
- **Frontend Transaction Statement Header:**
  - `CustomerPortal.tsx` line 209:
    ```tsx
    Showing records for account: {selectedAccount.account_number}
    ```
  - **Defect:** Prints the complete, unmasked 28-character synthetic IBAN directly on screen.
- **Remediation Required:**
  - Enforce masking in backend serialization schemas.
  - Apply uniform masking utilities across all frontend headers and detail views.

---

## 8. Verified UI Defects Summary

| Defect # | Component / File | Current Defect Description | Root Cause Identified |
| :-: | :--- | :--- | :--- |
| **D-01** | `frontend/src/App.tsx#L54` | Footer displays `SQLite 3` | Hardcoded string literal; does not reflect backend PostgreSQL configuration. |
| **D-02** | `CustomerPortal.tsx#L209` | Transaction statement header displays full IBAN | Missing mask formatter on selected account subtitle. |
| **D-03** | `CustomerPortal.tsx#L408` | Complaint modal header has layout clipping in RTL | Conflicting absolute positioning classes (`rtl:left-4 rtl:right-auto`) on modal close button. |
| **D-04** | `backend/app/api/v1/auth.py#L195` | Transaction dates are identical | Seed script instantiated `Transaction(...)` without distinct `timestamp` values; all defaulted to `now`. |
| **D-05** | `EmployeePortal.tsx#L737` | Audit timestamps omit calendar date and timezone | Uses `toLocaleTimeString()` which outputs `HH:MM:SS` only. |
| **D-06** | `backend/app/api/v1/policies.py` | `POL-TEST-*` test policies pollute UI catalog | Public and employee policy endpoints lack a filter excluding test prefixes. |
| **D-07** | `EmployeePortal.tsx#L370` | Complaints table lacks customer, date, SLA, assignee | Frontend table template omits columns present in database model. |
| **D-08** | `EmployeePortal.tsx` | Complaints queue lacks pagination and search | Renders single unpaginated array without category or priority filters. |

---

## 9. Phase 0 Step 1 Implementation Plan

*To be executed only after explicit user approval:*

1. **Test Isolation Setup (`backend/tests/conftest.py`):**
   - Configure pytest to use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) or an isolated PostgreSQL test schema (`nileops_test`) specifically during test runs.
   - Override `get_db_session` in `app.dependency_overrides` so no test ever connects to the development database.
2. **Demo Data Hygiene & Safe Deduplication:**
   - Take a complete physical database dump of the `nileops` PostgreSQL database before any cleanup.
   - Clean up only the 19 test-generated complaints and 18 test-generated `POL-TEST-*` policies, retaining the canonical seeded demo records (`cmp-001`, `cmp-002`, `pol-001`, `pol-002`, `pol-003`).
3. **Database-Driven Footer:**
   - Update `frontend/src/App.tsx` and `Header.tsx` to display the actual runtime database name fetched from `/health` (`PostgreSQL 16`).
4. **End-to-End IBAN Masking:**
   - Add a masking property to `AccountOut` or frontend formatter to ensure IBANs always render as `EG98••••••••••••••••••••5678`.
5. **Distinct Transaction Timestamps in Seeder:**
   - Update `backend/app/api/v1/auth.py` so seed transactions have distinct dates corresponding to their reference dates (`2026-11-01`, `2026-11-03`, `2026-11-05`).
6. **Complete Audit Timestamps:**
   - Format audit log timestamps as `YYYY-MM-DD HH:MM:SS UTC`.

---

## 10. Risks & Open Questions

1. **Risk:** Test Isolation Dependency: If pytest runs with in-memory SQLite while the app runs on PostgreSQL, Postgres-specific SQL constructs could behave differently.
   - *Mitigation:* Ensure all models and queries adhere strictly to standard SQLAlchemy 2 async ORM syntax.
2. **Risk:** Data cleanup safety: Destructive deletion must never run without a prior verified backup.
   - *Mitigation:* Execute `pg_dump` to `C:\AI\NileOps_V4\data\backups\nileops_pre_cleanup.sql` before any DELETE query.

---

## 11. Confirmation of Zero Modifications

**Certified:** No project files, database records, environment variables, or Git states were created, edited, deleted, or committed during this Step 0 inspection.

---
*End of Report — Awaiting User Approval to Proceed to Phase 0 Step 1.*

