# NileOps — MVP Known Limitations & Deferred Items

> **Document Identifier:** `docs/MVP_KNOWN_LIMITATIONS.md`  
> **Project:** NileOps — Intelligent Digital Banking Operations Platform  
> **Simulation Identity:** NileOps Demo Bank  
> **Date:** 2026-11-08  
> **Sprint Type:** 2-Hour Rapid MVP Delivery (Native Windows Environment)

---

## 1. Architectural & Database Limitations

1. **Development Database Engine (SQLite):**
   - The MVP runs on **async SQLite** (`aiosqlite`) to guarantee zero-dependency execution on Windows without requiring Docker Desktop, WSL2, or a native PostgreSQL Windows service.
   - *Limitation:* SQLite uses file-level locking for writes; it is not suited for high-concurrency production workloads.
   - *Production Path:* All SQLAlchemy 2.0 ORM models use standard portable types (`String(36)` UUIDs, standard DateTime, portable text fields). Migration to PostgreSQL 16 requires only updating `DATABASE_URL` in `.env`.

2. **Vector Database & RAG Search (Deferred):**
   - Qdrant container orchestration and Ollama LLM embeddings were explicitly deferred for this rapid MVP sprint per project instructions.
   - *Current Implementation:* The Policy Knowledge Base uses case-insensitive multi-field database keyword search across `code`, `title_en`, `title_ar`, `content_en`, `content_ar`, and `domain`.
   - *Production Path:* Connect Qdrant vector collection `nileops_kb` and dynamic embedding model probing in Phase 6.

3. **OCR Engine & Document AI (Simulated):**
   - The KYC verification module runs in deterministic simulation mode using synthetic National ID fixtures.
   - *Current Implementation:* Pre-verified synthetic Egyptian National ID data is displayed and reviewed in the employee workspace.
   - *Production Path:* Integrate the full ONNX / PaddleOCR synthetic document pipeline defined in `NATIONAL_ID_VALIDATION_SPEC.md` in Phase 5.

---

## 2. Security Boundaries & Simulation Constraints

1. **Strictly Fictional Banking Simulation:**
   - **NileOps Demo Bank** is an entirely fictional simulation identity.
   - There are zero connections to Central Bank of Egypt clearing networks (ACH, RTGS), IPN/InstaPay APIs, core banking systems (e.g. Finacle, Temenos), or card schemes (Visa/Mastercard).
   - Real money transfers, actual card issuance, and automated financial decision-making are impossible by design.

2. **Synthetic Data Boundaries:**
   - 100% of accounts, names, national ID numbers, and transactions are artificial fixtures.
   - No real customer PII, real Egyptian national ID images, or live banking credentials exist or may be loaded into the workspace.

3. **Session Secret Key:**
   - The default development configuration uses a non-production `SECRET_KEY` template. In a production environment, this must be overridden by a cryptographically random 256-bit secret stored in a secure secret manager.

4. **Client-Side Token Storage:**
   - The MVP stores the session JWT in `localStorage` for rapid demonstration. For production deployment, session tokens should transition to secure `HttpOnly`, `SameSite=Strict`, `Secure` cookies with CSRF tokens.

---

## 3. Deferred Features Matrix

| Feature | MVP Status | Production Phase | Notes |
| :--- | :--- | :--- | :--- |
| **PostgreSQL 16 & Alembic Migrations** | Deferred | Phase 2 | SQLite used for native Windows execution; models are 100% portable. |
| **Vector Search & Embedding Generation** | Deferred | Phase 6 | Plain text keyword search implemented across 12 policy domains. |
| **Ollama LLM Agent Copilot** | Deferred | Phase 8 | Pre-canned bilingual FAQs and policy search provided in MVP. |
| **Physical OCR Document Parsing** | Deferred | Phase 5 | Synthetic KYC queue with deterministic inspection implemented. |
| **External Core Banking Integration** | Out of Scope | None (Simulation) | NileOps remains strictly an operational simulation platform. |

---
*End of MVP Known Limitations.*

