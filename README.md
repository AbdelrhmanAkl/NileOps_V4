# NileOps — Intelligent Digital Banking Operations Platform

[![Backend Tests](https://img.shields.io/badge/tests-119%20passed-brightgreen.svg)]()
[![Frontend Build](https://img.shields.io/badge/frontend-Vite%20%2B%20TypeScript-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.15-336791.svg)]()
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.12-red.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **Fictional Simulation Identity:** NileOps Demo Bank  
> **Simulation Disclaimer:** NileOps is an enterprise-pattern digital banking operations prototype. It is **not** a licensed financial institution, is not connected to Central Bank of Egypt (CBE) or Civil Status networks, and does **not** process real financial transactions or genuine citizen identification documents. All customer profiles, account balances, and National ID numbers are 100% synthetic.

---

## Table of Contents

- [1. Project Overview & Fictional Simulation](#1-project-overview--fictional-simulation)
- [2. System Architecture](#2-system-architecture)
- [3. Technology Stack](#3-technology-stack)
- [4. Dual-Portal Banking Experience](#4-dual-portal-banking-experience)
- [5. PostgreSQL 16 & Relational Persistence](#5-postgresql-16--relational-persistence)
- [6. Qdrant & Grounded RAG Architecture](#6-qdrant--grounded-rag-architecture)
- [7. Egyptian National ID 9D Intelligence (OCR)](#7-egyptian-national-id-9d-intelligence-ocr)
- [8. Installation Prerequisites](#8-installation-prerequisites)
- [9. Native Setup Guide](#9-native-setup-guide)
- [10. Environment Configuration](#10-environment-configuration)
- [11. Service Startup Instructions](#11-service-startup-instructions)
- [12. Running Automated Tests & Isolation](#12-running-automated-tests--isolation)
- [13. Demo Authentication & Seed Profiles](#13-demo-authentication--seed-profiles)
- [14. Transparent Architectural Limitations](#14-transparent-architectural-limitations)
- [15. User Interface & Screenshot Index](#15-user-interface--screenshot-index)
- [16. Technical Documentation & Reports](#16-technical-documentation--reports)
- [17. License](#17-license)

---

## 1. Project Overview & Fictional Simulation

**NileOps** is an intelligent, bilingual (Egyptian Arabic RTL & English LTR) digital banking operations simulation platform designed around Egyptian banking standards and regulatory patterns. 

The platform addresses core operational workflows in digital banking:
1. **Customer Self-Service:** Balance inquiries, account statement tracking, certificate of deposit yield calculators, policy assistant, customer complaint filing, account opening requests, and card requests.
2. **Operations & Compliance Workflow:** Four-eyes approval governance, complaint lifecycle operations with deterministic keyword-matched AI advisory routing, service level agreement (SLA) monitoring, and human-in-the-loop KYC inspection queues.
3. **Retrieval-Augmented Generation (RAG):** Grounded policy question answering powered by Qdrant vector retrieval with strict portal boundary isolation (customer vs. employee), dynamic vector sizing, and explicit out-of-domain abstention.
4. **Document Intelligence (OCR):** 9-dimensional deterministic validation of 14-digit Egyptian National ID structures, calendar math, governorate allowlists, review routing, and public PII masking invariants (`NOT_VERIFIED`).

---

## 2. System Architecture

```mermaid
graph TB
    subgraph ClientLayer ["Client Layer (Dual Portal)"]
        CP["Customer Portal<br/>(React 18 / TypeScript / RTL & LTR)"]
        EP["Employee Portal<br/>(Operations, Compliance & Support)"]
    end

    subgraph APILayer ["API Gateway (FastAPI)"]
        AUTH["Auth & RBAC<br/>(JWT HS256)"]
        ROUTER["API Master Router<br/>(/api/v1)"]
        RAG_API["RAG Endpoint<br/>(/api/v1/rag/ask)"]
        OCR_API["OCR Endpoint<br/>(/api/v1/ocr/process-image-card)"]
        CMP_API["Complaints Endpoint<br/>(/api/v1/employee/complaints)"]
    end

    subgraph ServiceLayer ["Service Layer"]
        RAG_SVC["Production RAG Service<br/>(Portal Filter & Abstention)"]
        VEC_SVC["Qdrant Vector Service<br/>(4-Eyes Gate & Reconciliation)"]
        EMB_SVC["Embedding Service<br/>(Feature Hashing & Dense Projection)"]
        OCR_SVC["Image OCR Pipeline<br/>(PaddleOCR & 9D Validator)"]
        CMP_SVC["Complaint Intelligence<br/>(Deterministic Advisory Rules)"]
    end

    subgraph DataLayer ["Data & AI Infrastructure"]
        PG[("PostgreSQL 16.15<br/>Relational Ledger")]
        QD[("Qdrant Vector DB<br/>Policy Vector Store")]
        OLLAMA["Ollama LLM<br/>(Qwen3:8B Inference)"]
    end

    CP --> ROUTER
    EP --> ROUTER
    ROUTER --> AUTH
    ROUTER --> RAG_API
    ROUTER --> OCR_API
    ROUTER --> CMP_API
    RAG_API --> RAG_SVC
    OCR_API --> OCR_SVC
    CMP_API --> CMP_SVC
    RAG_SVC --> VEC_SVC
    RAG_SVC --> OLLAMA
    VEC_SVC --> EMB_SVC
    VEC_SVC --> QD
    VEC_SVC -.->|Reconciles with| PG
    ROUTER --> PG
```

---

## 3. Technology Stack

- **Frontend:**
  - React 18 SPA with TypeScript & Vite
  - Tailwind CSS for responsive styling
  - Lucide React iconography
  - Bilingual localization engine (Egyptian Arabic RTL + English LTR)
- **Backend:**
  - Python 3.11+ with FastAPI (asynchronous ASGI)
  - Pydantic v2 data validation and strict typing
  - SQLAlchemy 2.0 Async ORM with Asyncpg driver
  - Python-Jose (JWT cryptographic token handling)
  - Bcrypt secure credential hashing
- **Databases & Vector Stores:**
  - **Relational:** PostgreSQL 16.15 with `scram-sha-256` password authentication
  - **Vector Database:** Qdrant v1.12.5 (Cosine similarity metric, 384 dimensions)
  - **MVP Portable Storage:** Async SQLite (`nileops_mvp.db`) preserved as an offline fallback
- **AI & Document Intelligence:**
  - **Local LLM:** Ollama with `qwen3:8b` (extractive grounded fallback when offline/timed out)
  - **Embedding Service:** Sub-word character trigram feature hashing with deterministic orthonormal dense projection (384-d)
  - **OCR Engine:** PaddleOCR Arabic engine with deterministic 9-dimensional validator conforming to `docs/NATIONAL_ID_VALIDATION_SPEC.md`

---

## 4. Dual-Portal Banking Experience

NileOps enforces strict architectural and logical separation between public retail customers and authorized bank staff:

### A. Customer Portal
- Accessible to authenticated retail account holders.
- **Account Summary:** Real-time balances for Current and Savings accounts in EGP.
- **Transaction History:** Categorized debit/credit entries with timestamps and descriptions.
- **Interactive Complaint Submission:** Filing of service tickets with immediate tracking ID generation.
- **Certificates of Deposit Yield Calculator:** Simulated monthly returns based on Egyptian banking deposit rates (e.g., 23.5% annual yield).
- **Service Requests:** Submit account opening requests and card issuance requests with real-time state tracking.
- **AI Banking Assistant:** Policy question answering strictly scoped to public retail banking guidelines (`POL-RETAIL-001`).

### B. Employee Portal
- Accessible to staff members across canonical banking roles (`admin`, `operations_officer`, `customer_service`, `compliance_reviewer`, `branch_manager`).
- **Dashboard & Portfolio Search:** Inspect customer accounts, view KYC statuses, and review account activity.
- **Requests Queue:** Four-eyes review of customer account opening and debit card issuance requests.
- **Complaint Queue & Drawer:** Paginated table with server-side filters, sorting, SLA countdown, and advisory AI suggestions (deterministic category/team/priority suggestions).
- **Four-Eyes Policy Approval Workflow:** Create, review, approve, or reject bank operational policies. Creators are barred from approving their own documents.
- **KYC Document Queue:** Inspect and validate synthetic National ID cards under strict 9-dimensional compliance checks.
- **Audit Trail:** Role-scoped event logging with actor attribution and timestamps.

---

## 5. PostgreSQL 16 & Relational Persistence

The platform is natively integrated with **PostgreSQL 16.15**:
- **Application Role:** Dedicated least-privilege user `nileops_app` with schema privileges.
- **Authentication:** `scram-sha-256` configured and enforced in `pg_hba.conf`.
- **Database:** Dedicated database `nileops` with UTF-8 encoding.
- **Schema:** Relational entities (`users`, `accounts`, `transactions`, `complaints`, `policy_documents`, `kyc_verifications`, `audit_logs`, `account_opening_requests`, `card_requests`).
- **Test Database Isolation:** Test suites run strictly against `nileops_test`, protected by hard-failing guards.

---

## 6. Qdrant & Grounded RAG Architecture

The Knowledge Base and RAG pipeline provide grounded policy retrieval:
1. **Governance Before Ingestion (4-Eyes Check):**
   - Documents are ingested into Qdrant **only** after satisfying four-eyes approval (`status == 'APPROVED'`, designated approver, approver $\neq$ creator).
   - Draft, pending, or rejected documents are automatically excluded from the vector index during reconciliation.
2. **Strict Portal Boundary Filtering:**
   - **Customer Portal:** Filtered by `portal_access == 'customer'` AND `is_active == True`. Internal compliance manuals (e.g. `POL-KYC-001`) are physically excluded from search results (0.0% leakage).
   - **Employee Portal:** Retains visibility across both customer and employee operational policies.
3. **Thresholding & Explicit Abstention:**
   - Default similarity threshold is maintained at `0.15`.
   - Queries with top similarity score below `0.15` trigger standardized bilingual abstention, preventing hallucinations on out-of-domain queries.
4. **Verifiable Policy Citations:**
   - Every answer includes structured citations containing policy code, title, domain, and version.

---

## 7. Egyptian National ID 9D Intelligence (OCR)

Implements the specification defined in `docs/NATIONAL_ID_VALIDATION_SPEC.md`:

### Nine-Dimensional Evaluation Model
Every ID input or document scan is evaluated independently across 9 dimensions:
1. **Normalization (`D1`):** Normalizes Eastern Arabic digits (`٠-٩`) to Western digits (`0-9`); rejects disallowed characters.
2. **Format Validation (`D2`):** Century indicator ($C \in \{2, 3\}$), leap-year-aware calendar validation (e.g., Feb 29 on year 2000 is valid; Feb 29 on 1901 is invalid), and explicit `as_of_date` temporal boundaries.
3. **Governorate Reference (`D3`):** Validates against the 28 official Egyptian administrative governorate codes (01–35, 88).
4. **Gender Rule (`D4`):** Position 13 evaluates to Male (odd) or Female (even), classified strictly as provisional reference.
5. **Checksum Status (`D5`):** Position 14 verified as an ASCII numerical digit (no unverified government checksum formula claimed).
6. **OCR Extraction & Profile (`D6`):** Actively supports `EGY_NID_FRONT_V1`. Low confidence (<0.80) or unsupported document types trigger human review routing.
7. **Cross-Field Consistency (`D7`):** Compares OCR extracted values against user-provided onboarding form inputs.
8. **Review Routing (`D8`):** Implements Decision Tables 7.1.1 (Document AI) and 7.1.2 (Structured Intake) to emit compound statuses.
9. **Identity Verification (`D9`):** Permanent architectural invariant: `NOT_VERIFIED`.

---

## 8. Installation Prerequisites

- **Operating System:** Windows 10/11 (or Linux/macOS)
- **Python:** 3.11.x (tested on Python 3.11.9)
- **Node.js:** v20.x or v22.x LTS (with npm)
- **PostgreSQL:** Version 16.x (installed locally or via service)
- **Qdrant:** Version 1.12.x+ standalone executable or Python service (port 6333)
- **Ollama (Optional):** Running locally with `qwen3:8b` (extractive fallback operates autonomously when offline)

---

## 9. Native Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/AbdelrhmanAkl/NileOps_V4.git
cd NileOps_V4
```

### 2. Configure Backend Virtual Environment
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cd ..
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. Setup Qdrant Vector Database
Run the standalone Qdrant binary or the verified pure-Python dev substitute:
```bash
# Option A: Standalone Qdrant binary or Docker (Linux / CI / macOS / standard Windows)
docker run -d -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant:v1.12.0
# Or run standalone binary:
cd data/qdrant_storage && ../../bin/qdrant.exe

# Option B: Development Substitute Service (Machine-specific Windows workaround)
# On Windows hosts where unsigned binaries (qdrant.exe) or native C-extensions (.pyd)
# are blocked by Windows Smart App Control (SAC) / Code Integrity (Event 3077/3118),
# use the pure-Python in-memory dev substitute serving the identical 38-point nileops_kb collection:
python scratch/run_qdrant_service.py
```

> **Note on Windows Workarounds:** On workstations running Windows Smart App Control, two developer mitigations are documented (see `docs/RUNBOOK.md`):
> 1. `scratch/run_qdrant_service.py`: A pure-Python HTTP substitute on port 6333 matching Qdrant v1 REST API with zero native DLL dependencies.
> 2. `_PandasShimFinder`: A dynamic runtime meta-path import hook that shims `pandas` during PaddleOCR invocations when unsigned `.pyd` native extensions are blocked by OS security policy. Neither workaround is required in CI or standard Linux environments.

---

## 10. Environment Configuration

Copy `.env.example` to `.env` in both the repository root and `backend/`:
```bash
cp .env.example .env
cp .env.example backend/.env
```

Ensure configuration matches your local services:
```ini
ENVIRONMENT=development
DEBUG=true
PROJECT_NAME="NileOps Digital Banking Operations"
API_V1_PREFIX=/api/v1
SECRET_KEY=change-this-insecure-key-to-a-secure-256-bit-random-secret

# PostgreSQL 16 Connection
DATABASE_URL=postgresql+asyncpg://nileops_app:<YOUR_POSTGRES_PASSWORD>@127.0.0.1:5432/nileops

# Qdrant Vector DB
QDRANT_URL=http://127.0.0.1:6333

# Ollama LLM
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
```

---

## 11. Service Startup Instructions

Run the complete platform natively in separate terminals:

### Terminal 1: PostgreSQL 16
```bash
postgres -D <path_to_postgres_data>
```

### Terminal 2: Qdrant Vector Store
```bash
# Production / Native binary:
cd data/qdrant_storage && ../../bin/qdrant.exe

# OR Dev-Only Substitute (if qdrant.exe is restricted by Windows Smart App Control):
python scratch/run_qdrant_service.py
```

### Terminal 3: FastAPI Backend
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Service Health Probe: `http://localhost:8000/health`

### Terminal 4: React Frontend
```bash
cd frontend
npm run dev
```
- User Interface: `http://localhost:5173`

---

## 12. Running Automated Tests & Isolation

The backend test suite enforces strict isolation:
- **Relational Isolation:** All tests run against database `nileops_test`. The development database `nileops` is guarded and unreachable by tests.
- **Vector Isolation:** All tests run against collection `nileops_kb_test`. A hard-failing check in `vector_store.py` ensures tests fail immediately if the collection does not end with `_test`.

### Execute Test Suite (119 Tests)
```bash
cd backend
pytest -v -x -s --durations=10
```
Test module breakdown (119 passed / 100% pass rate):
- `tests/test_adversarial_agent.py` (29 tests): Allowlisted Ops Assistant agent, adversarial prompt injection defenses (EN/AR), forbidden tools refusal, and output guardrails (14-digit National ID, IBAN, and JWT scrubbing).
- `tests/test_health.py` (4 tests): Health probes, root redirect, API v1 status, and production JWT secret key guard.
- `tests/test_mvp.py` (6 tests): Authentication, RBAC isolation, data ownership, complaints, and four-eyes policy approval.
- `tests/test_complaint_intelligence.py` (6 tests): Deterministic advisory classification, SLA calculations, complaint lifecycle transitions, and employee pagination.
- `tests/test_simulated_requests.py` (7 tests): Account opening requests, debit card requests, and state machine validation.
- `tests/test_iban_masking.py` (2 tests): Public IBAN masking invariants.
- `tests/test_kpi_service.py` (6 tests): Operational KPI calculation engine and employee role RBAC.
- `tests/test_kyc_document_ai.py` (3 tests): Synthetic National ID masking, review notes requirements, and KYC lifecycle.
- `tests/test_kyc_mismatch.py` (12 tests): Cross-field KYC discrepancy checks (birthdate vs ID, governorate vs ID, low OCR confidence, missing fields).
- `tests/test_ocr.py` (12 tests): Digit normalization, leap-year calendar validation, governorate allowlists, Decision Tables 7.1.1 & 7.1.2.
- `tests/test_ocr_phase_2_1.py` (9 tests): Address parsing, WebP validation, and security fuzzing.
- `tests/test_ocr_phase_2_2.py` (5 tests): Image quality assessment, CLAHE contrast enhancement, and deskewing.
- `tests/test_ocr_security.py` (6 tests): Image size guards, decompression bomb protection, and PII masking.
- `tests/test_production_guards.py` (7 tests): Weak secret rejection, CORS wildcard prevention, login lockout, and sliding-window rate limiting.
- `tests/test_rag.py` (8 tests): Qdrant health, grounded answers, portal isolation, abstention, POL-TEST exclusion, and RBAC guards.

### Frontend Typecheck & Build
```bash
cd frontend
npm run build
```

---

## 13. Demo Authentication & Seed Profiles

For rapid local evaluation, NileOps provides convenient **1-click quick-login buttons** on the login screen (`http://localhost:5173`) that pre-fill synthetic development credentials for each supported role:

- **Retail Customer 1:** Active checking and savings accounts; recent transaction history.
- **Retail Customer 2:** Alternate customer profile for multi-tenant data ownership verification.
- **Operations Officer:** Access to the employee operations queue and customer portfolio.
- **Customer Service:** Complaint resolution and customer ticket handling.
- **Compliance Reviewer:** First-line policy creation and KYC inspection queue.
- **Branch Manager:** Second-line policy four-eyes approver and audit manager.
- **System Administrator:** System-wide management and technical oversight.

*Note: In accordance with security practices, plaintext seed passwords are not published in public documentation. They are managed through git-ignored local environment files and local database seed routines.*

---

## 14. Transparent Architectural Limitations

NileOps is designed as an architectural reference implementation and simulator. In the interest of engineering transparency, the following technical limitations are explicitly documented:

> [!IMPORTANT]
> **Known Limitations & Simulation Scope Notice:**
> - **100% Synthetic Simulation:** All data within NileOps—including customer profiles, account balances, complaint tickets, transaction ledgers, and 14-digit Egyptian National IDs—is 100% synthetic mock data generated for developer simulation. The platform is an architectural prototype and is not a licensed financial institution.
> - **Local LLM & Deterministic Fallback:** If a local Ollama instance (`qwen3:8b`) is not running or times out (2.0s threshold), the platform automatically activates deterministic extractive quotation fallback (`fallback_used: true`). Answers are extracted verbatim from retrieved policy chunks, ensuring high availability and zero hallucinations without requiring active GPU/neural generation.

1. **Hashing (Non-Semantic) Embeddings & Paraphrase Drop:**
   - The active embedding pipeline (`backend/app/services/embedding.py`) utilizes sub-word character trigram feature hashing projected down to 384 dimensions rather than a deep contextual neural transformer (such as BGE-M3 or text-embedding-3).
   - While lexical keyword queries achieve 100% Hit@1, colloquial Egyptian Arabic queries (paraphrased with dialectal variations) experience a drop to **60.0% Hit@1** at threshold 0.15 (and 33.3% at threshold 0.20) due to character trigram distance.
2. **Deterministic Extractive Fallback vs. Generative LLM:**
   - In offline local environments where Ollama is unavailable or times out, the platform deterministically falls back to extractive text quotation from the top-scoring policy chunk (`_synthesize_fallback_answer`).
   - The reported **"0.0% Hallucination Rate" reflects deterministic text extraction without token generation**, rather than neural model alignment or reasoning capability.
3. **OCR Performance vs. Egyptian Banking Handbook Target:**
   - The Egyptian Banking Handbook specifies a target field $F_1 \ge 90\%$.
   - Measured on our 40-card synthetic test set, this target is **NOT met**:
     - **Name Field $F_1$:** **62.5%**
     - **Address Field $F_1$:** **50.0%**
     - **National ID Field $F_1$:** **87.5%**
     - **Routed to Human Review:** **55.0%** of synthetic images.
   - All evaluation was conducted strictly on synthetic test cards without access to real citizen cards.
4. **Declarative Database Initialization without Alembic:**
   - Relational schemas are initialized declaratively via SQLAlchemy `create_all` during startup.
   - An incremental schema migration toolchain (such as Alembic) is not currently implemented; schema changes require declarative table updates or clean test resets.
5. **Simulation Boundary — Not a Commercial Bank:**
   - NileOps is a demonstration simulation platform and does not possess a CBE banking license.
   - No connections exist to live interbank switches, CBE core settlement networks, or the Ministry of Interior Civil Status Organization.
6. **Local Native Scope — Deployment Excluded:**
   - The project is architected and verified for local native developer execution.
   - Production cloud deployment, Kubernetes manifests, automated CI/CD pipelines, and public edge hosting are outside the scope of this project.

---

## 15. User Interface & Screenshot Index

Comprehensive visual evidence for all bilingual dual-portal workflows is indexed in [`docs/screenshots/SCREENSHOT_INDEX.md`](file:///c:/AI/NileOps_V4/docs/screenshots/SCREENSHOT_INDEX.md):

| Interface Screen | Language | Key Verification Focus |
| :--- | :---: | :--- |
| **Customer Portal Overview** | EN / AR | Dual-account balance cards, transaction ledger, CD yield calculator. |
| **Customer Complaint Filing** | EN / AR | Category selection, priority assignment, instant tracking code. |
| **AI Banking Assistant** | EN / AR | Grounded policy citations, expandable context drawer, abstention banner. |
| **Customer Requests Form** | EN / AR | Account opening and card requests with deterministic rule evaluation. |
| **Employee Dashboard** | EN / AR | KPI counters, requests review queue, customer search. |
| **Employee Complaint Queue** | EN / AR | Server-side pagination, SLA countdown timer, deterministic advisory drawer. |
| **KYC Document Queue** | EN / AR | 9D compliance inspector, mandatory reviewer notes on rejection, PII masking. |
| **Audit Trail & Governance** | EN / AR | Role-scoped event audit log with actor attribution and timestamps. |

---

## 16. Technical Documentation & Reports

Detailed technical reports and evaluation benchmarks are maintained in `docs/`:
- [`docs/CURRENT_PROJECT_STATE_REPORT.md`](file:///c:/AI/NileOps_V4/docs/CURRENT_PROJECT_STATE_REPORT.md): Complete feature implementation matrix, test metrics, and known defect audit.
- [`docs/RAG_EVALUATION.md`](file:///c:/AI/NileOps_V4/docs/RAG_EVALUATION.md): Dual-portal RAG benchmark, threshold sweep, and POL-TEST remediation.
- [`docs/OCR_IMAGE_LEVEL_EVALUATION.md`](file:///c:/AI/NileOps_V4/docs/OCR_IMAGE_LEVEL_EVALUATION.md): 40-image synthetic OCR evaluation, CER, and Handbook comparison.
- [`docs/NATIONAL_ID_VALIDATION_SPEC.md`](file:///c:/AI/NileOps_V4/docs/NATIONAL_ID_VALIDATION_SPEC.md): 9-dimensional Egyptian National ID specification and Decision Tables.
- [`docs/POSTGRESQL_IMPLEMENTATION_REPORT.md`](file:///c:/AI/NileOps_V4/docs/POSTGRESQL_IMPLEMENTATION_REPORT.md): PostgreSQL 16 migration, SCRAM-SHA-256, and isolation report.
- [`docs/screenshots/SCREENSHOT_INDEX.md`](file:///c:/AI/NileOps_V4/docs/screenshots/SCREENSHOT_INDEX.md): Index of captured visual verification evidence.

---

## 17. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
