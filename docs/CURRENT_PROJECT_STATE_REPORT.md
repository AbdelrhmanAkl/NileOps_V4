# NileOps Demo Bank — Current Project State Report

**Generated:** 2026-11-09  
**Platform Version:** NileOps V4  
**Target Architecture:** Fictional Digital Banking Operations Platform MVP  
**Host Environment:** Windows 10/11 x64 Native Runtime (PostgreSQL 16, Python 3.11, React 18, Vite, Tailwind CSS)

---

## 1. Feature Implementation & Verification Matrix

| Domain | Feature / Capability | Implementation Status | API Tested | Browser Tested | Verification Notes |
|---|---|:---:|:---:|:---:|---|
| **Auth & Security** | JWT Authentication & RBAC | `IMPLEMENTED` | `YES` | `YES` | Dual portal (Customer / Employee) with 5 distinct employee roles. Insecure JWT secret guard enforced in production mode outside tests. |
| **Auth & Security** | 1-Click Demo Login Personas | `IMPLEMENTED` | `YES` | `YES` | Pre-configured buttons for retail customer, operations officer, customer service, compliance, branch manager, and admin. |
| **Retail Banking** | Multi-Account Portfolio View | `IMPLEMENTED` | `YES` | `YES` | Displays Current, Savings, and Certificate of Deposit balances with masked IBANs. |
| **Retail Banking** | Transaction History & Details | `IMPLEMENTED` | `YES` | `YES` | Categorized debits/credits with counterparty labels and formatted EGP currency. |
| **Retail Banking** | CD Yield Calculator | `IMPLEMENTED` | `YES` | `YES` | Real-time annual and monthly interest payout estimation. |
| **Account Requests** | Simulated Account Application | `IMPLEMENTED` | `YES` | `YES` | Form submission with initial deposit, employment status, branch, and compliance disclosure. |
| **Card Requests** | Simulated Card Issuance | `IMPLEMENTED` | `YES` | `YES` | Account linking, card type selection, and customer tracking timeline. |
| **Dual Control** | Four-Eyes Request Review | `IMPLEMENTED` | `YES` | `YES` | Separate review and approval actions preventing self-approval; strict state machine transitions. |
| **Rules Engine** | Account & Card Eligibility Rules | `IMPLEMENTED` | `YES` | `YES` | Deterministic verification of synthetic KYC on file, minimum deposit thresholds, and income requirements. |
| **Complaints** | Customer Ticket Submission | `IMPLEMENTED` | `YES` | `YES` | Customer ticket creation with transaction reference association and category selection. |
| **Complaints** | Dynamic SLA Engine | `IMPLEMENTED` | `YES` | `YES` | Elapsed vs. remaining hours computation against priority targets (CRITICAL=4h, HIGH=12h, MEDIUM=24h, LOW=48h). |
| **Complaints** | Advisory Routing & Triage | `IMPLEMENTED` | `YES` | `YES` | Keyword and rule-based assignment recommendations to specialized operational teams. |
| **Complaints** | AI Draft Responses & Human Review | `IMPLEMENTED` | `YES` | `YES` | Pre-populated templated replies with mandatory employee review confirmation checkbox before dispatch. |
| **Complaints** | Test Ticket Segregation | `IMPLEMENTED` | `YES` | `YES` | `is_test=True` isolation: 19 test complaints excluded from customer view; employee view provides toggle. |
| **Document AI** | Synthetic Egyptian ID OCR | `IMPLEMENTED` | `YES` | `YES` | 14-digit National ID extraction, governorate decoding, birthdate calculation, and century rule checks. |
| **Document AI** | Compliance Invariant Enforcement | `IMPLEMENTED` | `YES` | `YES` | Permanent invariant `identity_verification_status = NOT_VERIFIED` maintained across all records and endpoints. |
| **Knowledge Base** | Policy Document Governance | `IMPLEMENTED` | `YES` | `YES` | Four-eyes authoring and approval workflow for internal operating policies. |
| **RAG Assistant** | Semantic Vector Search (Qdrant) | `IMPLEMENTED` | `YES` | `YES` | Document chunking, Cosine similarity search, and similarity threshold gating (0.15). |
| **RAG Assistant** | Retrieval Guard & RBAC Filtering | `IMPLEMENTED` | `YES` | `YES` | Inactive `POL-TEST-*` exclusion; customer portal blocked from employee-only operational policies. |
| **RAG Assistant** | Extractive Fallback Engine | `IMPLEMENTED` | `YES` | `YES` | Circuit-breaker regex extraction fallback when local LLM (Ollama) times out or is unreachable. |
| **Audit & Governance**| Immutable Audit Logging | `IMPLEMENTED` | `YES` | `YES` | Append-only audit table logging actor, action, timestamp (UTC), IP, and state delta JSON. RBAC restricted. |
| **Internationalization**| English & Arabic (LTR / RTL) | `IMPLEMENTED` | `YES` | `YES` | Full bidirectional support across both customer and employee portals with Cairo typography. |

