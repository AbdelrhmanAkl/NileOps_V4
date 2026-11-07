# NileOps — Intelligent Digital Banking Operations Platform

**Fictional Simulation Identity:** NileOps Demo Bank  
**Architecture:** Monorepo (FastAPI + React 18 / Vite / Tailwind + PostgreSQL 16 + Qdrant + Ollama)  
**Security Boundary:** Strictly Synthetic Data Only — No Real PII / No Real Banking Credentials

---

## 1. Project Overview

NileOps is an intelligent, bilingual (Arabic / English) digital banking operations simulation platform. It delivers:
- **Dual-Portal Architecture:**
  - **Customer Portal:** Retail banking assistance, product & service inquiries, simulated complaints, and loan/account calculators.
  - **Employee Portal:** Operations workspace, staff policy copilot, multi-role governance, and simulated KYC review workflows.
- **RAG Banking Knowledge Base:** 12 curated policy domains with dynamic embedding dimension discovery and four-eyes approval workflow.
- **National ID OCR & Document AI:** Synthetic validation pipeline operating strictly on artificial fixtures under `NATIONAL_ID_VALIDATION_SPEC.md`.

---

## 2. Directory Structure

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
│   ├── PHASE_1_EXECUTION_PLAN.md
│   └── NATIONAL_ID_VALIDATION_SPEC.md
│
├── backend/                            # FastAPI Python Service
│   ├── pyproject.toml                  # Dependencies & linter configuration
│   ├── requirements.txt                # Static pip lockfile
│   ├── alembic.ini                     # Database migration configuration
│   ├── alembic/                        # Migration scripts
│   ├── app/
│   │   ├── main.py                     # Application entry point (/health)
│   │   ├── core/                       # Configuration, security, exceptions
│   │   ├── db/                         # SQLAlchemy session & declarative base
│   │   ├── api/                        # API routes (v1 router)
│   │   ├── models/                     # Database models
│   │   ├── schemas/                    # Pydantic schemas
│   │   └── services/                   # Business domain services
│   ├── tests/                          # Automated backend tests
│   └── uploads/                        # Local file uploads (.gitignored)
│
├── frontend/                           # React 18 SPA (Dual-Portal: NileOps Demo Bank)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx                    # Application mount
│       ├── App.tsx                     # Dual-portal navigation shell
│       ├── api/                        # HTTP client
│       ├── components/                 # Shared UI components
│       ├── contexts/                   # Auth & Language contexts
│       ├── portals/
│       │   ├── customer/               # Customer Portal
│       │   └── employee/               # Employee Portal
│       └── types/                      # TypeScript definitions
│
├── docker/                             # Docker-related configurations
└── tests/                              # Global integration & end-to-end tests
```

---

## 3. Quickstart & Development

### Backend Setup
```bash
cd backend
python -m venv .venv
# Activate virtualenv:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_health.py
uvicorn app.main:app --reload --port 8000
```

### Docker Services
```bash
docker compose up -d
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Documentation Baseline
Full architectural, database, and security specifications are preserved in `docs/`.
All developments strictly follow Phase specifications without violating synthetic data boundaries.
