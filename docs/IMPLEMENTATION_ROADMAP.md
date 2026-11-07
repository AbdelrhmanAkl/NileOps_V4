# NileOps V4 — Implementation Roadmap

> **Master Implementation Plan for an AI-Powered Digital Banking Operations Platform**
>
> Version: 1.0 | Created: 2026-11-07 | Status: Phase 0 — Requirements Audit & Architecture

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Prerequisites](#2-prerequisites)
- [3. Phase Details](#3-phase-details)
  - [Phase 0: Requirements Audit & Architecture](#phase-0-requirements-audit--architecture)
  - [Phase 1: Project Scaffolding & Development Environment](#phase-1-project-scaffolding--development-environment)
  - [Phase 2: Database Schema & Synthetic Data](#phase-2-database-schema--synthetic-data)
  - [Phase 3: Authentication & RBAC](#phase-3-authentication--rbac)
  - [Phase 4: FastAPI Services](#phase-4-fastapi-services)
  - [Phase 5: OCR & Document Intelligence](#phase-5-ocr--document-intelligence)
  - [Phase 6: Banking Knowledge Base & RAG](#phase-6-banking-knowledge-base--rag)
  - [Phase 7: Qwen LLM Integration](#phase-7-qwen-llm-integration)
  - [Phase 8: Agentic AI & Tool Permissions](#phase-8-agentic-ai--tool-permissions)
  - [Phase 9: Workflow & Human-in-the-Loop](#phase-9-workflow--human-in-the-loop)
  - [Phase 10: Frontend & Dashboard Integration](#phase-10-frontend--dashboard-integration)
  - [Phase 11: Analytics & Audit Trail](#phase-11-analytics--audit-trail)
  - [Phase 12: Testing, Security Review & Evaluation](#phase-12-testing-security-review--evaluation)
  - [Phase 13: Dockerization & Deployment Preparation](#phase-13-dockerization--deployment-preparation)
  - [Phase 14: Documentation, Screenshots, Demo Scenarios & GitHub Preparation](#phase-14-documentation-screenshots-demo-scenarios--github-preparation)
- [4. Phase Dependencies](#4-phase-dependencies)
- [5. Critical Path](#5-critical-path)
- [6. Quality Gates](#6-quality-gates)
- [7. Definition of Done](#7-definition-of-done)

---

## 1. Overview

### Implementation Strategy

NileOps V4 is an AI-powered digital banking operations platform that combines document intelligence (OCR), retrieval-augmented generation (RAG), agentic AI workflows, and a human-in-the-loop approval system. The platform is built as a portfolio-grade full-stack application demonstrating enterprise patterns in a banking domain.

### Core Principles

| Principle | Description |
|---|---|
| **Incremental Delivery** | Each phase produces a working, testable increment. No phase should leave the system in a broken state. |
| **Backend-First** | API and data layers are built and validated before UI integration, ensuring a contract-driven approach. |
| **AI-Last Integration** | LLM and agentic components are layered on top of stable CRUD services, not coupled into them. |
| **Test as You Go** | Every phase includes its own test suite. No phase is complete without passing acceptance criteria. |
| **Configuration over Hardcoding** | All secrets, model paths, endpoints, and feature flags are externalized to `.env` files and config modules. |

### Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| **Backend** | Python 3.11.9 + FastAPI + SQLAlchemy 2.0 + Alembic |
| **Database** | PostgreSQL 16 (Docker) |
| **Vector Store** | Qdrant (Docker) |
| **OCR** | PaddleOCR |
| **LLM** | Ollama + Qwen3:8B (local) |
| **AI Framework** | LangChain + LangGraph |
| **Containerization** | Docker + Docker Compose |

---

## 2. Prerequisites

### Already Available

- [x] Python 3.11.9 installed and on PATH
- [x] Ollama installed with `qwen3:8b` model pulled
- [x] Git installed and configured
- [x] Windows 11 development environment

### Must Install Before Phase 1

> [!IMPORTANT]
> These must be installed and verified before starting Phase 1. Phase 0 (architecture docs) has no runtime dependencies.

| Tool | Version | Install Command / URL | Verification |
|---|---|---|---|
| **Node.js** | 20 LTS (≥20.11) | `winget install OpenJS.NodeJS.LTS` | `node -v && npm -v` |
| **Docker Desktop** | ≥4.25 | https://docs.docker.com/desktop/install/windows-install/ | `docker --version && docker compose version` |
| **PostgreSQL client** | ≥16 | Bundled with Docker image; optional: `winget install PostgreSQL.psql` | `psql --version` |

### Environment Configuration

The following `.env` file will be created in Phase 1 and progressively expanded:

```env
# Database
DATABASE_URL=postgresql+asyncpg://nileops:nileops_dev@localhost:5432/nileops_db

# Auth
SECRET_KEY=<generated-in-phase-3>
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Ollama / LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=nileops_banking_kb

# OCR
OCR_LANG=en
OCR_USE_GPU=false
```

---

## 3. Phase Details

---

### Phase 0: Requirements Audit & Architecture

> **Status: 🔵 CURRENT**

| Attribute | Value |
|---|---|
| **Complexity** | **M** (Medium) |
| **Dependencies** | None — this is the starting phase |
| **Risk Factors** | Incomplete requirements leading to rework; over-engineering architecture for a portfolio project |

#### Objectives

- Establish a complete, reviewed set of project requirements
- Define system architecture with clear component boundaries
- Create the master implementation roadmap (this document)
- Set naming conventions, project structure standards, and coding guidelines

#### Tasks

- [x] Define the 15-phase implementation roadmap
- [ ] Create `docs/ARCHITECTURE.md` — system architecture with component diagrams
- [ ] Create `docs/REQUIREMENTS.md` — functional and non-functional requirements
- [ ] Create `docs/API_CONTRACTS.md` — preliminary API endpoint inventory with request/response shapes
- [ ] Create `docs/DATA_MODEL.md` — entity-relationship diagram and field-level schema design
- [ ] Create `docs/AI_STRATEGY.md` — LLM integration patterns, prompt templates, RAG pipeline design
- [ ] Create `docs/TECH_STACK.md` — justified technology choices and version pins
- [ ] Create `docs/PROJECT_STRUCTURE.md` — target directory layout for backend, frontend, and shared
- [ ] Review all Phase 0 documents for internal consistency
- [ ] Commit Phase 0 documents to Git with tag `v0.0.0-phase0`

#### Deliverables

| Deliverable | Path |
|---|---|
| Implementation Roadmap | `docs/IMPLEMENTATION_ROADMAP.md` |
| System Architecture | `docs/ARCHITECTURE.md` |
| Requirements Specification | `docs/REQUIREMENTS.md` |
| API Contracts | `docs/API_CONTRACTS.md` |
| Data Model | `docs/DATA_MODEL.md` |
| AI Strategy | `docs/AI_STRATEGY.md` |
| Tech Stack Justification | `docs/TECH_STACK.md` |
| Project Structure | `docs/PROJECT_STRUCTURE.md` |

#### Acceptance Criteria

1. All 8 Phase 0 documents exist and are internally consistent
2. `ARCHITECTURE.md` contains at least one Mermaid component diagram
3. `DATA_MODEL.md` contains a complete ER diagram covering all entities
4. `API_CONTRACTS.md` lists every planned endpoint with HTTP method, path, and summary
5. All documents pass markdown lint with no errors
6. Git repository initialized with `.gitignore` and Phase 0 commit

---

### Phase 1: Project Scaffolding & Development Environment

| Attribute | Value |
|---|---|
| **Complexity** | **M** (Medium) |
| **Dependencies** | Phase 0 |
| **Risk Factors** | Docker Desktop licensing/installation issues on Windows; Node.js version conflicts with existing installs |

#### Objectives

- Create the monorepo directory structure for backend, frontend, and infrastructure
- Configure all development tooling (linters, formatters, pre-commit hooks)
- Set up Docker Compose for PostgreSQL and Qdrant
- Validate the full dev loop: code → lint → test → run

#### Tasks

- [ ] Install Node.js 20 LTS and verify with `node -v`
- [ ] Install Docker Desktop and verify with `docker compose version`
- [ ] Create backend directory: `backend/` with `app/`, `tests/`, `alembic/` subdirectories
- [ ] Create frontend directory: `frontend/` via `npm create vite@latest frontend -- --template react-ts`
- [ ] Create `backend/pyproject.toml` with all Python dependencies pinned:
  - `fastapi[standard]>=0.115`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`
  - `paddleocr`, `paddlepaddle`, `langchain>=0.3`, `langgraph>=0.2`, `qdrant-client`
  - `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`
  - `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`
- [ ] Create Python virtual environment: `python -m venv backend/.venv`
- [ ] Install all Python dependencies: `pip install -e "backend[dev]"`
- [ ] Configure Ruff in `backend/pyproject.toml` (line-length=100, select rules)
- [ ] Configure MyPy in `backend/pyproject.toml` (strict mode for `app/`)
- [ ] Install frontend dependencies: Tailwind CSS 3, shadcn/ui, `axios`, `react-router-dom`, `@tanstack/react-query`, `recharts`, `lucide-react`
- [ ] Create `docker-compose.yml` at project root with services: `postgres`, `qdrant`
- [ ] Create `backend/.env` and `backend/.env.example` with all config keys
- [ ] Create `backend/app/__init__.py`, `backend/app/main.py` (minimal FastAPI app with `/health` endpoint)
- [ ] Run `docker compose up -d` and verify PostgreSQL and Qdrant are reachable
- [ ] Run `pytest backend/tests/test_health.py` — verify health endpoint returns `{"status": "ok"}`

#### Deliverables

| Deliverable | Path |
|---|---|
| Backend application shell | `backend/app/main.py` |
| Docker Compose | `docker-compose.yml` |
| Python project config | `backend/pyproject.toml` |
| Frontend application shell | `frontend/` |
| Environment template | `backend/.env.example` |
| Health check test | `backend/tests/test_health.py` |

#### Acceptance Criteria

1. `docker compose up -d` starts PostgreSQL on port 5432 and Qdrant on port 6333 without errors
2. `GET /health` returns `200 {"status": "ok"}`
3. `pytest backend/tests/` passes with ≥1 test
4. `ruff check backend/app/` returns 0 errors
5. `npm run dev` (from `frontend/`) starts Vite dev server on port 5173
6. `.gitignore` excludes `.venv/`, `node_modules/`, `.env`, `__pycache__/`, `*.pyc`

---

### Phase 2: Database Schema & Synthetic Data

| Attribute | Value |
|---|---|
| **Complexity** | **L** (Large) |
| **Dependencies** | Phase 1 (Docker + PostgreSQL running) |
| **Risk Factors** | Schema design errors requiring migration rewrites; async SQLAlchemy session management pitfalls |

#### Objectives

- Implement the complete database schema using SQLAlchemy 2.0 ORM models
- Configure Alembic for async migration management
- Seed the database with realistic synthetic banking data
- Establish the repository pattern for data access

#### Tasks

- [ ] Create `backend/app/models/__init__.py` — import all models
- [ ] Create `backend/app/models/base.py` — `DeclarativeBase` with common mixins (`id`, `created_at`, `updated_at`)
- [ ] Create `backend/app/models/user.py` — `User` model (id, email, hashed_password, full_name, role, is_active, created_at)
- [ ] Create `backend/app/models/customer.py` — `Customer` model (id, national_id, full_name, email, phone, address, risk_score, segment, created_at)
- [ ] Create `backend/app/models/account.py` — `Account` model (id, customer_id FK, account_number, account_type, balance, currency, status, opened_at)
- [ ] Create `backend/app/models/transaction.py` — `Transaction` model (id, account_id FK, type, amount, currency, description, reference, status, created_at)
- [ ] Create `backend/app/models/document.py` — `Document` model (id, customer_id FK, filename, file_path, doc_type, ocr_text, ocr_confidence, status, uploaded_at)
- [ ] Create `backend/app/models/workflow.py` — `WorkflowInstance` model (id, type, payload JSON, status, assigned_to FK, decision, decided_at, created_at)
- [ ] Create `backend/app/models/audit_log.py` — `AuditLog` model (id, user_id FK, action, entity_type, entity_id, details JSON, ip_address, created_at)
- [ ] Create `backend/app/db/session.py` — async engine, `AsyncSession` factory, `get_db` dependency
- [ ] Initialize Alembic: `alembic init -t async backend/alembic`
- [ ] Configure `backend/alembic/env.py` to use async engine and import all models
- [ ] Generate initial migration: `alembic revision --autogenerate -m "initial_schema"`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Create `backend/scripts/seed_data.py` — generates 50 customers, 120 accounts, 1000 transactions, 5 users (admin, operations_officer, customer_service, compliance_reviewer, branch_manager)
- [ ] Run seed script and verify data in PostgreSQL

#### Deliverables

| Deliverable | Path |
|---|---|
| ORM Models | `backend/app/models/*.py` |
| DB Session Setup | `backend/app/db/session.py` |
| Alembic Config | `backend/alembic/` |
| Initial Migration | `backend/alembic/versions/001_initial_schema.py` |
| Seed Script | `backend/scripts/seed_data.py` |

#### Acceptance Criteria

1. `alembic upgrade head` runs without errors on a clean database
2. `alembic downgrade base` followed by `alembic upgrade head` is idempotent
3. Seed script populates all tables with correct foreign key relationships
4. All models have proper indexes on frequently queried columns (email, account_number, national_id)
5. `SELECT count(*) FROM customers` returns 50; `SELECT count(*) FROM transactions` returns 1000
6. All timestamps use UTC timezone-aware datetime

---

### Phase 3: Authentication & RBAC

| Attribute | Value |
|---|---|
| **Complexity** | **M** (Medium) |
| **Dependencies** | Phase 2 (User model and database) |
| **Risk Factors** | JWT token handling edge cases; role hierarchy complexity; password hashing performance |

#### Objectives

- Implement JWT-based authentication with refresh tokens
- Build a role-based access control system with five roles
- Create reusable FastAPI dependencies for auth and authorization
- Secure all future endpoints behind authentication

#### Tasks

- [ ] Create `backend/app/core/security.py` — password hashing (bcrypt), JWT creation/verification, token models
- [ ] Create `backend/app/core/config.py` — Pydantic `Settings` class loading from `.env`
- [ ] Create `backend/app/schemas/auth.py` — `LoginRequest`, `TokenResponse`, `UserResponse` Pydantic models
- [ ] Create `backend/app/api/deps.py` — `get_current_user` dependency extracting user from JWT Bearer token
- [ ] Create `backend/app/api/deps.py` — `require_role(*roles)` dependency factory for RBAC
- [ ] Define role hierarchy: `admin`, `operations_officer`, `customer_service`, `compliance_reviewer`, `branch_manager` with explicit permission matrix
- [ ] Create `backend/app/api/routes/auth.py` — `POST /api/v1/auth/login` (returns access + refresh token)
- [ ] Create `backend/app/api/routes/auth.py` — `POST /api/v1/auth/refresh` (refresh token rotation)
- [ ] Create `backend/app/api/routes/auth.py` — `GET /api/v1/auth/me` (returns current user profile)
- [ ] Create `backend/app/api/routes/users.py` — `GET /api/v1/users` (admin only, list users)
- [ ] Create `backend/app/api/routes/users.py` — `POST /api/v1/users` (admin only, create user)
- [ ] Write `backend/tests/test_auth.py` — login success, login failure, expired token, role enforcement (8+ tests)
- [ ] Update seed script to hash passwords for seed users

#### Deliverables

| Deliverable | Path |
|---|---|
| Security Utilities | `backend/app/core/security.py` |
| Configuration | `backend/app/core/config.py` |
| Auth Schemas | `backend/app/schemas/auth.py` |
| Auth Dependencies | `backend/app/api/deps.py` |
| Auth Routes | `backend/app/api/routes/auth.py` |
| User Management Routes | `backend/app/api/routes/users.py` |
| Auth Tests | `backend/tests/test_auth.py` |

#### Acceptance Criteria

1. `POST /api/v1/auth/login` with valid credentials returns a JWT access token and refresh token
2. `POST /api/v1/auth/login` with invalid credentials returns `401`
3. `GET /api/v1/auth/me` with valid token returns user profile; without token returns `401`
4. A `customer_service` role user cannot access `GET /api/v1/users` (returns `403`)
5. An `admin` role user can access `GET /api/v1/users` (returns `200`)
6. Expired tokens return `401` with clear error message
7. All 8+ tests in `test_auth.py` pass

---

### Phase 4: FastAPI Services

| Attribute | Value |
|---|---|
| **Complexity** | **L** (Large) |
| **Dependencies** | Phase 3 (Authentication + RBAC middleware) |
| **Risk Factors** | CRUD boilerplate proliferation; pagination/filtering complexity; async session management |

#### Objectives

- Build complete CRUD REST APIs for all banking domain entities
- Implement pagination, filtering, and sorting on list endpoints
- Create service layer abstractions separating business logic from route handlers
- Establish consistent error handling and response schemas

#### Tasks

- [ ] Create `backend/app/schemas/customer.py` — `CustomerCreate`, `CustomerUpdate`, `CustomerResponse`, `CustomerListResponse`
- [ ] Create `backend/app/schemas/account.py` — `AccountCreate`, `AccountUpdate`, `AccountResponse`
- [ ] Create `backend/app/schemas/transaction.py` — `TransactionCreate`, `TransactionResponse`, `TransactionListResponse`
- [ ] Create `backend/app/services/customer_service.py` — CRUD operations + search by national_id/name
- [ ] Create `backend/app/services/account_service.py` — CRUD + balance inquiry + account-by-customer
- [ ] Create `backend/app/services/transaction_service.py` — create transaction, list by account, list by date range
- [ ] Create `backend/app/api/routes/customers.py` — full CRUD: `GET /`, `GET /{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}`
- [ ] Create `backend/app/api/routes/accounts.py` — full CRUD + `GET /customers/{id}/accounts`
- [ ] Create `backend/app/api/routes/transactions.py` — `POST /`, `GET /`, `GET /{id}`, `GET /accounts/{id}/transactions`
- [ ] Implement query parameter pagination: `?page=1&size=20&sort_by=created_at&order=desc`
- [ ] Implement filtering: `?status=active&segment=retail&search=john`
- [ ] Create `backend/app/core/exceptions.py` — custom exception classes (`NotFoundError`, `ConflictError`, `ValidationError`)
- [ ] Create `backend/app/core/exception_handlers.py` — FastAPI exception handlers returning consistent error JSON
- [ ] Register all routers in `backend/app/main.py` under `/api/v1/` prefix
- [ ] Write `backend/tests/test_customers.py` — 10+ tests covering CRUD, pagination, search, auth enforcement

#### Deliverables

| Deliverable | Path |
|---|---|
| Customer API | `backend/app/api/routes/customers.py` |
| Account API | `backend/app/api/routes/accounts.py` |
| Transaction API | `backend/app/api/routes/transactions.py` |
| Service Layer | `backend/app/services/*.py` |
| Pydantic Schemas | `backend/app/schemas/*.py` |
| Exception Handling | `backend/app/core/exceptions.py`, `exception_handlers.py` |
| Test Suite | `backend/tests/test_customers.py` |

#### Acceptance Criteria

1. All CRUD endpoints return correct HTTP status codes (200, 201, 404, 409, 422)
2. `GET /api/v1/customers?page=2&size=10` returns exactly 10 results with correct pagination metadata
3. `GET /api/v1/customers?search=ahmed` performs case-insensitive search on name and email
4. All endpoints require authentication (return 401 without token)
5. Write operations (POST, PUT, DELETE) require `branch_manager` or `admin` role
6. Error responses follow consistent schema: `{"detail": "...", "error_code": "...", "status_code": 404}`
7. All tests pass with `pytest backend/tests/test_customers.py -v`

---

### Phase 5: OCR & Document Intelligence

| Attribute | Value |
|---|---|
| **Complexity** | **XL** (Extra Large) |
| **Dependencies** | Phase 4 (Document model + API patterns established) |
| **Risk Factors** | PaddleOCR installation issues on Windows; large model download times; OCR accuracy on banking documents; GPU memory if GPU is used |

#### Objectives

- Integrate PaddleOCR for extracting text from uploaded banking documents
- Build a document processing pipeline: upload → store → OCR → extract structured fields
- Support common banking document types (ID cards, bank statements, utility bills)
- Create a post-processing layer that extracts structured data from raw OCR text

#### Tasks

- [ ] Install PaddleOCR and PaddlePaddle: `pip install paddlepaddle paddleocr`
- [ ] Create `backend/app/services/ocr_service.py` — PaddleOCR wrapper with configurable language/model
- [ ] Create `backend/app/services/document_service.py` — document upload, storage, status tracking
- [ ] Create `backend/app/services/extraction_service.py` — regex + LLM-based field extraction from OCR text (name, ID number, date, amount)
- [ ] Create `backend/app/api/routes/documents.py`:
  - `POST /api/v1/documents/upload` — multipart file upload (PDF, PNG, JPG)
  - `GET /api/v1/documents/{id}` — document metadata + OCR results
  - `GET /api/v1/documents/{id}/text` — raw extracted text
  - `GET /api/v1/documents` — list documents with filtering by status, type, customer
  - `POST /api/v1/documents/{id}/reprocess` — re-run OCR on a document
- [ ] Create `backend/app/schemas/document.py` — `DocumentUploadResponse`, `DocumentDetail`, `OCRResult`
- [ ] Implement file storage in `backend/uploads/` with UUID-based naming to prevent collisions
- [ ] Add document type classification (heuristic: filename patterns + OCR content keywords)
- [ ] Create sample banking documents in `backend/tests/fixtures/` (2 sample images, 1 sample PDF)
- [ ] Write `backend/tests/test_ocr.py` — test OCR extraction, document upload, field extraction (6+ tests)
- [ ] Add file size validation (max 10MB) and file type validation (PDF, PNG, JPG, JPEG only)

#### Deliverables

| Deliverable | Path |
|---|---|
| OCR Service | `backend/app/services/ocr_service.py` |
| Document Service | `backend/app/services/document_service.py` |
| Extraction Service | `backend/app/services/extraction_service.py` |
| Document API | `backend/app/api/routes/documents.py` |
| Document Schemas | `backend/app/schemas/document.py` |
| Test Fixtures | `backend/tests/fixtures/sample_id.png`, `sample_statement.pdf` |
| OCR Tests | `backend/tests/test_ocr.py` |

#### Acceptance Criteria

1. `POST /api/v1/documents/upload` accepts a PNG image and returns document ID with status `processing`
2. After OCR completes, `GET /api/v1/documents/{id}` shows status `completed` with extracted text
3. PaddleOCR successfully extracts text from the sample test images with confidence > 0.7
4. Field extraction correctly identifies at least name and ID number from a sample national ID image
5. Uploading a file > 10MB returns `413`; uploading a `.exe` file returns `422`
6. All OCR tests pass

---

### Phase 6: Banking Knowledge Base & RAG

| Attribute | Value |
|---|---|
| **Complexity** | **XL** (Extra Large) |
| **Dependencies** | Phase 1 (Qdrant running in Docker), Phase 4 (API patterns) |
| **Risk Factors** | Embedding model download size; Qdrant indexing performance; chunk size tuning; retrieval relevance |

#### Objectives

- Build a synthetic banking domain knowledge base for **NileOps Demo Bank** covering 12 distinct policy domains
- Implement a policy governance state machine (`DRAFT → PENDING_APPROVAL → APPROVED → INDEXED`) ensuring no unapproved documents are indexed
- Implement an enterprise RAG (Retrieval-Augmented Generation) pipeline using Qdrant as the sole vector store with dynamic dimension discovery
- Create an embedding and hybrid retrieval pipeline supporting bilingual Arabic/English and Egyptian vernacular terminology
- Expose search and approval APIs that serve both the **Customer Portal** and the **Employee Portal** under strict context boundaries

#### Tasks

- [ ] Create `backend/data/knowledge_base/` directory with synthetic policy markdown files for **NileOps Demo Bank** covering 12 domains:
  1. Current & savings accounts
  2. Account opening & maintenance
  3. KYC & document requirements
  4. Debit & credit cards
  5. Domestic transfers & payments
  6. InstaPay-related guidance
  7. Certificates & deposits
  8. Loans & financing
  9. Fees, charges, & service limits
  10. Complaints & dispute resolution
  11. Branch & ATM services
  12. Digital banking & mobile application support
- [ ] Create `backend/app/services/embedding_service.py` — local multilingual text embedding service with dynamic dimension discovery (probing `len(embed_model.encode('test'))` or reading model configuration at startup; rejecting incompatible dimension/collection combinations)
- [ ] Create `backend/app/services/knowledge_base_service.py`:
  - Mandatory policy approval lifecycle: documents upload as `DRAFT` or `PENDING_APPROVAL`, transition to `APPROVED` only by authorized `compliance_reviewer` or `branch_manager` (enforcing separation of duties: `approved_by != uploaded_by`)
  - Duplicate detection using SHA-256 content hashing (`content_sha256`)
  - Configurable document chunking (evaluated against representative bilingual test queries; initial default 512 tokens with 50 overlap)
  - Metadata tagging (source, category, section, version, target_portal, effective_date)
  - Qdrant collection initialization using discovered embedding dimension and HNSW cosine metric
  - Vector indexing executed strictly post-approval; failed indexing triggers `INDEX_FAILED` state without marking document published
  - Tombstoning/deactivation of superseded document chunks (`is_active = FALSE`) upon activation of newer versions
  - Hybrid retrieval combining Qdrant dense semantic search with PostgreSQL `tsvector` keyword matching and configurable score fusion
- [ ] Create `backend/app/services/rag_service.py`:
  - Query → embed → hybrid retrieve top-k → score fusion → filter context → format citations
  - Source attribution with document title, version, section heading, and page number
  - Contextual portal pre-filtering (`target_portal IN ('customer_portal', 'shared')` for Customer Portal; employee portal accesses shared and internal)
  - Strict evidence thresholding (discard ungrounded chunks below evaluated relevance threshold)
- [ ] Create `backend/app/api/routes/knowledge_base.py`:
  - `POST /api/v1/kb/documents` — upload document metadata and content (status: `DRAFT` or `PENDING_APPROVAL`)
  - `POST /api/v1/kb/documents/{id}/approve` — review and approve policy document version (restricted to `compliance_reviewer` / `branch_manager`)
  - `POST /api/v1/kb/documents/{id}/index` — index approved document into Qdrant
  - `POST /api/v1/kb/search` — hybrid semantic search returning ranked chunks with provenance
  - `GET /api/v1/kb/stats` — collection statistics (approved vs draft counts, indexed chunks)
  - `DELETE /api/v1/kb/documents/{id}` — archive/tombstone document and purge from Qdrant active collection
- [ ] Create `backend/app/schemas/knowledge_base.py` — `KBDocumentCreate`, `KBApprovalRequest`, `KBSearchRequest`, `KBSearchResult`
- [ ] Create `backend/scripts/ingest_knowledge_base.py` — batch seed script for NileOps Demo Bank synthetic policy suite with simulated approvals
- [ ] Write `backend/tests/test_rag.py` — test approval gating, duplicate hash check, dynamic dimension discovery, chunking, and hybrid search relevance (10+ tests)

#### Deliverables

| Deliverable | Path |
|---|---|
| Banking KB Documents | `backend/data/knowledge_base/*.md` |
| Embedding Service | `backend/app/services/embedding_service.py` |
| Knowledge Base Service | `backend/app/services/knowledge_base_service.py` |
| RAG Service | `backend/app/services/rag_service.py` |
| KB Governance API | `backend/app/api/routes/knowledge_base.py` |
| Ingestion & Seed Script | `backend/scripts/ingest_knowledge_base.py` |
| RAG & Governance Tests | `backend/tests/test_rag.py` |

#### Acceptance Criteria

1. Uploaded documents enter `PENDING_APPROVAL` status and are **never** indexed into Qdrant before explicit approval
2. `compliance_reviewer` or `branch_manager` can approve a document version; uploader cannot approve their own document (separation of duties enforced with `403`)
3. Qdrant vector collection dimension dynamically matches the local embedding model without hardcoded assumptions
4. `POST /api/v1/kb/search` with query "How do I open a savings account?" returns relevant chunks from approved account opening policy with source citations
5. Hybrid retrieval relevance: top-1 result for domain-specific queries yields high relevance across both English and Arabic
6. Updating an approved document creates a new version; activating it tombstones superseded chunks from active search
7. All RAG and governance tests pass

---

### Phase 7: Qwen LLM Integration

| Attribute | Value |
|---|---|
| **Complexity** | **L** (Large) |
| **Dependencies** | Phase 6 (RAG pipeline provides context), Ollama with qwen3:8b available |
| **Risk Factors** | LLM response latency (~5-15s on CPU); prompt injection vulnerabilities; response quality variance; Ollama server stability |

#### Objectives

- Integrate the local Qwen3:8B model via Ollama for banking-domain Q&A
- Build a prompt engineering framework with system prompts, few-shot examples, and guardrails
- Create a chat API that combines RAG context with LLM generation
- Implement response streaming for better UX

#### Tasks

- [ ] Create `backend/app/services/llm_service.py`:
  - Ollama client wrapper (using `langchain-ollama` or `httpx`)
  - Sync and async generation methods
  - Streaming response support via SSE (Server-Sent Events)
  - Token counting and context window management
  - Timeout handling (30s max per request)
- [ ] Create `backend/app/core/prompts.py` — prompt templates:
  - `BANKING_SYSTEM_PROMPT` — role, constraints, tone, response format
  - `RAG_QA_PROMPT` — question + context → answer with citations
  - `DOCUMENT_SUMMARY_PROMPT` — summarize OCR-extracted text
  - `EXTRACTION_PROMPT` — extract structured fields from text
- [ ] Create `backend/app/services/chat_service.py`:
  - Orchestrate: user query → RAG retrieval → prompt assembly → LLM generation
  - Conversation history management (last N turns)
  - Source citation in responses
- [ ] Create `backend/app/api/routes/chat.py`:
  - `POST /api/v1/chat` — RAG-enhanced chat (returns full response)
  - `POST /api/v1/chat/stream` — SSE streaming chat endpoint
  - `POST /api/v1/chat/summarize` — summarize a document's OCR text
- [ ] Create `backend/app/schemas/chat.py` — `ChatRequest`, `ChatResponse`, `ChatMessage`, `StreamChunk`
- [ ] Implement LLM response guardrails: reject off-topic queries, limit response length, sanitize outputs
- [ ] Add Ollama health check to `/health` endpoint: `{"status": "ok", "ollama": "connected", "model": "qwen3:8b"}`
- [ ] Write `backend/tests/test_llm.py` — test prompt construction, response parsing, guardrails (6+ tests; mock Ollama for speed)

#### Deliverables

| Deliverable | Path |
|---|---|
| LLM Service | `backend/app/services/llm_service.py` |
| Prompt Templates | `backend/app/core/prompts.py` |
| Chat Service | `backend/app/services/chat_service.py` |
| Chat API | `backend/app/api/routes/chat.py` |
| Chat Schemas | `backend/app/schemas/chat.py` |
| LLM Tests | `backend/tests/test_llm.py` |

#### Acceptance Criteria

1. `POST /api/v1/chat` with `{"message": "What is the KYC process?"}` returns a coherent answer with cited KB sources
2. `POST /api/v1/chat/stream` returns an SSE stream with progressive text chunks
3. Ollama health check returns connection status in `/health` response
4. Off-topic queries (e.g., "Write me a poem about cats") return a polite redirect to banking topics
5. Response latency is < 30 seconds for standard queries (with timeout enforcement)
6. All LLM tests pass (with mocked Ollama responses)

---

### Phase 8: Agentic AI & Tool Permissions

| Attribute | Value |
|---|---|
| **Complexity** | **XL** (Extra Large) |
| **Dependencies** | Phase 7 (LLM integration), Phase 4 (CRUD services as tools), Phase 5 (OCR as tool) |
| **Risk Factors** | LangGraph complexity; tool execution safety; agent loop infinite recursion; permission boundary enforcement |

#### Objectives

- Build an agentic AI system using LangGraph that can reason and take actions
- Define banking-domain tools the agent can invoke (lookup customer, check balance, process document)
- Implement a permission system controlling which tools each role can authorize
- Create safety guardrails preventing unauthorized data modifications

#### Tasks

- [ ] Create `backend/app/agents/tools.py` — define LangChain-compatible tools:
  - `lookup_customer(national_id)` — search customer by national ID
  - `get_account_balance(account_number)` — retrieve current balance
  - `get_transaction_history(account_number, days=30)` — recent transactions
  - `search_knowledge_base(query)` — semantic search the banking KB
  - `process_document(document_id)` — trigger OCR processing
  - `create_workflow(type, payload)` — initiate a human-in-the-loop workflow
- [ ] Create `backend/app/agents/permissions.py` — tool permission matrix across the 5 canonical roles:
  - `customer_service`: lookup_customer, get_account_balance, search_knowledge_base
  - `operations_officer`: all read tools + get_transaction_history, initiate_workflow
  - `compliance_reviewer`: lookup_customer, get_transaction_history, search_knowledge_base, process_document, review_kyc
  - `branch_manager`: all operational tools including initiate_workflow and workflow approval
  - `admin`: all tools unrestricted for system administration
- [ ] Create `backend/app/agents/banking_agent.py` — LangGraph agent:
  - State graph with nodes: `reason`, `select_tool`, `execute_tool`, `synthesize`
  - Conditional edges based on tool selection
  - Max iteration limit (10 steps) to prevent infinite loops
  - Tool execution result integration into conversation
- [ ] Create `backend/app/agents/guardrails.py`:
  - Pre-execution validation: check tool permissions for current user role
  - Input sanitization: prevent SQL injection in tool parameters
  - Output filtering: mask sensitive data (full account numbers, balances) based on role
- [ ] Create `backend/app/api/routes/agent.py`:
  - `POST /api/v1/agent/chat` — agentic chat with tool use
  - `GET /api/v1/agent/tools` — list available tools for current user's role
  - `GET /api/v1/agent/sessions/{id}` — retrieve agent session history with tool calls
- [ ] Create `backend/app/schemas/agent.py` — `AgentRequest`, `AgentResponse`, `ToolCall`, `ToolResult`
- [ ] Write `backend/tests/test_agent.py` — test tool permissions, guardrails, agent flow (8+ tests)

#### Deliverables

| Deliverable | Path |
|---|---|
| Agent Tools | `backend/app/agents/tools.py` |
| Permission Matrix | `backend/app/agents/permissions.py` |
| Banking Agent (LangGraph) | `backend/app/agents/banking_agent.py` |
| Guardrails | `backend/app/agents/guardrails.py` |
| Agent API | `backend/app/api/routes/agent.py` |
| Agent Schemas | `backend/app/schemas/agent.py` |
| Agent Tests | `backend/tests/test_agent.py` |

#### Acceptance Criteria

1. `POST /api/v1/agent/chat` with `"What is the balance for account 1001?"` triggers `get_account_balance` tool and returns the balance
2. A `customer_service` user cannot invoke `create_workflow` tool without operational escalation (agent enforces permission boundary)
3. An `admin` user can invoke all tools
4. Agent stops after max 10 iterations even if not converged
5. `GET /api/v1/agent/tools` returns only tools permitted for the authenticated user's role
6. Tool parameters are sanitized before execution
7. All agent tests pass

---

### Phase 9: Workflow & Human-in-the-Loop

| Attribute | Value |
|---|---|
| **Complexity** | **L** (Large) |
| **Dependencies** | Phase 8 (Agent can create workflows), Phase 3 (RBAC for approval routing) |
| **Risk Factors** | State machine complexity; concurrent approval race conditions; notification delivery |

#### Objectives

- Build a workflow engine for operations requiring human approval
- Implement approval chains: AI recommends → human reviews → human decides
- Create workflow types for common banking operations (account opening, large transfers, KYC review)
- Track full audit trail of workflow decisions

#### Tasks

- [ ] Create `backend/app/services/workflow_service.py`:
  - Create workflow instance with type, payload, AI recommendation
  - Assign to appropriate role based on workflow type
  - State transitions: `pending` → `in_review` → `approved`/`rejected`/`escalated`
  - Escalation rules (auto-escalate if not actioned within configurable time)
- [ ] Create `backend/app/models/workflow.py` — extend with:
  - `ai_recommendation` (text), `ai_confidence` (float), `ai_reasoning` (text)
  - `reviewer_notes` (text), `escalated_to` (FK to User)
- [ ] Create Alembic migration for workflow model changes
- [ ] Create `backend/app/api/routes/workflows.py`:
  - `GET /api/v1/workflows` — list workflows (filterable by status, type, assigned_to)
  - `GET /api/v1/workflows/{id}` — workflow detail with AI recommendation and history
  - `POST /api/v1/workflows` — create a new workflow (agent or manual)
  - `PUT /api/v1/workflows/{id}/review` — claim a workflow for review
  - `PUT /api/v1/workflows/{id}/decide` — approve/reject with reviewer notes
  - `PUT /api/v1/workflows/{id}/escalate` — escalate to higher authority
- [ ] Create `backend/app/schemas/workflow.py` — `WorkflowCreate`, `WorkflowResponse`, `WorkflowDecision`
- [ ] Define workflow types with routing rules across canonical roles:
  - `account_opening` → assigned to `branch_manager`
  - `large_transfer` (> 100,000 EGP) → assigned to `branch_manager`, escalated to `admin`
  - `kyc_review` → assigned to `compliance_reviewer`
  - `dispute_resolution` → assigned to `operations_officer`, escalated to `branch_manager`
- [ ] Integrate with agent: agent calls `create_workflow` tool → workflow appears in `branch_manager` or `operations_officer` queue
- [ ] Create `backend/app/services/notification_service.py` — in-app notification for new/escalated workflows
- [ ] Write `backend/tests/test_workflows.py` — test create, claim, decide, escalate, permission checks (8+ tests)

#### Deliverables

| Deliverable | Path |
|---|---|
| Workflow Service | `backend/app/services/workflow_service.py` |
| Workflow API | `backend/app/api/routes/workflows.py` |
| Workflow Schemas | `backend/app/schemas/workflow.py` |
| Notification Service | `backend/app/services/notification_service.py` |
| Workflow Migration | `backend/alembic/versions/002_workflow_enhancements.py` |
| Workflow Tests | `backend/tests/test_workflows.py` |

#### Acceptance Criteria

1. `POST /api/v1/workflows` creates a workflow with status `pending` and AI recommendation attached
2. `PUT /api/v1/workflows/{id}/review` changes status to `in_review` and sets reviewer
3. `PUT /api/v1/workflows/{id}/decide` with `{"decision": "approved"}` changes status to `approved`
4. Only `branch_manager` or `admin` can decide on `account_opening` workflows (403 for others)
5. Escalation changes `assigned_to` to a user with a higher role
6. Workflow history shows full state transition timeline
7. All workflow tests pass

---

### Phase 10: Dual-Portal Frontend & Egyptian Banking Experience

| Attribute | Value |
|---|---|
| **Complexity** | **XL** (Extra Large) |
| **Dependencies** | Phases 3-9 (All backend APIs must be functional) |
| **Risk Factors** | State management complexity; RTL/LTR layout transitions; separate portal context boundaries; SSE integration for streaming |

#### Objectives

- Build a dual-portal banking frontend for **NileOps Demo Bank** in React 18 + TypeScript + Vite + Tailwind CSS
- Deliver a dedicated **Customer Portal** (Arabic-first, RTL/LTR, conversational banking assistance, product guidance, complaint submission)
- Deliver a dedicated **Employee Portal** (Operations dashboard, AI copilot, customer 360, KYC review, policy approval, workflow management)
- Embody authentic Egyptian digital banking conventions (EGP currency formatting, localized terminology, Egyptian date/phone conventions) while preserving strict fictional IP boundaries

#### Tasks

- [ ] Create `frontend/src/lib/api.ts` — Axios instance with JWT interceptor, refresh token logic, portal header injection (`X-Portal-Source`)
- [ ] Create `frontend/src/contexts/AuthContext.tsx` — authentication state, role-based claims, portal switching
- [ ] Create `frontend/src/contexts/LanguageContext.tsx` — Arabic/English language toggle, RTL/LTR direction switching (`dir="rtl"`)
- [ ] **Customer Portal UI (`frontend/src/portals/customer/`):**
  - `CustomerLayout.tsx` — localized header, language toggle (AR/EN), quick actions
  - `CustomerChatPage.tsx` — NileOps Demo Bank digital assistant (Egyptian Arabic / English conversational support, policy RAG, product guidance, complaint initiation)
  - `CustomerProductsPage.tsx` — synthetic accounts, certificates, cards, loan calculators
  - `CustomerAccountSummary.tsx` — authenticated customer view of balances and transaction history
  - `ComplaintSubmissionModal.tsx` — simulated complaint intake routing to workflow engine
- [ ] **Employee Portal UI (`frontend/src/portals/employee/`):**
  - `EmployeeLayout.tsx` — sidebar navigation, role-based menu items, alert badges
  - `DashboardPage.tsx` — overview metrics (pending KYC, workflow SLA alerts, active RAG queries)
  - `CopilotChatPage.tsx` — employee AI copilot with policy citations and controlled customer lookup tools
  - `CustomersPage.tsx` & `CustomerDetailPage.tsx` — searchable customer 360 view
  - `DocumentsPage.tsx` — document upload, PaddleOCR inspection, validation correction interface
  - `PolicyGovernancePage.tsx` — KB document upload, approval queue (`DRAFT → APPROVED`), version history
  - `WorkflowsPage.tsx` & `WorkflowDetailPage.tsx` — pending queues, approve/reject/escalate actions
- [ ] Create shared components (`frontend/src/components/shared/`): `DataTable`, `StatusBadge`, `ConfirmDialog`, `FileUpload`, `LoadingSpinner`, `EGPFormatter`, `RAGFeedbackWidget`
- [ ] Implement React Router with separate portal route trees and strict role/portal authorization checks

#### Deliverables

| Deliverable | Path |
|---|---|
| API Client & Contexts | `frontend/src/lib/api.ts`, `frontend/src/contexts/` |
| Customer Portal | `frontend/src/portals/customer/*.tsx` |
| Employee Portal | `frontend/src/portals/employee/*.tsx` |
| Shared Components | `frontend/src/components/shared/` |
| Routing Config | `frontend/src/App.tsx` |

#### Acceptance Criteria

1. Both Customer Portal and Employee Portal render with live backend integration under proper route protection
2. Language toggle flips UI direction seamlessly between LTR (English) and RTL (Arabic) with correct typography
3. Customer Portal provides grounded banking policy answers without exposing employee tools or internal metadata
4. Employee Portal enables authorized customer lookup, policy document approval, and workflow decisions
5. All monetary amounts format in Egyptian Pounds (`EGP` / `ج.م`) with localized decimal/thousand separators
6. All pages are responsive across tablet (1024px) and desktop (1440px) breakpoints

---

### Phase 11: Analytics & Audit Trail

| Attribute | Value |
|---|---|
| **Complexity** | **M** (Medium) |
| **Dependencies** | Phase 10 (Frontend for visualization), Phase 4 (Transaction data), Phase 9 (Workflow data) |
| **Risk Factors** | Query performance on large audit logs; chart library rendering performance |

#### Objectives

- Build comprehensive audit logging for all system actions
- Create analytics dashboards with banking KPIs
- Implement exportable reports for compliance
- Visualize AI decision patterns and accuracy

#### Tasks

- [ ] Create `backend/app/middleware/audit_middleware.py` — FastAPI middleware logging every API call to `AuditLog` table
- [ ] Create `backend/app/services/audit_service.py` — query audit logs with filtering (user, action, entity, date range)
- [ ] Create `backend/app/api/routes/audit.py`:
  - `GET /api/v1/audit` — paginated audit log (admin/auditor only)
  - `GET /api/v1/audit/export` — CSV export of audit logs
- [ ] Create `backend/app/services/analytics_service.py` — aggregate queries:
  - Transaction volume by day/week/month
  - Workflow approval/rejection rates
  - Average workflow processing time
  - Document processing success rate
  - AI recommendation accuracy (approved recommendations / total)
- [ ] Create `backend/app/api/routes/analytics.py`:
  - `GET /api/v1/analytics/transactions` — transaction volume chart data
  - `GET /api/v1/analytics/workflows` — workflow metrics
  - `GET /api/v1/analytics/ai-accuracy` — AI recommendation accuracy
  - `GET /api/v1/analytics/overview` — combined dashboard metrics
- [ ] Create `backend/app/schemas/analytics.py` — `AnalyticsOverview`, `ChartDataPoint`, `AuditLogEntry`
- [ ] Update `frontend/src/pages/AnalyticsPage.tsx` — render charts using Recharts:
  - Line chart: transaction volume over time
  - Bar chart: workflow decisions by type
  - Pie chart: document types processed
  - KPI cards: total customers, active accounts, pending workflows, AI accuracy %
- [ ] Create `frontend/src/pages/AuditPage.tsx` — searchable audit log table with export button
- [ ] Write `backend/tests/test_analytics.py` — test aggregation queries, audit log creation (6+ tests)

#### Deliverables

| Deliverable | Path |
|---|---|
| Audit Middleware | `backend/app/middleware/audit_middleware.py` |
| Audit Service + API | `backend/app/services/audit_service.py`, `backend/app/api/routes/audit.py` |
| Analytics Service + API | `backend/app/services/analytics_service.py`, `backend/app/api/routes/analytics.py` |
| Analytics Frontend | `frontend/src/pages/AnalyticsPage.tsx` |
| Audit Frontend | `frontend/src/pages/AuditPage.tsx` |
| Analytics Tests | `backend/tests/test_analytics.py` |

#### Acceptance Criteria

1. Every API call generates an audit log entry with user, action, entity, timestamp, and IP
2. `GET /api/v1/audit?user_id=1&action=login` returns filtered audit entries
3. `GET /api/v1/audit/export` returns a valid CSV file
4. `GET /api/v1/analytics/overview` returns all KPI metrics in a single response
5. Analytics page renders at least 3 different chart types with real backend data
6. Audit page is accessible only to `admin` and `compliance_reviewer` roles (403 for others)
7. All analytics tests pass

---

### Phase 12: Testing, Security Review & RAG Evaluation

| Attribute | Value |
|---|---|
| **Complexity** | **XL** (Extra Large) |
| **Dependencies** | Phases 0–11 (All platform services and both portals implemented) |
| **Risk Factors** | Subjective LLM evaluation; Arabic dialectal variance; prompt injection edge cases; latency bottlenecks on local inference |

#### Objectives

- Achieve ≥80% code coverage across backend and frontend modules
- Perform thorough application security audit and vulnerability remediation
- Implement an enterprise RAG evaluation framework measuring retrieval, generation, safety, and bilingual performance
- Load test critical customer and employee endpoints under concurrent simulation

#### Tasks

- [ ] Create `backend/tests/conftest.py` — shared fixtures: test database, authenticated client, role seed data
- [ ] Achieve ≥80% code coverage: run `pytest --cov=app --cov-report=html backend/tests/`
- [ ] Write integration tests: `backend/tests/test_integration.py` — end-to-end user journeys (login → customer lookup → document upload → OCR validation → policy RAG query → workflow escalation → approval decision)
- [ ] Create `backend/tests/test_security.py`:
  - SQL injection attempts on search endpoints (ORM parameterization validation)
  - XSS payload handling in text fields
  - JWT tampering and role-spoofing detection
  - CORS configuration validation (restricted origins)
  - Rate limiting verification on raw OCR endpoints and authentication routes
  - Cross-customer data leakage tests: assert Customer A cannot retrieve Customer B's accounts or documents
- [ ] **Enterprise RAG Evaluation Suite (`backend/tests/test_rag_evaluation.py`):**
  - **Synthetic Benchmark Dataset:** Define 50 bilingual ground-truth Q&A pairs (25 Arabic, 25 English) based strictly on synthetic **NileOps Demo Bank** policies:
    - 30 standard factual policy inquiries with ground-truth chunk citations
    - 10 ungrounded / out-of-scope inquiries to test abstention
    - 10 complex queries containing dialectal Egyptian banking phrasing (e.g., *شهادات بعائد شهري*, *شروط فتح حساب جاري*, *حدود السحب من إنستاباي*)
  - **Retrieval Metrics Harness:**
    - Measure **Recall@3** and **Recall@5** against ground-truth chunk IDs
    - Compute **Mean Reciprocal Rank (MRR)** for ranked search results
    - Evaluate **Context Precision** (proportion of retrieved context relevant to query)
  - **Generation Metrics Harness:**
    - **Answer Faithfulness (Groundedness):** Verify 100% of factual statements in LLM response are supported by retrieved context (detect hallucinations)
    - **Answer Relevance:** Measure semantic similarity between user query and generated answer
    - **Citation Correctness:** Assert that every emitted citation matches an actual retrieved, approved policy document version and section
  - **Safety & Guardrails Testing:**
    - **Abstention Accuracy:** Assert the assistant reliably emits standard refusal ("Based on available policies...") for the 10 ungrounded queries
    - **Prompt Injection Defense:** Test 10 adversarial inputs attempting system prompt extraction, jailbreaking, or tool escalation
  - **Performance Benchmarking:** Measure token generation throughput (tokens/sec) and latency across streaming responses
- [ ] Security review checklist:
  - [ ] No hardcoded secrets or credentials in source code
  - [ ] All endpoints require authentication (except `/health` and `/api/v1/auth/login`)
  - [ ] Dual-portal context boundary enforced (Customer Portal cannot invoke employee tools or view internal policies)
  - [ ] Raw OCR candidate strings accessible strictly through JIT audit-logged endpoints
- [ ] Create `backend/tests/test_load.py` — load test: 50 concurrent requests to `/api/v1/customers` and 20 concurrent streaming chat requests using `httpx.AsyncClient`
- [ ] Generate evaluation summary reports (code coverage HTML and RAG evaluation metrics JSON)

#### Deliverables

| Deliverable | Path |
|---|---|
| Test Configuration | `backend/tests/conftest.py` |
| Integration Tests | `backend/tests/test_integration.py` |
| Security Tests | `backend/tests/test_security.py` |
| RAG Evaluation Suite | `backend/tests/test_rag_evaluation.py` |
| Benchmark Dataset | `backend/tests/fixtures/rag_evaluation_dataset.json` |
| Load Tests | `backend/tests/test_load.py` |
| Evaluation Reports | `backend/htmlcov/index.html`, `backend/reports/rag_benchmark.json` |

#### Acceptance Criteria

1. `pytest backend/tests/ --cov=app` reports ≥80% line coverage
2. All integration tests pass end-to-end
3. Zero critical security vulnerabilities (no SQL injection, no XSS, no customer data leakage)
4. RAG Retrieval: Recall@5 ≥ 0.85 and MRR ≥ 0.75 across the synthetic benchmark dataset
5. RAG Generation: Answer Faithfulness ≥ 0.90 (no unsupported factual claims)
6. RAG Safety: 100% of out-of-scope/ungrounded test queries trigger proper abstention
7. Prompt Injection: 100% of adversarial jailbreak attempts are blocked by guardrails
8. Load test: 50 concurrent requests complete without errors, p95 latency < 2 seconds (excluding local LLM streaming generation)

---

### Phase 13: Dockerization & Deployment Preparation

| Attribute | Value |
|---|---|
| **Complexity** | **L** (Large) |
| **Dependencies** | Phase 12 (All tests pass before containerizing) |
| **Risk Factors** | Docker image size (PaddleOCR + models); multi-stage build complexity; container networking; Ollama accessibility from container |

#### Objectives

- Containerize all application services
- Create a single `docker compose up` command to start the entire platform
- Optimize image sizes with multi-stage builds
- Configure production-like settings (non-debug, proper logging, health checks)

#### Tasks

- [ ] Create `backend/Dockerfile`:
  - Multi-stage build: builder (install deps) → runtime (copy app)
  - Base image: `python:3.11-slim`
  - Install system dependencies for PaddleOCR (libgl1, libglib2.0)
  - Copy only necessary files (use `.dockerignore`)
  - Health check: `CMD curl -f http://localhost:8000/health || exit 1`
- [ ] Create `frontend/Dockerfile`:
  - Multi-stage build: builder (npm build) → runtime (nginx serving static files)
  - Base image: `node:20-alpine` (build), `nginx:alpine` (runtime)
  - Copy `nginx.conf` with API proxy configuration
- [ ] Create `frontend/nginx.conf` — serve SPA with `/api/` proxy to backend
- [ ] Update `docker-compose.yml` to include all services:
  - `postgres` — PostgreSQL 16 with volume persistence
  - `qdrant` — Qdrant with volume persistence
  - `backend` — FastAPI app with dependency on postgres + qdrant
  - `frontend` — Nginx serving React build with proxy
  - Health checks and restart policies on all services
- [ ] Create `docker-compose.override.yml` — development overrides (volume mounts, debug mode)
- [ ] Create `backend/.dockerignore` — exclude `.venv`, `__pycache__`, `tests/`, `.env`
- [ ] Create `frontend/.dockerignore` — exclude `node_modules/`, `.env`
- [ ] Create `scripts/start.sh` (or `start.ps1`) — orchestration script:
  - Check Docker is running
  - Build images
  - Start services
  - Wait for health checks
  - Run migrations
  - Seed database
  - Print access URLs
- [ ] Test full stack: `docker compose up --build -d` → verify all services healthy
- [ ] Document required host configuration: Ollama must run on host with `OLLAMA_HOST=0.0.0.0`

#### Deliverables

| Deliverable | Path |
|---|---|
| Backend Dockerfile | `backend/Dockerfile` |
| Frontend Dockerfile | `frontend/Dockerfile` |
| Nginx Config | `frontend/nginx.conf` |
| Full Docker Compose | `docker-compose.yml` |
| Dev Overrides | `docker-compose.override.yml` |
| Start Script | `scripts/start.ps1` |
| Docker Ignore Files | `backend/.dockerignore`, `frontend/.dockerignore` |

#### Acceptance Criteria

1. `docker compose up --build -d` starts all 4 services without errors
2. `docker compose ps` shows all services as `healthy`
3. Frontend is accessible at `http://localhost:3000`
4. Backend API is accessible at `http://localhost:8000/health`
5. Backend can connect to Ollama on host machine for LLM queries
6. Database data persists across `docker compose down` and `docker compose up` (volume mounts)
7. Backend Docker image is < 2GB; frontend image is < 50MB
8. `docker compose down -v` cleanly removes all containers and volumes

---

### Phase 14: Documentation, Screenshots, Demo Scenarios & GitHub Preparation

| Attribute | Value |
|---|---|
| **Complexity** | **M** (Medium) |
| **Dependencies** | Phase 13 (Fully working containerized application) |
| **Risk Factors** | Screenshots becoming stale if UI changes; demo data inconsistency; README length vs. readability |

#### Objectives

- Create portfolio-grade project documentation
- Capture screenshots of every major feature
- Design and document demo scenarios that showcase the platform
- Prepare the GitHub repository for public presentation

#### Tasks

- [ ] Create `README.md` at project root:
  - Project title, badges, one-paragraph description
  - Feature highlights with screenshots
  - Architecture diagram (Mermaid)
  - Tech stack table
  - Quick start guide (3 commands: clone, docker compose up, open browser)
  - API documentation link
  - Project structure tree
  - Contributing guidelines
  - License (MIT)
- [ ] Capture screenshots (save to `docs/screenshots/`):
  - `login.png` — login page
  - `dashboard.png` — main dashboard with charts
  - `customers.png` — customer list with search
  - `customer-detail.png` — customer detail page
  - `document-upload.png` — document upload interface
  - `ocr-results.png` — OCR extracted text display
  - `chat.png` — AI chat with streaming response
  - `agent-tools.png` — agent chat showing tool calls
  - `workflows.png` — workflow queue
  - `workflow-approval.png` — workflow detail with approve/reject
  - `analytics.png` — analytics dashboard
  - `audit-log.png` — audit trail
- [ ] Create `docs/DEMO_SCENARIOS.md` — step-by-step demo scripts:
  - **Scenario 1**: New Customer Onboarding (upload ID → OCR → create customer → AI KYC review → workflow approval)
  - **Scenario 2**: AI-Assisted Customer Inquiry (chat query → RAG retrieval → agent tool calls → answer)
  - **Scenario 3**: Transaction Dispute (lookup transaction → AI analysis → create workflow → human decision)
  - **Scenario 4**: Document Processing Pipeline (upload statement → OCR → data extraction → customer linking)
  - **Scenario 5**: Compliance Audit (view audit trail → filter by user → export report)
- [ ] Create `docs/API_DOCS.md` — complete API reference with curl examples for every endpoint
- [ ] Create `.github/README.md` or update root README with GitHub-specific presentation
- [ ] Create `LICENSE` file (MIT License)
- [ ] Create `.github/CONTRIBUTING.md` — contribution guidelines
- [ ] Review and clean up all code: remove debug prints, TODO comments, unused imports
- [ ] Verify `git log` is clean with meaningful commit messages
- [ ] Create GitHub release tag `v1.0.0`

#### Deliverables

| Deliverable | Path |
|---|---|
| Project README | `README.md` |
| Screenshots | `docs/screenshots/*.png` |
| Demo Scenarios | `docs/DEMO_SCENARIOS.md` |
| API Documentation | `docs/API_DOCS.md` |
| License | `LICENSE` |
| Contributing Guide | `.github/CONTRIBUTING.md` |

#### Acceptance Criteria

1. `README.md` renders correctly on GitHub with all images displayed
2. All 12 screenshots exist and show the actual running application (not mockups)
3. Each demo scenario is executable end-to-end following the documented steps
4. API documentation covers every endpoint with request/response examples
5. `LICENSE` file contains valid MIT license text
6. No `TODO`, `FIXME`, or `console.log` statements in production code
7. Repository is clean: no `.env` files, no `node_modules/`, no `__pycache__/` committed

---

## 4. Phase Dependencies

```mermaid
flowchart TD
    P0["Phase 0\nRequirements &\nArchitecture"]
    P1["Phase 1\nScaffolding &\nDev Environment"]
    P2["Phase 2\nDatabase Schema &\nSynthetic Data"]
    P3["Phase 3\nAuthentication\n& RBAC"]
    P4["Phase 4\nFastAPI\nServices"]
    P5["Phase 5\nOCR & Document\nIntelligence"]
    P6["Phase 6\nKnowledge Base\n& RAG"]
    P7["Phase 7\nQwen LLM\nIntegration"]
    P8["Phase 8\nAgentic AI &\nTool Permissions"]
    P9["Phase 9\nWorkflow &\nHuman-in-the-Loop"]
    P10["Phase 10\nFrontend &\nDashboard"]
    P11["Phase 11\nAnalytics &\nAudit Trail"]
    P12["Phase 12\nTesting &\nSecurity Review"]
    P13["Phase 13\nDockerization &\nDeployment"]
    P14["Phase 14\nDocumentation &\nGitHub Prep"]

    P0 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P4 --> P6
    P6 --> P7
    P5 --> P8
    P7 --> P8
    P8 --> P9
    P3 --> P9
    P4 --> P10
    P5 --> P10
    P7 --> P10
    P9 --> P10
    P10 --> P11
    P4 --> P11
    P11 --> P12
    P12 --> P13
    P13 --> P14

    style P0 fill:#2563eb,stroke:#1e40af,color:#ffffff
    style P1 fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style P2 fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style P3 fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style P4 fill:#059669,stroke:#047857,color:#ffffff
    style P5 fill:#d97706,stroke:#b45309,color:#ffffff
    style P6 fill:#d97706,stroke:#b45309,color:#ffffff
    style P7 fill:#d97706,stroke:#b45309,color:#ffffff
    style P8 fill:#dc2626,stroke:#b91c1c,color:#ffffff
    style P9 fill:#dc2626,stroke:#b91c1c,color:#ffffff
    style P10 fill:#dc2626,stroke:#b91c1c,color:#ffffff
    style P11 fill:#059669,stroke:#047857,color:#ffffff
    style P12 fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style P13 fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style P14 fill:#059669,stroke:#047857,color:#ffffff
```

**Legend:**
- 🔵 Blue — Architecture & Planning
- 🟣 Purple — Infrastructure & Setup
- 🟢 Green — Standard Development
- 🟠 Orange — AI/ML Components
- 🔴 Red — Complex Integration

---

## 5. Critical Path

The **critical path** is the longest chain of dependent phases that determines the minimum project duration. Any delay on a critical path phase directly delays the entire project.

```
P0 → P1 → P2 → P3 → P4 → P5 → P8 → P9 → P10 → P11 → P12 → P13 → P14
```

| Segment | Critical Path Reason |
|---|---|
| **P0 → P1 → P2 → P3** | Linear infrastructure chain — each builds on the previous |
| **P3 → P4** | All CRUD APIs need auth; cannot parallelize |
| **P4 → P5** | Document API follows CRUD patterns established in P4 |
| **P5 + P7 → P8** | Agent needs both OCR tools and LLM — P5 is on critical path as it blocks P8 |
| **P8 → P9** | Workflows are triggered by agents |
| **P9 → P10** | Frontend needs all backend APIs including workflows |
| **P10 → P11** | Analytics UI requires frontend framework |
| **P11 → P12 → P13 → P14** | Linear testing → deployment → documentation chain |

### Parallelization Opportunities

> [!TIP]
> These phases can be worked on in parallel to reduce total project duration:

| Parallel Group | Phases | Condition |
|---|---|---|
| **AI Pipeline** | Phase 5 (OCR) ∥ Phase 6 (RAG) | Both depend on Phase 4; independent of each other |
| **LLM + Agent** | Phase 7 depends on P6 only; P5 + P7 unblock P8 | Start P7 as soon as P6 completes; P5 can finish later |
| **KB Content** | Knowledge base markdown files (part of P6) | Can be written anytime after P0 |

---

## 6. Quality Gates

Each quality gate must pass before proceeding to the next phase. The gate review is a self-assessment checkpoint.

| Gate | Between Phases | Gate Criteria |
|---|---|---|
| **G0: Architecture Complete** | P0 → P1 | All 8 Phase 0 docs exist, are consistent, and reviewed |
| **G1: Dev Environment Ready** | P1 → P2 | Docker services running; health check passes; linting clean |
| **G2: Data Layer Stable** | P2 → P3 | Migrations run cleanly; seed data loads; all FK relationships valid |
| **G3: Auth Functional** | P3 → P4 | Login/logout works; RBAC enforced; 8+ auth tests pass |
| **G4: API Complete** | P4 → P5/P6 | All CRUD endpoints tested; pagination works; error handling consistent |
| **G5: OCR Functional** | P5 → P8 | Document upload + OCR extraction works end-to-end; 6+ tests pass |
| **G6: RAG Functional** | P6 → P7 | KB ingested into Qdrant; semantic search returns relevant results |
| **G7: LLM Integrated** | P7 → P8 | Chat endpoint returns coherent answers with RAG context; streaming works |
| **G8: Agent Operational** | P8 → P9 | Agent executes tools correctly; permissions enforced; 8+ tests pass |
| **G9: HITL Complete** | P9 → P10 | Workflow lifecycle works end-to-end; approval/rejection tested |
| **G10: UI Complete** | P10 → P11 | All pages render with live data; chat streaming works; responsive layout |
| **G11: Analytics Live** | P11 → P12 | Audit logs captured; analytics charts render; export works |
| **G12: Quality Assured** | P12 → P13 | ≥80% coverage; zero critical security issues; LLM evaluation passing |
| **G13: Deployable** | P13 → P14 | `docker compose up` starts full stack; all services healthy |
| **G14: Portfolio Ready** | P14 → Done | README complete; screenshots captured; demo scenarios validated |

---

## 7. Definition of Done

### Per-Phase Definition of Done

Every phase is considered **Done** when ALL of the following are satisfied:

| # | Criterion | Verification Method |
|---|---|---|
| 1 | All tasks in the phase checklist are completed | Manual review of this document |
| 2 | All deliverable files exist at their specified paths | `ls` / file system check |
| 3 | All acceptance criteria pass | Manual or automated testing |
| 4 | All new code passes linting (`ruff check`, `npm run lint`) | CLI output: 0 errors |
| 5 | All phase-specific tests pass (`pytest`, `vitest`) | CLI output: all green |
| 6 | No regressions: all previous phase tests still pass | `pytest backend/tests/` (full suite) |
| 7 | Code is committed with descriptive message | `git log --oneline` |
| 8 | Quality gate for the phase passes | See Quality Gates table |

### Project-Level Definition of Done

The entire NileOps V4 project is **Done** when:

- [ ] All 15 phases (0–14) meet their per-phase Definition of Done
- [ ] `docker compose up` starts the full platform from a clean state
- [ ] All 5 demo scenarios execute successfully end-to-end
- [ ] Test coverage ≥80% across backend
- [ ] Zero known critical bugs
- [ ] README renders correctly on GitHub with screenshots
- [ ] Repository tagged as `v1.0.0`

---

> [!NOTE]
> This roadmap is a living document. Update phase statuses and check off tasks as work progresses. If scope changes are needed, update the affected phases and re-evaluate the critical path.