---

## 2. Test Suite Execution & Coverage

### 2.1 Backend Pytest Results
Test suite executed in complete isolation using dedicated databases (`nileops_test` in PostgreSQL and `nileops_kb_test` in Qdrant):

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.5.0
rootdir: c:\AI\NileOps_V4\backend
configfile: pyproject.toml
plugins: anyio-4.8.0, asyncio-0.24.0
asyncio: mode=Mode.AUTO
collected 77 items

backend/tests/test_audit_rbac.py ........                                [ 10%]
backend/tests/test_complaints_phase4.py ...............                  [ 29%]
backend/tests/test_dual_control_requests.py ................             [ 50%]
backend/tests/test_health.py ......                                      [ 58%]
backend/tests/test_kyc_governance.py ..........                          [ 71%]
backend/tests/test_ocr_security.py ...                                   [ 75%]
backend/tests/test_policy_rag.py ..................                      [ 98%]
backend/tests/test_rag_security.py .                                     [100%]

======================== 77 passed, 4 warnings in 34.14s =======================
```

- **Total Test Cases:** 77
- **Passed:** 77 (100%)
- **Failed:** 0
- **Execution Time:** 34.14 seconds
- **Database Safety Guard:** Hard-coded assertions reject execution unless target database names end with `_test`.

### 2.2 Frontend Build & TypeScript Verification
- **TypeScript Static Analysis:** `npx.cmd tsc --noEmit` completed with **0 errors**.
- **Production Asset Bundle:** Verified in `frontend/dist/` (`index.html`, JavaScript chunks, CSS stylesheets).

---

## 3. Development Database State (Zero Deletions)

Row counts verified directly from PostgreSQL 16 `nileops` production-seed database:

| Table Name | Row Count | Invariant / Status |
|---|:---:|---|
| `users` | 7 | 1 customer, 5 staff personas, 1 admin |
| `accounts` | 4 | Current, High-Yield Savings, 3-Year CD, Secondary Current |
| `transactions` | 4 | Real-time synthetic salary, utility, and ATM entries |
| `complaints` | 21 | 2 production customer tickets (`is_test=False`), 19 test tickets (`is_test=True`) |
| `policy_documents` | 21 | Operational banking policies governing retail, KYC, and disputes |
| `kyc_verifications` | 3 | All strictly marked `NOT_VERIFIED` |
| `audit_logs` | 343 | Immutable append-only log entries (0 deletions, 0 overwrites) |
| `account_opening_requests` | 1 | Seed request `REQ-ACC-B68ACF82` |
| `card_requests` | 1 | Seed request `REQ-CRD-06A6E643` |

---

## 4. Transparent Architectural Limitations & Known Defects

In accordance with strict project transparency guidelines, the following limitations are documented:

### 4.1 Feature Hashing Embeddings vs Paraphrase Recall
- **Embedding Implementation:** The current vector index uses token feature hashing with unigram/bigram projection into a fixed 384-dimensional vector space (`cosine` distance). It does not use a deep neural transformer model (e.g. `sentence-transformers/all-MiniLM-L6-v2` or `multilingual-e5`).
- **Empirical Measurement:**
  - Lexical / exact question match: **Hit@1 = 92.5%**, **Hit@3 = 97.5%**, **MRR = 0.950**.
  - Paraphrased questions (Arabic Egyptian colloquial & English rephrasing): **Hit@1 = 60.0%** at threshold 0.15.
  - Sweeping threshold to 0.20 causes Paraphrase Hit@1 to drop to **33.3%** (abstaining on 10 out of 15 valid in-domain questions).
- **Recommendation:** Keep retrieval similarity threshold at `0.15`. Upgrading to neural embeddings requires installing PyTorch or ONNX Runtime with approved code signing.

### 4.2 Extractive LLM Fallback (Circuit-Breaker Mode)
- **Local LLM Availability:** When the local Ollama daemon times out (>10.0s) or is not running, the system transparently engages the deterministic extractive fallback engine.
- **Answer Faithfulness:** Under extractive fallback, answers are verbatim excerpts extracted directly from the highest-scoring cited policy chunk.
- **Metrics Interpretation:** The measured **0% hallucination rate** reflects exact extractive citations rather than generative natural language synthesis.

### 4.3 Synthetic Egyptian National ID OCR vs. Handbook Target
- **Handbook Target:** Field F1 score $\ge 90.0\%$.
- **Measured Empirical Results (Synthetic Cards Only):**
  - **National ID (14 digits):** Exact Match: **87.5%**, CER: **0.016**, Field F1: **87.5%** *(Target Not Met)*.
  - **Full Name (Arabic):** Exact Match: **62.5%**, CER: **0.098**, Field F1: **62.5%** *(Target Not Met)*.
  - **Address (Arabic):** Exact Match: **50.0%**, CER: **0.141**, Field F1: **50.0%** *(Target Not Met)*.
  - **Factory Code:** Exact Match: **70.0%**, CER: **0.052**, Field F1: **70.0%** *(Target Not Met)*.
  - **Human Review Routing:** **70.0%** of synthetic cards correctly triggered human review fallback.
- **Root Cause:** Degradation is driven by rotation ($\pm 10^\circ$), Gaussian blur, low lighting, and Arabic font ligature variations where character boundaries merge.
- **Rule Enforcement:** All extractions remain `NOT_VERIFIED` pending human review.

### 4.4 Database Schema Migrations
- **Current Approach:** Schema synchronization relies on SQLAlchemy `create_all()`.
- **Limitation:** Alembic migration scripts (`alembic upgrade head`) are not configured. Schema evolutions require explicit table alteration scripts.

### 4.5 Simulation Boundaries
- **Fictional Platform:** NileOps is strictly an operational simulation. No real Egyptian banking APIs, central bank networks, InstaPay rails, or real National ID databases are queried. All identity cards, accounts, and payments are synthetic.

### 4.6 Host Windows Application Control Policy
- **Host Restrictions:** Following the host machine reboot, Windows Defender Application Control (WDAC) enforced code signing policies restricting unsigned native extensions (`qdrant.exe`, Rollup native `.node`, Cython `.pyd`).
- **Resilience Strategy:** The platform operates using a pure-Python REST service for Qdrant vector operations on port 6333, a pure-Node.js static server on port 5173, and pure-Python fallbacks in SQLAlchemy and OCR.

---

## 5. Scope Boundaries: What Was NOT Done

The following items were explicitly excluded from the MVP scope:
1. **CI/CD Automation:** No GitHub Actions or GitLab CI pipelines were configured.
2. **Containerization:** Dockerfile and Docker Compose configurations were not created; native Windows runtime is utilized.
3. **API Rate Limiting:** Dynamic rate-limiting middleware (such as `slowapi` or Redis token buckets) was not implemented.
4. **Neural Transformer Embeddings:** Deep neural embedding model weights were not integrated into the production path.
5. **Public Cloud Deployment:** Production deployment to AWS, Azure, or GCP was explicitly out of the Handbook MVP scope.

---

## 6. Secret & Security Audit Report

A repository-wide scan was conducted to ensure no production secrets, credentials, or customer PII are tracked in Git.

- **`.env.example` Check:** Confirmed to contain only generic placeholder values (`nileops_user`, `localhost`, `secret_key_here`).
- **`.gitignore` Coverage:** Explicitly ignores:
  - `data/` (synthetic cards, uploads, eval sets)
  - `scratch/` (temporary scripts, runtime mocks)
  - `tests/ocr/fixtures/` (real ID fixtures strictly excluded from Git and testing)
  - `*.pyc`, `__pycache__/`, `.venv/`, `node_modules/`, `frontend/dist/`
- **Tracked Files with Synthetic Test Passwords (Catalogued without printing secret values):**
  - `backend/app/api/v1/auth.py` (synthetic test password hashes for demo personas)
  - `backend/tests/test_audit_rbac.py` (synthetic mock credentials for unit test execution)
  - `backend/tests/test_complaints_phase4.py` (synthetic mock credentials for unit test execution)
  - `backend/tests/test_dual_control_requests.py` (synthetic mock credentials for unit test execution)
  - `backend/tests/test_kyc_governance.py` (synthetic mock credentials for unit test execution)
  - `backend/tests/test_policy_rag.py` (synthetic mock credentials for unit test execution)
  - `backend/tests/test_rag_security.py` (synthetic mock credentials for unit test execution)
  - No production credentials, live private keys, or authentic customer PII exist anywhere in the repository.

