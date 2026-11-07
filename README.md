# NileOps — Intelligent Digital Banking Operations Platform

[![Backend Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)]()
[![Frontend Build](https://img.shields.io/badge/frontend-Vite%20%2B%20TypeScript-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.15-336791.svg)]()
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.12-red.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **Fictional Simulation Identity:** NileOps Demo Bank  
> **Simulation Disclaimer:** NileOps is an enterprise-pattern digital banking demonstration and operations prototype. It is **not** a licensed financial institution, is not connected to live Egyptian Central Bank (CBE) or Civil Status networks, and does **not** process real financial transactions or genuine citizen identification documents. All data, customer profiles, account balances, and National ID numbers are 100% synthetic.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. System Architecture](#2-system-architecture)
- [3. Technology Stack](#3-technology-stack)
- [4. Dual-Portal Banking Experience](#4-dual-portal-banking-experience)
- [5. PostgreSQL 16 Integration](#5-postgresql-16-integration)
- [6. Qdrant & Production RAG Architecture](#6-qdrant--production-rag-architecture)
- [7. OCR & Document Intelligence](#7-ocr--document-intelligence)
- [8. Installation Prerequisites](#8-installation-prerequisites)
- [9. Native Windows Setup Guide](#9-native-windows-setup-guide)
- [10. Environment Configuration](#10-environment-configuration)
- [11. Service Startup Instructions](#11-service-startup-instructions)
- [12. Running Automated Tests](#12-running-automated-tests)
- [13. Synthetic Demo Credentials](#13-synthetic-demo-credentials)
- [14. Security Boundaries & Limitations](#14-security-boundaries--limitations)
- [15. User Interface & Screenshots](#15-user-interface--screenshots)

---

## 1. Project Overview

**NileOps** is an intelligent, bilingual (Arabic & English) digital banking operations simulation platform designed around Egyptian banking standards and regulatory frameworks. 

The platform addresses critical operational friction in consumer banking:
1. **Customer Self-Service:** Instant balance inquiries, transaction tracking, certificate of deposit yield calculators, policy Q&A, and complaint submission.
2. **Operations & Compliance Workflow:** Four-eyes policy approval governance, complaint lifecycle resolution with internal notes, customer portfolio administration, and human-in-the-loop KYC inspection queues.
3. **Retrieval-Augmented Generation (RAG):** Context-grounded policy question answering using Qdrant vector retrieval with strict portal boundary isolation, dynamic vector sizing, and explicit hallucination abstention.
4. **Document Intelligence (OCR):** Deterministic 9-dimensional validation of 14-digit Egyptian National ID structures, calendar math, governorate allowlists, and review routing.

---

## 2. System Architecture

```mermaid
graph TB
    subgraph ClientLayer ["Client Layer (Dual Portal)"]
        CP["Customer Portal<br/>(React 18 / TS / RTL & LTR)"]
        EP["Employee Portal<br/>(Operations & Compliance)"]
    end

    subgraph APILayer ["API Gateway (FastAPI)"]
        AUTH["Auth & RBAC<br/>(JWT HS256)"]
        ROUTER["API Master Router<br/>(/api/v1)"]
        RAG_API["RAG Endpoint<br/>(/api/v1/rag/ask)"]
        OCR_API["OCR Endpoint<br/>(/api/v1/ocr/validate)"]
    end

    subgraph ServiceLayer ["Service Layer"]
        RAG_SVC["Production RAG Service<br/>(Portal Filter & Abstention)"]
        VEC_SVC["Qdrant Vector Service<br/>(4-Eyes Gate & Reconciliation)"]
        EMB_SVC["Semantic Embedding Service<br/>(Arabic Normalization & Probing)"]
        OCR_SVC["OCR 9D Validator<br/>(Tables 7.1.1 & 7.1.2)"]
    end

    subgraph DataLayer ["Data & AI Infrastructure"]
        PG[("PostgreSQL 16.15<br/>Relational Ledger")]
        QD[("Qdrant Vector DB<br/>Policy Vector Store")]
        OLLAMA["Ollama Server<br/>(Qwen3:8B Inference)"]
    end

    CP --> ROUTER
    EP --> ROUTER
    ROUTER --> AUTH
    ROUTER --> RAG_API
    ROUTER --> OCR_API
    RAG_API --> RAG_SVC
    OCR_API --> OCR_SVC
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
  - Tailwind CSS for modern responsive styling
  - Lucide React iconography
  - Bilingual localization engine (Egyptian Arabic RTL + English LTR)
- **Backend:**
  - Python 3.11.9 + FastAPI (asynchronous ASGI)
  - Pydantic v2 data validation and strict typing
  - SQLAlchemy 2.0 Async ORM + Asyncpg driver
  - Python-Jose (JWT cryptographic token handling)
  - Bcrypt secure credential hashing
- **Databases & Vector Stores:**
  - **Relational:** PostgreSQL 16.15 with `scram-sha-256` password authentication
  - **Vector Database:** Qdrant v1.12.5 (Windows standalone executable, Cosine metric)
  - **MVP Portable Storage:** Async SQLite (`nileops_mvp.db`) preserved as a development fallback
- **AI / LLM & Document Intelligence:**
  - **Local LLM:** Ollama running `qwen3:8b` (4096 context / dynamic discovery)
  - **Semantic Vectorizer:** High-performance dense projection with Arabic diacritics removal and token hashing
  - **OCR Engine:** Deterministic 9-dimensional National ID validator conforming to `docs/NATIONAL_ID_VALIDATION_SPEC.md`

---

## 4. Dual-Portal Banking Experience

NileOps enforces strict architectural and logical separation between public retail customers and authorized bank staff:

### A. Customer Portal
- Accessible to authenticated retail account holders (`customer1@nileops.demo`).
- **Account Summary:** Real-time balances for Current and Savings accounts in EGP.
- **Transaction History:** Categorized debit/credit entries with timestamps and descriptions.
- **Interactive Complaint Submission:** Filing of service tickets with immediate tracking ID generation.
- **Certificates of Deposit Yield Calculator:** Simulated monthly returns based on current Egyptian banking deposit rates (e.g., 23.5% annual yield).
- **AI Banking Assistant:** Policy question answering strictly scoped to public retail banking guidelines.

### B. Employee Portal
- Accessible to staff members across canonical banking roles (`admin`, `operations_officer`, `customer_service`, `compliance_reviewer`, `branch_manager`).
- **Portfolio Search:** Search customer accounts, view KYC statuses, and inspect account activity.
- **Complaint Queue:** Update complaint states (`IN_REVIEW`, `RESOLVED`, `REJECTED`) and attach internal audit notes.
- **Four-Eyes Policy Approval Workflow:** Create, review, approve, or reject bank operational policies. Creators are barred from approving their own documents.
- **KYC Document Queue:** Inspect and validate synthetic National ID cards under strict 9-dimensional compliance checks.

---

## 5. PostgreSQL 16 Integration

The platform is natively integrated with **PostgreSQL 16.15**:
- **Application Role:** Dedicated least-privilege user `nileops_app` with schema privileges.
- **Authentication:** `scram-sha-256` configured and enforced in `pg_hba.conf`.
- **Database:** Dedicated database `nileops` with UTF-8 encoding.
- **Schema & Migration:** 7 core relational entities (`users`, `accounts`, `transactions`, `complaints`, `policy_documents`, `kyc_verifications`, `audit_logs`).
- **Data Continuity:** Synthetic seed data migrated seamlessly from SQLite; the original SQLite database file `backend/nileops_mvp.db` remains intact as an offline backup.

---

## 6. Qdrant & Production RAG Architecture

The Knowledge Base and RAG pipeline provide grounded policy retrieval:
1. **Governance Before Ingestion (4-Eyes Check):**
   - Documents are ingested into Qdrant **only** after satisfying four-eyes approval (`status == 'APPROVED'`, designated approver, approver $\neq$ creator).
   - Draft, pending, or rejected documents are automatically purged from the vector index during reconciliation.
2. **Strict Portal Boundary Filtering:**
   - **Customer Portal:** Filtered by `portal_access == 'customer'` AND `is_active == True`. Internal compliance manuals (e.g. `POL-KYC-001`) are physically excluded from search results.
   - **Employee Portal:** Retains visibility across both customer and employee operational policies.
3. **Thresholding & Explicit Abstention:**
   - Queries with a maximum similarity score below threshold ($\text{score} < 0.15$) trigger a standardized abstention message, completely eliminating hallucinations on out-of-domain queries.
4. **Verifiable Policy Citations:**
   - Every answer includes structured citations containing the policy code (e.g., `POL-RETAIL-001`), title, domain, and version.

---

## 7. OCR & Document Intelligence

Implements the specification defined in `docs/NATIONAL_ID_VALIDATION_SPEC.md`:

### Nine-Dimensional Evaluation Model
Every ID input or document scan is evaluated independently across 9 dimensions:
1. **Normalization (`D1`):** Normalizes Eastern Arabic digits (`٠-٩`) to Western digits (`0-9`); rejects disallowed characters.
2. **Format Validation (`D2`):** Century indicator ($C \in \{2, 3\}$), leap-year-aware calendar validation (e.g., Feb 29 on year 2000 is valid; Feb 29 on 1901 is invalid), and explicit `as_of_date` temporal boundaries.
3. **Governorate Reference (`D3`):** Validates against the 28 official Egyptian administrative governorate codes (01–35, 88).
4. **Gender Rule (`D4`):** Position 13 evaluates to Male (odd) or Female (even), classified strictly as provisional reference.
5. **Checksum Status (`D5`):** Position 14 verified as an ASCII numerical digit (no unverified government checksum formula claimed).
6. **OCR Extraction & Profile (`D6`):** Actively supports `EGY_NID_FRONT_V1`. Low confidence (<0.80) or unsupported document types (e.g., passports) trigger human review routing.
7. **Cross-Field Consistency (`D7`):** Compares OCR extracted values against user-provided onboarding form inputs.
8. **Review Routing (`D8`):** Implements Decision Tables 7.1.1 (Document AI) and 7.1.2 (Structured Intake) to emit compound statuses (`PROVISIONAL_FORMAT_AND_CONSISTENCY_PASSED`, `PROVISIONAL_FORMAT_PASSED_CONSISTENCY_UNCHECKED`, or `REQUIRES_HUMAN_REVIEW`).
9. **Identity Verification (`D9`):** Permanent architectural invariant: `NOT_VERIFIED`.

---

## 8. Installation Prerequisites

- **Operating System:** Windows 10/11 (or Linux/macOS)
- **Python:** 3.11.x (tested on Python 3.11.9)
- **Node.js:** v20.x or v22.x LTS (tested on Node.js v26.13.0 LTS & npm 11.20.0)
- **PostgreSQL:** Version 16.x (installed locally or via service)
- **Qdrant:** Version 1.12.x+ standalone executable (see setup instructions below)
- **Ollama (Optional for LLM generation):** Running locally with `qwen3:8b` (fallback synthesis operates autonomously if Ollama is offline)

---

## 9. Native Windows Setup Guide

### 1. Clone the Repository
```powershell
git clone https://github.com/AbdelrhmanAkl/NileOps_V4.git
cd NileOps_V4
```

### 2. Configure Backend Virtual Environment
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### 3. Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### 4. Setup Qdrant Vector Database
Download the official standalone Qdrant binary for Windows:
```powershell
# Create directories
New-Item -ItemType Directory -Path "bin", "data\qdrant_storage" -Force

# Download and extract Qdrant Windows release
$url = "https://github.com/qdrant/qdrant/releases/download/v1.12.5/qdrant-x86_64-pc-windows-msvc.zip"
Invoke-WebRequest -Uri $url -OutFile "qdrant.zip" -UseBasicParsing
Expand-Archive -Path "qdrant.zip" -DestinationPath "bin" -Force
Remove-Item "qdrant.zip" -Force
```

---

## 10. Environment Configuration

Copy `.env.example` to `.env` in both the repository root and `backend/`:
```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
```

Ensure the configuration matches your local services:
```ini
ENVIRONMENT=development
DEBUG=true
PROJECT_NAME="NileOps Digital Banking Operations"
API_V1_PREFIX=/api/v1
SECRET_KEY=change-this-to-a-secure-random-secret-in-production

# PostgreSQL 16 Connection
DATABASE_URL=postgresql+asyncpg://nileops_app:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/nileops

# Qdrant Vector DB
QDRANT_URL=http://127.0.0.1:6333

# Ollama LLM
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
```

---

## 11. Service Startup Instructions

Open four PowerShell windows to run the complete stack:

### Window 1: PostgreSQL 16
```powershell
& "C:\PostgreSQL\16\pgsql\bin\postgres.exe" -D "C:\PostgreSQL\data"
```

### Window 2: Qdrant Vector Store
```powershell
Set-Location "C:\AI\NileOps_V4\data\qdrant_storage"
& "C:\AI\NileOps_V4\bin\qdrant.exe"
```

### Window 3: FastAPI Backend
```powershell
cd C:\AI\NileOps_V4\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Service Health Probe: `http://localhost:8000/health`

### Window 4: React Frontend
```powershell
cd C:\AI\NileOps_V4\frontend
npm run dev
```
- User Interface: `http://localhost:5173`

---

## 12. Running Automated Tests

### Backend Automated Test Suite (22 Tests)
```powershell
cd C:\AI\NileOps_V4\backend
.\.venv\Scripts\Activate.ps1
pytest -v
```
All 22 automated tests execute in under 10 seconds:
- `backend/tests/test_health.py`: 3 passed (Health probes, root redirect, API v1 status)
- `backend/tests/test_mvp.py`: 6 passed (Authentication, RBAC isolation, data ownership, complaints, 4-eyes policy approval)
- `backend/tests/test_ocr.py`: 9 passed (Normalization, leap year calendar math, governorate allowlists, Decision Tables 7.1.1 & 7.1.2, identity invariants)
- `backend/tests/test_rag.py`: 4 passed (Qdrant health, grounded answers, portal isolation, abstention on off-topic queries)

### Frontend Production Build
```powershell
cd C:\AI\NileOps_V4\frontend
npm run build
```
Compiles TypeScript and bundles production assets via Vite with zero warnings or errors.

---

## 13. Synthetic Demo Credentials

The platform includes convenient 1-click login buttons on the login screen, pre-populated with synthetic development accounts:

| Role / User Profile | Email | Password | Primary Portal |
| :--- | :--- | :--- | :--- |
| **Retail Customer 1** | `customer1@nileops.demo` | `Customer2026!` | Customer Portal |
| **Retail Customer 2** | `customer2@nileops.demo` | `Customer2026!` | Customer Portal |
| **Operations Officer** | `ops@nileops.demo` | `NileOps2026!` | Employee Portal |
| **Customer Service** | `cs@nileops.demo` | `NileOps2026!` | Employee Portal |
| **Compliance Reviewer** | `compliance@nileops.demo` | `NileOps2026!` | Employee Portal |
| **Branch Manager** | `manager@nileops.demo` | `NileOps2026!` | Employee Portal |
| **System Administrator** | `admin@nileops.demo` | `NileOps2026!` | Employee Portal |

*All credentials and identities are strictly synthetic and reserved exclusively for local evaluation.*

---

## 14. Security Boundaries & Limitations

1. **Egyptian Data Protection Law 151/2020 Compliance:**
   - Raw National ID numbers and personal identifiers are masked (`2950****1234`) across all public APIs, frontend responses, and audit records.
   - Real Egyptian citizen identification cards or authentic personal documents are strictly prohibited from entering this repository.
2. **Permanent Identity Boundary Invariant:**
   - Passing synthetic format or OCR checks **never** constitutes legal identity verification. The platform explicitly emits `identity_verification_status = NOT_VERIFIED`.
3. **No Autonomous Financial Ledger Writes:**
   - Balances, certificates, and transfers operate in an isolated simulation sandbox without external monetary impact.
4. **Separation of Duties (4-Eyes Rule):**
   - Critical banking policies require dual-control sign-off. Policy creators cannot approve their own documents.

---

## 15. User Interface & Screenshots

| Interface Screen | Description |
| :--- | :--- |
| **Login & Role Selector** | Quick 1-click role selection between Customer and Employee personas with instant Arabic RTL / English LTR toggle. |
| **Customer Portal Overview** | Real-time synthetic account cards, recent transaction history, and certificate of deposit yield calculator. |
| **AI Banking Assistant** | Grounded Arabic conversational assistance citing specific policy codes and answering account opening inquiries. |
| **Employee Operations Queue** | Customer search, complaint resolution workflow with internal notes, and 4-eyes policy approval management. |
| **KYC Document Review Queue** | 9-dimensional compliance inspector for National ID verification with automatic routing to human review. |

---

## 16. Implementation Reports & Documentation

Comprehensive technical documentation is maintained in the `docs/` directory:
- [POSTGRESQL_IMPLEMENTATION_REPORT.md](file:///c:/AI/NileOps_V4/docs/POSTGRESQL_IMPLEMENTATION_REPORT.md): Native PostgreSQL 16 configuration and migration report.
- [QDRANT_IMPLEMENTATION_REPORT.md](file:///c:/AI/NileOps_V4/docs/QDRANT_IMPLEMENTATION_REPORT.md): Qdrant vector database integration and governance report.
- [RAG_IMPLEMENTATION_REPORT.md](file:///c:/AI/NileOps_V4/docs/RAG_IMPLEMENTATION_REPORT.md): Dual-portal RAG pipeline, thresholding, and citation report.
- [OCR_IMPLEMENTATION_REPORT.md](file:///c:/AI/NileOps_V4/docs/OCR_IMPLEMENTATION_REPORT.md): Egyptian National ID 9D validation model and test report.
- [FINAL_INTEGRATION_REPORT.md](file:///c:/AI/NileOps_V4/docs/FINAL_INTEGRATION_REPORT.md): End-to-end integration and verification report.
- [NATIONAL_ID_VALIDATION_SPEC.md](file:///c:/AI/NileOps_V4/docs/NATIONAL_ID_VALIDATION_SPEC.md): Complete engineering specification for Egyptian ID validation.

---

## 17. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
