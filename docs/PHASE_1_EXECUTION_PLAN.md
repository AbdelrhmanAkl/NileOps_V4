# NileOps — Phase 1: Project Scaffolding & Development Environment Execution Plan

> **Document Version:** 1.0.0  
> **Date:** 2026-11-07  
> **Phase Target:** Phase 1 (Scaffolding & Dev Environment)  
> **Status:** Execution Ready (Pending Explicit User Authorization)  

---

## 1. Objectives

Phase 1 establishes the foundational monorepo structure, development environment configuration, Docker service containers, and automated health-check endpoints for NileOps without implementing business logic or database seed data.

Key objectives:
1. Initialize the monorepo directory tree for `backend/`, `frontend/`, `docker/`, and `tests/`.
2. Configure `.env.example` with complete configuration keys and zero committed secrets.
3. Establish Docker Compose specifications for PostgreSQL 16 and Qdrant.
4. Set up the minimal FastAPI application shell with an unauthenticated `/health` endpoint and CORS middleware.
5. Set up the React 18 + TypeScript + Vite + Tailwind CSS frontend application shell.
6. Initialize Git tracking with a hardened `.gitignore`.

---

## 2. Target Project Directory Structure

```
c:\AI\NileOps_V4\
├── .gitignore                          # Hardened Git ignore rules
├── .env.example                        # Template environment variables
├── README.md                           # Master repository documentation
├── docker-compose.yml                  # Local development container stack
│
├── docs/                               # Phase 0 & Phase 0.5 architectural documentation
│   ├── ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── SECURITY_REQUIREMENTS.md
│   ├── PROJECT_ASSESSMENT.md
│   ├── PHASE_0_5_ENGINEERING_REVIEW.md
│   └── PHASE_1_EXECUTION_PLAN.md
│
├── backend/                            # FastAPI Python Service
│   ├── pyproject.toml                  # Pinned dependencies & Ruff / MyPy configuration
│   ├── requirements.txt                # Static pip lockfile
│   ├── alembic.ini                     # Database migration configuration
│   ├── alembic/                        # Migration scripts directory
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application factory
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic BaseSettings
│   │   │   ├── security.py             # Password & JWT utilities
│   │   │   └── exceptions.py           # Standardized error classes
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # Async SQLAlchemy session factory
│   │   │   └── base.py                 # DeclarativeBase mixins
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                 # Auth & DB dependencies
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── router.py           # v1 aggregated router
│   │   ├── models/                     # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/                    # Pydantic v2 schemas
│   │   └── services/                   # Business domain services
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_health.py              # Initial health-check test
│   └── uploads/                        # Isolated local upload directory (.gitignored)
│
└── frontend/                           # React 18 SPA (Dual-Portal: NileOps Demo Bank)
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx                    # Entry point
        ├── App.tsx                     # Root router with dual-portal route trees
        ├── api/                        # Axios client with portal headers
        ├── components/                 # Shared UI components & design system
        ├── contexts/                   # AuthContext, LanguageContext (AR/EN RTL/LTR)
        ├── portals/                    # Dual-Portal Implementations
        │   ├── customer/               # Customer Portal (Retail Q&A, products, complaints)
        │   └── employee/               # Employee Portal (Staff copilot, KYC, workflows)
        └── types/                      # TypeScript definitions
```

---

## 3. Environment & Prerequisites

### 3.1 Host System Dependencies
- **Python:** 3.11.9 (Verified on PATH).
- **Node.js:** v20+ LTS (Required to scaffold `frontend/`).
- **Docker Desktop:** Required to execute PostgreSQL and Qdrant containers.
- **Ollama:** Verified running with local model `qwen3:8b`.

### 3.2 Environment Variable Configuration (`.env.example`)
```env
# Application Settings
ENVIRONMENT=development
DEBUG=true
PROJECT_NAME="NileOps Digital Banking Operations"
API_V1_PREFIX="/api/v1"

# Security & Authentication
SECRET_KEY=change-this-insecure-key-to-a-secure-256-bit-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Primary Database (PostgreSQL 16)
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nileops_app
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_DB=nileops_db
DATABASE_URL=postgresql+asyncpg://nileops_app:<POSTGRES_PASSWORD>@localhost:5432/nileops_db

# Vector Database (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_COLLECTION=nileops_kb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=dynamic  # Probed automatically at model startup (no fixed dimension assumed)

# AI / Ollama Inference
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Document Upload & Storage
UPLOAD_DIR=backend/uploads
MAX_UPLOAD_SIZE_BYTES=15728640  # 15 MB
```

---

## 4. Phase 1 Implementation Sequence

1. **Step 1: Version Control Initialization**
   - Create `.gitignore` ignoring virtualenvs (`.venv/`), node modules (`node_modules/`), compiled bytecode, `.env` files, uploads, and model binaries.
   - Initialize Git repository if not already established.

2. **Step 2: Backend Scaffolding**
   - Create `backend/` directory structure.
   - Create `backend/pyproject.toml` with pinned dependencies:
     - `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `pydantic-settings>=2.4.0`
     - `sqlalchemy[asyncio]>=2.0.30`, `asyncpg>=0.29.0`, `alembic>=1.13.0`
     - `python-jose[cryptography]>=3.3.0`, `passlib[bcrypt]>=1.7.4`, `python-multipart>=0.0.9`
     - `httpx>=0.27.0`, `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `ruff>=0.5.0`
   - Create virtual environment `backend/.venv` and install base dependencies.
   - Create `backend/app/main.py` with `/health` returning `{"status": "healthy", "service": "NileOps Backend", "version": "1.0.0"}`.

3. **Step 3: Docker Services Definition**
   - Create `docker-compose.yml` containing:
     - `postgres`: image `postgres:16-alpine`, ports `5432:5432`, healthcheck `pg_isready`.
     - `qdrant`: image `qdrant/qdrant:latest`, ports `6333:6333`, healthcheck via HTTP GET `/healthz`.

4. **Step 4: Frontend Scaffolding**
   - Run `npm create vite@latest frontend -- --template react-ts` (when Node.js is confirmed).
   - Configure Tailwind CSS, PostCSS, and create a basic banking navigation shell.

5. **Step 5: Verification & Quality Gate**
   - Run `pytest backend/tests/test_health.py` to confirm API availability.
   - Run `ruff check backend/` to ensure zero linter errors.

---

## 5. Phase 1 Acceptance Criteria

1. Project structure matches Section 2 exactly.
2. `docker-compose.yml` successfully provisions PostgreSQL 16 and Qdrant containers in healthy state.
3. `GET http://localhost:8000/health` returns `200 OK` with JSON health payload.
4. `.env.example` exists with all required keys and zero actual secrets.
5. `.gitignore` prevents leaks of `.venv`, `node_modules`, `.env`, and binary files.
6. Automated health test passes via `pytest`.
7. No database seed data or operational application code is created during Phase 1 (reserved for Phases 2–4).

---
*End of Phase 1 Execution Plan. Execution paused. Awaiting explicit user approval to proceed.*

