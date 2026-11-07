# NileOps — Architecture Document

> **Version:** 1.0.0  
> **Last Updated:** 2026-11-07  
> **Classification:** Internal — Engineering  
> **Status:** Living Document

---

## Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Component Architecture](#2-component-architecture)
- [3. Data Flow Diagrams](#3-data-flow-diagrams)
- [4. API Architecture](#4-api-architecture)
- [5. Database Architecture](#5-database-architecture)
- [6. Security Architecture](#6-security-architecture)
- [7. AI Architecture](#7-ai-architecture)
- [8. Deployment Architecture](#8-deployment-architecture)
- [9. Directory Structure](#9-directory-structure)
- [10. Integration Points](#10-integration-points)
- [11. Configuration Management](#11-configuration-management)
- [12. Scalability Considerations](#12-scalability-considerations)

---

## 1. System Overview

**NileOps** is an enterprise-grade, AI-powered digital banking operations platform designed to streamline core banking workflows through intelligent automation. The platform combines modern full-stack engineering with production-ready AI capabilities — including local LLM inference, document OCR intelligence, retrieval-augmented generation (RAG), and autonomous agentic operations — all within a secure, auditable, and compliance-ready architecture.

### Design Principles

| Principle | Implementation |
|---|---|
| **Privacy-First AI** | All LLM inference runs locally via Ollama — zero data leaves the network |
| **Human-in-the-Loop** | Critical AI decisions require explicit human approval before execution |
| **Auditability** | Immutable event trail for every state change across the platform |
| **Bilingual-Native** | Arabic and English support at every layer — UI, LLM, OCR, search |
| **Modularity** | Each domain is an independent service module with clean API boundaries |
| **Type Safety** | Pydantic models on the backend, TypeScript on the frontend |

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Client["Frontend Layer"]
        UI["React SPA<br/>TypeScript + Vite + Tailwind"]
    end

    subgraph Gateway["API Gateway Layer"]
        API["FastAPI Application<br/>REST API + WebSocket"]
        AUTH["Auth Middleware<br/>JWT + RBAC"]
        VALID["Request Validation<br/>Pydantic Models"]
    end

    subgraph Services["Service Layer"]
        DASH["Dashboard<br/>Service"]
        CUST["Customer<br/>Management"]
        DOC["Document<br/>Intelligence"]
        KB["Knowledge Base<br/>Service"]
        ASSIST["AI Assistant<br/>Service"]
        AGENT["AI Operations<br/>Agent"]
        WF["Workflow<br/>Engine"]
        HITL["Human-in-the-Loop<br/>Service"]
        AUDIT["Audit Trail<br/>Service"]
        ANALYTICS["Analytics &<br/>Reporting"]
    end

    subgraph AI["AI Layer"]
        LLM["Qwen3 8B<br/>via Ollama"]
        OCR["PaddleOCR<br/>+ OpenCV"]
        RAG["RAG Engine<br/>Embeddings + Retrieval"]
        LG["LangGraph<br/>Agent Runtime"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL<br/>Primary Database")]
        QD[("Qdrant<br/>Vector Database")]
        FS[("File Storage<br/>Documents & Media")]
    end

    UI <-->|"HTTPS / WSS"| API
    API --> AUTH
    AUTH --> VALID
    VALID --> Services

    DASH --> PG
    CUST --> PG
    DOC --> OCR
    DOC --> PG
    DOC --> FS
    KB --> RAG
    KB --> QD
    KB --> PG
    ASSIST --> LLM
    ASSIST --> RAG
    AGENT --> LG
    AGENT --> LLM
    LG -->|"Tool Calls"| Services
    WF --> PG
    WF --> HITL
    HITL --> PG
    AUDIT --> PG
    ANALYTICS --> PG

    RAG --> QD
    RAG --> LLM

    classDef frontend fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef gateway fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef service fill:#10b981,stroke:#047857,color:#fff
    classDef ai fill:#f59e0b,stroke:#b45309,color:#fff
    classDef data fill:#ef4444,stroke:#991b1b,color:#fff

    class UI frontend
    class API,AUTH,VALID gateway
    class DASH,CUST,DOC,KB,ASSIST,AGENT,WF,HITL,AUDIT,ANALYTICS service
    class LLM,OCR,RAG,LG ai
    class PG,QD,FS data
```

---

## 2. Component Architecture

### 2.1 Frontend Layer — React SPA

The frontend is a single-page application built with React 18, TypeScript, and Vite, styled with Tailwind CSS. It communicates exclusively through the REST API and WebSocket connections.

```mermaid
graph LR
    subgraph Frontend["React SPA"]
        Router["React Router v6<br/>Route Guards"]
        Pages["Page Components<br/>Dashboard, Customers, Docs..."]
        Shared["Shared Components<br/>Tables, Forms, Modals"]
        Hooks["Custom Hooks<br/>useAuth, useApi, useWebSocket"]
        Store["State Management<br/>React Query + Context"]
        API_Client["API Client<br/>Axios + Interceptors"]
        I18N["i18n Layer<br/>Arabic / English"]
    end

    Router --> Pages
    Pages --> Shared
    Pages --> Hooks
    Hooks --> Store
    Hooks --> API_Client
    API_Client -->|"HTTP/WS"| BackendAPI["FastAPI Backend"]
    Pages --> I18N

    classDef fe fill:#3b82f6,stroke:#1e40af,color:#fff
    class Router,Pages,Shared,Hooks,Store,API_Client,I18N fe
```

| Concern | Technology | Purpose |
|---|---|---|
| Build Tool | Vite | Fast HMR, optimized production builds |
| Styling | Tailwind CSS | Utility-first, consistent design system |
| Data Fetching | React Query (TanStack) | Server state caching, background refetch |
| Routing | React Router v6 | Nested routes, role-based guards |
| Forms | React Hook Form + Zod | Type-safe validation, performant forms |
| Internationalization | i18next | Bilingual Arabic/English with RTL support |
| HTTP Client | Axios | Request/response interceptors, JWT refresh |

### 2.2 API Gateway Layer — FastAPI

The FastAPI application serves as the single entry point for all client requests. It handles authentication, request validation, rate limiting, and route delegation to internal services.

```mermaid
graph TD
    REQ["Incoming Request"] --> CORS["CORS Middleware"]
    CORS --> RATE["Rate Limiter"]
    RATE --> JWT["JWT Authentication"]
    JWT --> RBAC["RBAC Authorization"]
    RBAC --> PYDANTIC["Pydantic Validation"]
    PYDANTIC --> ROUTER["API Router<br/>v1/"]
    ROUTER --> HANDLER["Route Handler"]
    HANDLER --> SERVICE["Service Layer"]
    SERVICE --> RESP["Response Serialization"]
    RESP --> LOG["Audit Logging Middleware"]
    LOG --> CLIENT["Client Response"]

    classDef mw fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef core fill:#6366f1,stroke:#3730a3,color:#fff
    class CORS,RATE,JWT,RBAC,LOG mw
    class PYDANTIC,ROUTER,HANDLER,SERVICE,RESP core
```

**Key design decisions:**

- **Versioned routes** — All endpoints scoped under `/api/v1/` to support future non-breaking upgrades
- **Dependency injection** — FastAPI `Depends()` for database sessions, auth context, and service instances
- **Async-first** — All I/O-bound handlers are `async def` with `asyncpg` and async HTTP clients
- **Structured error responses** — Consistent `ErrorResponse` schema across all failure modes

### 2.3 Service Layer — Business Logic

Each service module encapsulates a bounded domain context. Services are stateless, depend on repositories for data access, and emit audit events for state-changing operations.

| Service | Responsibility | Key Dependencies |
|---|---|---|
| `DashboardService` | Aggregate real-time statistics from database | PostgreSQL |
| `CustomerService` | CRUD for customers, KYC status management, account linking | PostgreSQL |
| `AccountService` | Account creation, balance queries, transaction history | PostgreSQL |
| `TransactionService` | Transaction recording, filtering, export | PostgreSQL |
| `LoanService` | Loan applications, approval workflows, repayment tracking | PostgreSQL, WorkflowEngine |
| `DocumentService` | Document upload, OCR dispatch, result storage | PaddleOCR, File Storage, PostgreSQL |
| `KnowledgeBaseService` | Document ingestion, versioning, semantic search | Qdrant, RAG Engine, PostgreSQL |
| `AssistantService` | Chat session management, LLM inference orchestration | Ollama (Qwen3), RAG Engine |
| `AgentService` | Tool-based task execution, approval queue management | LangGraph, LLM, Tool Registry |
| `WorkflowService` | State machine execution for banking processes | PostgreSQL, HITL Service |
| `HITLService` | Review queue management, approval/rejection handling | PostgreSQL, WebSocket |
| `AuditService` | Immutable event recording, trail querying | PostgreSQL |
| `AnalyticsService` | Report generation, metric aggregation, data export | PostgreSQL |

### 2.4 AI Layer

The AI layer comprises four subsystems that operate independently but compose together for intelligent banking operations.

```mermaid
graph TB
    subgraph LLM_Engine["LLM Inference Engine"]
        OLLAMA["Ollama Server"]
        QWEN["Qwen3 8B Model"]
        OLLAMA --> QWEN
    end

    subgraph RAG_Engine["RAG Pipeline"]
        EMBED["Embedding Model"]
        CHUNK["Document Chunker"]
        RETRIEVE["Retrieval Engine"]
        RERANK["Context Reranker"]
        CHUNK --> EMBED
        EMBED --> QDRANT_C["Qdrant Store"]
        RETRIEVE --> QDRANT_C
        RETRIEVE --> RERANK
        RERANK --> CONTEXT["Augmented Context"]
    end

    subgraph OCR_Engine["Document Intelligence"]
        PREPROCESS["Image Preprocessing<br/>OpenCV"]
        PADDLE["PaddleOCR Engine"]
        EXTRACT["Field Extractor"]
        CONFIDENCE["Confidence Scorer"]
        PREPROCESS --> PADDLE
        PADDLE --> EXTRACT
        EXTRACT --> CONFIDENCE
    end

    subgraph Agent_Runtime["Agent Runtime"]
        LANGGRAPH["LangGraph Orchestrator"]
        TOOL_REG["Tool Registry<br/>Strict Allowlist"]
        PLANNER["Task Planner"]
        EXECUTOR["Tool Executor"]
        APPROVAL["Approval Gate"]
        LANGGRAPH --> PLANNER
        PLANNER --> TOOL_REG
        TOOL_REG --> EXECUTOR
        EXECUTOR --> APPROVAL
    end

    CONTEXT --> QWEN
    CONFIDENCE --> EXTRACT
    PLANNER --> QWEN
    APPROVAL -->|"Human Approved"| EXECUTOR

    classDef llm fill:#f59e0b,stroke:#b45309,color:#fff
    classDef rag fill:#06b6d4,stroke:#0e7490,color:#fff
    classDef ocr fill:#ec4899,stroke:#be185d,color:#fff
    classDef agent fill:#84cc16,stroke:#4d7c0f,color:#fff

    class OLLAMA,QWEN llm
    class EMBED,CHUNK,RETRIEVE,RERANK,CONTEXT,QDRANT_C rag
    class PREPROCESS,PADDLE,EXTRACT,CONFIDENCE ocr
    class LANGGRAPH,TOOL_REG,PLANNER,EXECUTOR,APPROVAL agent
```

### 2.5 Data Layer

| Store | Technology | Purpose | Data Types |
|---|---|---|---|
| **Primary Database** | PostgreSQL 16 | Transactional data, relationships, audit trail | Customers, accounts, transactions, workflows, users, audit logs |
| **Vector Database** | Qdrant | Semantic similarity search for RAG | Document embeddings, metadata, collection management |
| **File Storage** | Local volume (Docker mount) | Binary document storage | Uploaded PDFs, images, OCR outputs, generated reports |

---

## 3. Data Flow Diagrams

### 3.1 Document OCR Processing Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant DocSvc as Document Service
    participant Store as File Storage
    participant OCR as PaddleOCR Engine
    participant DB as PostgreSQL

    User->>UI: Upload document (PDF/Image)
    UI->>API: POST /api/v1/documents/upload<br/>[multipart/form-data]
    API->>API: Validate file type & size
    API->>DocSvc: process_document(file, metadata)
    DocSvc->>Store: Save original file
    Store-->>DocSvc: file_path

    DocSvc->>DB: Create document record<br/>status=PROCESSING

    DocSvc->>OCR: extract_text(file_path)
    OCR->>OCR: Image preprocessing (OpenCV)<br/>Deskew, denoise, binarize
    OCR->>OCR: PaddleOCR text detection
    OCR->>OCR: PaddleOCR text recognition
    OCR-->>DocSvc: Raw OCR results + confidence scores

    DocSvc->>DocSvc: Field extraction<br/>(name, ID, dates, amounts)
    DocSvc->>DocSvc: Calculate aggregate confidence
    DocSvc->>DB: Update document record<br/>status=COMPLETED, extracted_fields, confidence

    alt Confidence < threshold
        DocSvc->>DB: Flag for human review<br/>status=NEEDS_REVIEW
        DocSvc-->>API: Response with review_required=true
    else Confidence >= threshold
        DocSvc-->>API: Response with extracted data
    end

    API-->>UI: Document processing result
    UI-->>User: Display extracted fields + confidence
```

### 3.2 RAG Query Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant KB as Knowledge Base Service
    participant Embed as Embedding Model
    participant Qdrant as Qdrant Vector DB
    participant LLM as Qwen3 8B (Ollama)
    participant DB as PostgreSQL

    User->>UI: Ask question about banking policy
    UI->>API: POST /api/v1/assistant/chat<br/>{message, session_id}
    API->>KB: semantic_search(query)

    KB->>Embed: Generate query embedding
    Embed-->>KB: query_vector [dynamic_dim]

    KB->>Qdrant: Search nearest neighbors<br/>top_k=5, score_threshold=0.7
    Qdrant-->>KB: Relevant document chunks + metadata

    KB->>KB: Rerank results by relevance
    KB->>KB: Build augmented context<br/>with source citations

    KB-->>API: Retrieved context + sources

    API->>LLM: Generate response<br/>{system_prompt, context, user_query}
    LLM-->>API: LLM response (streaming)

    API->>DB: Log interaction<br/>(query, sources, response, latency)

    API-->>UI: Streamed response + source documents
    UI-->>User: Display answer with citations
```

### 3.3 Agent Tool Execution Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant Agent as LangGraph Agent
    participant LLM as Qwen3 8B
    participant Tools as Tool Registry
    participant HITL as HITL Service
    participant Target as Target Service
    actor Reviewer

    User->>UI: "Open a savings account for customer C-1042"
    UI->>API: POST /api/v1/agent/execute<br/>{task_description}
    API->>Agent: execute_task(task)

    Agent->>LLM: Plan task execution<br/>{task, available_tools}
    LLM-->>Agent: Tool call plan:<br/>1. lookup_customer(C-1042)<br/>2. open_account(type=savings)

    loop For each planned tool call
        Agent->>Tools: Validate tool in allowlist
        Tools-->>Agent: Tool authorized ✓

        alt Tool requires approval
            Agent->>HITL: Request human approval<br/>{tool, params, justification}
            HITL->>UI: Push approval request (WebSocket)
            UI->>Reviewer: Display approval dialog
            Reviewer->>UI: Approve / Reject
            UI->>HITL: Submit decision
            HITL-->>Agent: Approval decision

            alt Rejected
                Agent-->>API: Task aborted by reviewer
                API-->>UI: Display rejection reason
            end
        end

        Agent->>Target: Execute tool call
        Target-->>Agent: Tool result
        Agent->>LLM: Process result, plan next step
    end

    Agent-->>API: Task complete + summary
    API-->>UI: Execution result + audit trail
    UI-->>User: Display outcome
```

### 3.4 Workflow State Transitions

```mermaid
stateDiagram-v2
    [*] --> Initiated: Customer/Agent submits request

    state "KYC Verification Workflow" as KYC {
        Initiated --> DocumentUpload: Collect documents
        DocumentUpload --> OCRProcessing: Documents received
        OCRProcessing --> AutoVerification: OCR complete
        AutoVerification --> HumanReview: Low confidence / Mismatch
        AutoVerification --> Approved: All checks passed
        HumanReview --> Approved: Reviewer approves
        HumanReview --> Rejected: Reviewer rejects
        Rejected --> DocumentUpload: Customer resubmits
    }

    state "Account Opening Workflow" as AccOpen {
        Initiated --> KYCCheck: Validate KYC status
        KYCCheck --> AccountCreation: KYC verified
        KYCCheck --> KYCRequired: KYC not verified
        KYCRequired --> KYCCheck: KYC completed
        AccountCreation --> ComplianceReview: Account configured
        ComplianceReview --> Approved: Compliance cleared
        ComplianceReview --> Rejected: Compliance failed
    }

    Approved --> [*]
    Rejected --> [*]
```

> [!NOTE]
> All four workflows (KYC Verification, Account Opening, Card Request, Complaints) follow the same state machine pattern with domain-specific states. Each transition emits an audit event and may trigger notifications.

### 3.5 Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Gateway
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>UI: Enter credentials
    UI->>API: POST /api/v1/auth/login<br/>{username, password}
    API->>Auth: authenticate(credentials)
    Auth->>DB: Fetch user by username
    DB-->>Auth: User record + hashed password

    Auth->>Auth: Verify password (bcrypt)

    alt Invalid credentials
        Auth-->>API: AuthenticationError
        API-->>UI: 401 Unauthorized
    end

    Auth->>Auth: Generate JWT access token (15m)
    Auth->>Auth: Generate refresh token (7d)
    Auth->>DB: Store refresh token hash

    Auth-->>API: {access_token, refresh_token, user}
    API-->>UI: Set tokens + user profile
    UI->>UI: Store access token in memory<br/>Refresh token in httpOnly cookie

    Note over UI,API: Subsequent authenticated requests

    UI->>API: GET /api/v1/customers<br/>Authorization: Bearer {access_token}
    API->>Auth: Validate JWT signature + expiry
    Auth->>Auth: Extract user_id, role, permissions
    Auth-->>API: AuthContext{user_id, role, permissions}
    API->>API: RBAC check against route requirements
    API-->>UI: Protected resource response

    Note over UI,API: Token refresh flow

    UI->>API: POST /api/v1/auth/refresh<br/>{refresh_token}
    API->>Auth: validate_refresh_token()
    Auth->>DB: Verify token hash + expiry
    Auth->>Auth: Generate new access token
    Auth->>Auth: Rotate refresh token
    Auth-->>API: {new_access_token, new_refresh_token}
    API-->>UI: Updated tokens
```

---

## 4. API Architecture

### Design Principles

| Principle | Implementation |
|---|---|
| **RESTful Resource Modeling** | Nouns for resources, HTTP verbs for actions (`GET /customers`, `POST /accounts`) |
| **API Versioning** | URI path versioning: `/api/v1/` prefix on all routes |
| **Consistent Response Envelope** | All responses follow `{data, meta, errors}` structure |
| **Pagination** | Cursor-based for large datasets, offset-based for admin views |
| **Idempotency** | `Idempotency-Key` header support on POST/PUT operations |
| **Content Negotiation** | `application/json` primary; `multipart/form-data` for file uploads |

### Route Namespace Map

```
/api/v1/
├── auth/
│   ├── POST   /login
│   ├── POST   /refresh
│   └── POST   /logout
├── dashboard/
│   └── GET    /stats
├── customers/
│   ├── GET    /                    # List with filtering
│   ├── POST   /                    # Create customer
│   ├── GET    /{id}                # Get customer detail
│   ├── PUT    /{id}                # Update customer
│   ├── GET    /{id}/accounts       # Customer accounts
│   ├── GET    /{id}/transactions   # Customer transactions
│   └── GET    /{id}/kyc            # KYC status
├── accounts/
│   ├── GET    /
│   ├── POST   /
│   └── GET    /{id}/transactions
├── transactions/
│   ├── GET    /
│   └── POST   /
├── loans/
│   ├── GET    /
│   ├── POST   /
│   ├── GET    /{id}
│   └── PATCH  /{id}/status
├── documents/
│   ├── POST   /upload
│   ├── GET    /{id}
│   ├── GET    /{id}/ocr-result
│   └── POST   /{id}/reprocess
├── knowledge-base/
│   ├── GET    /documents
│   ├── POST   /documents/ingest
│   ├── GET    /documents/{id}
│   ├── POST   /search
│   └── GET    /documents/{id}/versions
├── assistant/
│   ├── POST   /chat
│   ├── GET    /sessions
│   ├── GET    /sessions/{id}/history
│   └── DELETE /sessions/{id}
├── agent/
│   ├── POST   /execute
│   ├── GET    /tasks
│   ├── GET    /tasks/{id}
│   └── GET    /tools
├── workflows/
│   ├── GET    /
│   ├── POST   /
│   ├── GET    /{id}
│   ├── GET    /{id}/transitions
│   └── PATCH  /{id}/state
├── reviews/
│   ├── GET    /pending
│   ├── GET    /{id}
│   └── POST   /{id}/decision
├── audit/
│   ├── GET    /events
│   └── GET    /events/{entity_type}/{entity_id}
└── analytics/
    ├── GET    /reports
    ├── POST   /reports/generate
    └── GET    /metrics
```

### Error Response Schema

All errors return a consistent structure with machine-readable codes and human-readable messages:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format",
        "code": "INVALID_FORMAT"
      }
    ],
    "request_id": "req_a1b2c3d4",
    "timestamp": "2026-11-07T20:00:00Z"
  }
}
```

### Standard HTTP Status Codes

| Code | Usage |
|---|---|
| `200` | Successful retrieval or update |
| `201` | Successful resource creation |
| `204` | Successful deletion (no body) |
| `400` | Validation error / malformed request |
| `401` | Missing or invalid authentication |
| `403` | Authenticated but insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict (duplicate, state violation) |
| `422` | Semantically invalid request body |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

## 5. Database Architecture

### Entity-Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        varchar role
        jsonb permissions
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CUSTOMERS {
        uuid id PK
        varchar first_name
        varchar last_name
        varchar email UK
        varchar phone
        varchar national_id UK
        varchar kyc_status
        jsonb address
        timestamp date_of_birth
        timestamp created_at
        timestamp updated_at
    }

    ACCOUNTS {
        uuid id PK
        uuid customer_id FK
        varchar account_number UK
        varchar account_type
        decimal balance
        varchar currency
        varchar status
        timestamp opened_at
        timestamp closed_at
    }

    TRANSACTIONS {
        uuid id PK
        uuid account_id FK
        varchar transaction_type
        decimal amount
        varchar currency
        decimal balance_after
        varchar reference_number UK
        varchar description
        varchar status
        timestamp created_at
    }

    LOANS {
        uuid id PK
        uuid customer_id FK
        uuid account_id FK
        decimal principal_amount
        decimal interest_rate
        integer term_months
        varchar status
        timestamp applied_at
        timestamp approved_at
        timestamp disbursed_at
    }

    DOCUMENTS {
        uuid id PK
        uuid customer_id FK
        varchar document_type
        varchar file_path
        varchar original_filename
        varchar mime_type
        integer file_size
        varchar ocr_status
        float ocr_confidence
        jsonb extracted_fields
        timestamp uploaded_at
        timestamp processed_at
    }

    KB_DOCUMENTS {
        uuid id PK
        varchar title
        varchar source_type
        varchar file_path
        integer current_version
        varchar status
        timestamp ingested_at
        timestamp updated_at
    }

    KB_CHUNKS {
        uuid id PK
        uuid document_id FK
        integer chunk_index
        text content
        varchar qdrant_point_id
        integer version
        jsonb metadata
    }

    CHAT_SESSIONS {
        uuid id PK
        uuid user_id FK
        varchar title
        varchar language
        timestamp created_at
        timestamp last_active_at
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        varchar role
        text content
        jsonb sources
        integer token_count
        float latency_ms
        timestamp created_at
    }

    AGENT_TASKS {
        uuid id PK
        uuid user_id FK
        text task_description
        varchar status
        jsonb tool_calls
        jsonb result
        timestamp created_at
        timestamp completed_at
    }

    WORKFLOWS {
        uuid id PK
        varchar workflow_type
        uuid entity_id
        varchar entity_type
        varchar current_state
        jsonb state_data
        uuid initiated_by FK
        timestamp created_at
        timestamp updated_at
    }

    WORKFLOW_TRANSITIONS {
        uuid id PK
        uuid workflow_id FK
        varchar from_state
        varchar to_state
        varchar triggered_by
        jsonb metadata
        timestamp created_at
    }

    REVIEW_ITEMS {
        uuid id PK
        varchar review_type
        uuid entity_id
        varchar entity_type
        varchar status
        uuid assigned_to FK
        jsonb review_data
        text decision_notes
        timestamp created_at
        timestamp decided_at
    }

    AUDIT_EVENTS {
        uuid event_id PK
        uuid user_id FK
        varchar action
        varchar resource_type
        uuid resource_id
        jsonb old_values
        jsonb new_values
        varchar ip_address
        text user_agent
        varchar session_id
        jsonb metadata
        timestamp created_at
    }

    CUSTOMERS ||--o{ ACCOUNTS : "owns"
    CUSTOMERS ||--o{ DOCUMENTS : "submits"
    CUSTOMERS ||--o{ LOANS : "applies for"
    ACCOUNTS ||--o{ TRANSACTIONS : "records"
    LOANS }o--|| ACCOUNTS : "disbursed to"
    KB_DOCUMENTS ||--o{ KB_CHUNKS : "split into"
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : "contains"
    USERS ||--o{ CHAT_SESSIONS : "initiates"
    USERS ||--o{ AGENT_TASKS : "creates"
    WORKFLOWS ||--o{ WORKFLOW_TRANSITIONS : "progresses through"
    USERS ||--o{ REVIEW_ITEMS : "assigned to"
    USERS ||--o{ AUDIT_EVENTS : "performed by"
```

### Key Indexing Strategy

| Table | Index | Type | Purpose |
|---|---|---|---|
| `customers` | `national_id` | Unique B-tree | Fast KYC lookups |
| `accounts` | `customer_id` | B-tree | Customer account listing |
| `accounts` | `account_number` | Unique B-tree | Account lookups |
| `transactions` | `account_id, created_at` | Composite B-tree | Chronological transaction history |
| `transactions` | `reference_number` | Unique B-tree | Duplicate detection |
| `documents` | `customer_id, document_type` | Composite B-tree | Customer document queries |
| `audit_events` | `entity_type, entity_id` | Composite B-tree | Entity audit trail |
| `audit_events` | `created_at` | B-tree (BRIN) | Time-range queries on large table |
| `workflows` | `workflow_type, current_state` | Composite B-tree | Queue-based workflow processing |
| `review_items` | `status, assigned_to` | Composite B-tree | Pending review queue |

### Migration Strategy

Database migrations are managed with **Alembic** using the following conventions:

- Migrations are auto-generated from SQLAlchemy model changes
- Each migration has a descriptive message and is reviewed before application
- Down-migrations are always provided for rollback capability
- Data migrations are separated from schema migrations
- Production migrations run within transactions with automatic rollback on failure

---

## 6. Security Architecture

### RBAC Model

```mermaid
graph TD
    subgraph Roles
        ADMIN["Administrator<br/>Full system & user admin"]
        OPS["Operations Officer<br/>Workflows, intake, ops"]
        CS["Customer Service<br/>Lookup, complaints, status"]
        COMP["Compliance Reviewer<br/>KYC review, audit, approvals"]
        BM["Branch Manager<br/>Branch workflows & approvals"]
    end

    subgraph Permissions
        P1["customers:read"]
        P2["customers:write"]
        P3["accounts:read"]
        P4["accounts:write"]
        P5["transactions:read"]
        P6["transactions:write"]
        P7["documents:read"]
        P8["documents:write"]
        P9["workflows:approve"]
        P10["agent:execute"]
        P11["audit:read"]
        P12["analytics:read"]
        P13["users:manage"]
        P14["kb:manage"]
    end

    ADMIN --> P1 & P2 & P3 & P4 & P5 & P6 & P7 & P8 & P9 & P10 & P11 & P12 & P13 & P14
    BM --> P1 & P2 & P3 & P4 & P5 & P7 & P8 & P9 & P11 & P12
    OPS --> P1 & P2 & P3 & P4 & P5 & P7 & P8 & P10
    CS --> P1 & P3 & P5 & P7
    COMP --> P1 & P3 & P5 & P7 & P9 & P11 & P12 & P14

    classDef role fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef perm fill:#6366f1,stroke:#3730a3,color:#fff
    class ADMIN,BM,OPS,CS,COMP role
    class P1,P2,P3,P4,P5,P6,P7,P8,P9,P10,P11,P12,P13,P14 perm
```

### JWT Token Architecture

| Property | Access Token | Refresh Token |
|---|---|---|
| **Lifetime** | 15 minutes | 7 days |
| **Storage** | In-memory (JavaScript variable) | httpOnly, Secure, SameSite=Strict cookie |
| **Payload** | `{sub, role, permissions, exp, iat, jti}` | `{sub, exp, iat, jti, token_family}` |
| **Rotation** | Issued on every refresh | Rotated on every use (one-time use) |
| **Revocation** | Short-lived, no explicit revocation | Hash stored in DB, deletable |

### Data Protection Layers

```mermaid
graph LR
    subgraph Transport["Transport Security"]
        TLS["TLS 1.3<br/>All HTTP traffic"]
    end

    subgraph Application["Application Security"]
        INPUT["Input Validation<br/>Pydantic + Zod"]
        SQLI["SQL Injection Prevention<br/>SQLAlchemy ORM"]
        XSS["XSS Protection<br/>React auto-escaping"]
        CSRF["CSRF Protection<br/>SameSite cookies"]
        RATE["Rate Limiting<br/>Per-user throttling"]
    end

    subgraph Data["Data-at-Rest"]
        HASH["Password Hashing<br/>bcrypt (cost=12)"]
        ENCRYPT["Sensitive Field Encryption<br/>AES-256-GCM"]
        AUDIT_LOG["Immutable Audit Log<br/>Append-only table"]
    end

    TLS --> Application
    Application --> Data

    classDef transport fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef app fill:#10b981,stroke:#047857,color:#fff
    classDef data fill:#ef4444,stroke:#991b1b,color:#fff

    class TLS transport
    class INPUT,SQLI,XSS,CSRF,RATE app
    class HASH,ENCRYPT,AUDIT_LOG data
```

> [!IMPORTANT]
> The audit_events table uses an append-only pattern — no UPDATE or DELETE operations are permitted at the application level. This ensures a tamper-evident audit trail suitable for regulatory compliance.

---

## 7. AI Architecture

### Component Interaction Model

```mermaid
graph TB
    subgraph Clients["Client Entry Points"]
        CHAT["Chat Interface<br/>(Assistant)"]
        AGENT_UI["Agent Console<br/>(Operations)"]
        DOC_UI["Document Upload<br/>(Intelligence)"]
        KB_UI["Knowledge Base<br/>(Search)"]
    end

    subgraph Orchestration["Orchestration Layer"]
        ASSISTANT_SVC["Assistant Service<br/>Session + Context Management"]
        AGENT_SVC["Agent Service<br/>LangGraph Orchestration"]
        DOC_SVC["Document Service<br/>OCR Pipeline Manager"]
        KB_SVC["KB Service<br/>Ingestion + Retrieval"]
    end

    subgraph Core_AI["Core AI Services"]
        LLM_CLIENT["LLM Client<br/>Ollama API Wrapper"]
        RAG_PIPE["RAG Pipeline<br/>Embed → Search → Rerank → Augment"]
        OCR_PIPE["OCR Pipeline<br/>Preprocess → Detect → Recognize → Extract"]
        AGENT_RT["Agent Runtime<br/>LangGraph State Machine"]
    end

    subgraph Infrastructure["AI Infrastructure"]
        OLLAMA_SRV["Ollama Server<br/>(GPU/CPU)"]
        QDRANT_SRV["Qdrant Server<br/>(Vector Storage)"]
        PADDLE_RT["PaddleOCR Runtime<br/>(CPU)"]
    end

    CHAT --> ASSISTANT_SVC
    AGENT_UI --> AGENT_SVC
    DOC_UI --> DOC_SVC
    KB_UI --> KB_SVC

    ASSISTANT_SVC --> LLM_CLIENT
    ASSISTANT_SVC --> RAG_PIPE
    AGENT_SVC --> AGENT_RT
    AGENT_RT --> LLM_CLIENT
    DOC_SVC --> OCR_PIPE
    KB_SVC --> RAG_PIPE

    LLM_CLIENT --> OLLAMA_SRV
    RAG_PIPE --> QDRANT_SRV
    RAG_PIPE --> LLM_CLIENT
    OCR_PIPE --> PADDLE_RT

    classDef client fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef orch fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef core fill:#f59e0b,stroke:#b45309,color:#fff
    classDef infra fill:#ef4444,stroke:#991b1b,color:#fff

    class CHAT,AGENT_UI,DOC_UI,KB_UI client
    class ASSISTANT_SVC,AGENT_SVC,DOC_SVC,KB_SVC orch
    class LLM_CLIENT,RAG_PIPE,OCR_PIPE,AGENT_RT core
    class OLLAMA_SRV,QDRANT_SRV,PADDLE_RT infra
```

### LLM Integration — Qwen3 8B via Ollama

| Aspect | Configuration |
|---|---|
| **Model** | `qwen3:8b` — 8 billion parameter multilingual model |
| **Runtime** | Ollama (local inference, no external API calls) |
| **Context Window** | 32,768 tokens |
| **Languages** | English, Arabic (native bilingual support) |
| **Temperature** | Task-dependent: 0.1 (extraction), 0.4 (chat), 0.0 (agent planning) |
| **Streaming** | Server-Sent Events (SSE) for real-time chat responses |
| **Prompt Strategy** | System prompt per task type + few-shot examples for banking domain |

### RAG Pipeline & Policy Governance Detail

#### Dual-Portal Architecture for NileOps Demo Bank

NileOps simulates retail digital banking operations for a fictional institution, **NileOps Demo Bank** (a working simulation identity with no affiliation to or imitation of any real institution). The platform provides two distinct user interfaces sharing one approved policy knowledge base under strict authorization boundaries:

```mermaid
graph TD
    subgraph SharedKB["Approved Banking Policy Knowledge Base (PostgreSQL 16 + Qdrant)"]
        KB_APPROVED["12 Approved Policy Domains<br/>(Accounts, KYC, Cards, Transfers, InstaPay, Loans, etc.)"]
    end

    subgraph CustomerPortal["Customer Portal (Public / Retail Client)"]
        CP_UI["Customer Web & Mobile Interface<br/>(Arabic-first, Egyptian vernacular, RTL/LTR)"]
        CP_RAG["Customer Conversational Assistant<br/>(Policy Q&A, Product Guide, Complaint Intake)"]
        CP_AUTH["Authenticated Customer Services<br/>(Own balance, own statements via JWT)"]
        CP_UI --> CP_RAG
        CP_UI --> CP_AUTH
    end

    subgraph EmployeePortal["Employee Portal (Internal Bank Operations)"]
        EP_UI["Operations & Copilot Dashboard<br/>(Staff RBAC: admin, ops_officer, customer_service, etc.)"]
        EP_COPILOT["Customer Service AI Copilot<br/>(Policy search, cited guidance, case summary)"]
        EP_TOOLS["Controlled Banking Tools<br/>(Customer 360, KYC review, workflow approval)"]
        EP_GOV["Policy Governance Queue<br/>(DRAFT -> PENDING_APPROVAL -> APPROVED)"]
        EP_UI --> EP_COPILOT
        EP_UI --> EP_TOOLS
        EP_UI --> EP_GOV
    end

    CP_RAG -->|Read-only Filtered Chunks| KB_APPROVED
    EP_COPILOT -->|Read-only All Chunks| KB_APPROVED
    EP_GOV -->|Approves & Indexes| KB_APPROVED

    classDef cp fill:#0284c7,stroke:#0369a1,color:#fff
    classDef ep fill:#4f46e5,stroke:#3730a3,color:#fff
    classDef kb fill:#059669,stroke:#047857,color:#fff

    class CP_UI,CP_RAG,CP_AUTH cp
    class EP_UI,EP_COPILOT,EP_TOOLS,EP_GOV ep
    class KB_APPROVED kb
```

#### Mandatory Policy Approval State Machine

All knowledge base documents follow a strictly auditable state machine ensuring unapproved documents never enter active retrieval collections:

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Upload Document (PDF/DOCX/MD)
    DRAFT --> PENDING_APPROVAL: Submit for Review
    PENDING_APPROVAL --> APPROVED: Explicit Approval (compliance_reviewer / branch_manager)
    PENDING_APPROVAL --> REJECTED: Rejection (with mandatory reason)
    REJECTED --> DRAFT: Edit & Resubmit
    APPROVED --> INDEXED: Qdrant Vector Indexing Complete
    INDEXED --> ARCHIVED: Superseded by New Version
    APPROVED --> INDEX_FAILED: Qdrant Connection / Embedding Error
    INDEX_FAILED --> APPROVED: Retry Indexing
    ARCHIVED --> [*]
```

- **Separation of Duties:** The employee who uploaded a policy document (`uploaded_by`) cannot approve it (`approved_by != uploaded_by`).
- **Superseded Document Tombstoning:** Activating a new approved version deactivates all chunks belonging to older versions in Qdrant (`is_active = FALSE`).

#### 12 Synthetic Policy Domains (NileOps Demo Bank)
1. Current & Savings Accounts
2. Account Opening & Account Maintenance
3. KYC & Identity Document Requirements
4. Debit, Credit & Prepaid Cards
5. Domestic Transfers & Clearing
6. InstaPay Network Guidelines & Daily Limits
7. Investment Certificates & Term Deposits
8. Retail Loans & Financing Policies
9. Schedule of Fees, Commissions & Service Limits
10. Customer Complaints & Dispute Procedures
11. Branch Network, Working Hours & ATM Services
12. Digital Banking & Mobile Application Support

#### Ingestion & Retrieval Pipeline

```mermaid
graph LR
    subgraph Ingestion["Document Ingestion & Governance"]
        UPLOAD["Upload Policy<br/>(PDF, DOCX, MD)"]
        HASH["SHA-256 Checksum<br/>(Duplicate Detection)"]
        REVIEW["Human Approval Gate<br/>(compliance_reviewer)"]
        SPLIT["Bilingual Chunking<br/>(Evaluated 512t, 50ov)"]
        EMBED_I["Dynamic Dimension<br/>Embedding Probe"]
        STORE_I["Store in Qdrant<br/>+ Postgres Metadata"]
        UPLOAD --> HASH --> REVIEW --> SPLIT --> EMBED_I --> STORE_I
    end

    subgraph Retrieval["Query-Time Hybrid Retrieval"]
        QUERY["User Query (AR / EN)"]
        EMBED_Q["Embed Query"]
        SEARCH["Vector Similarity (Qdrant)<br/>Cosine Top-K"]
        LEXICAL["Keyword Matching<br/>(Postgres tsvector)"]
        FUSION["Score Fusion & Portal Filter<br/>(target_portal check)"]
        BUILD["Context Assembly<br/>+ Exact Provenance Citations"]
        QUERY --> EMBED_Q --> SEARCH
        QUERY --> LEXICAL
        SEARCH --> FUSION
        LEXICAL --> FUSION
        FUSION --> BUILD
    end

    BUILD --> LLM_GEN["LLM Grounded Generation<br/>(qwen3:8b via Ollama)"]

    classDef ingest fill:#06b6d4,stroke:#0e7490,color:#fff
    classDef retrieve fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef gen fill:#f59e0b,stroke:#b45309,color:#fff

    class UPLOAD,HASH,REVIEW,SPLIT,EMBED_I,STORE_I ingest
    class QUERY,EMBED_Q,SEARCH,LEXICAL,FUSION,BUILD retrieve
    class LLM_GEN gen
```

#### Grounded Generation & Escalation Rules
- **Evidence-Bound Answers:** The assistant generates responses strictly grounded in retrieved policy chunks and cites document title, version number, and section title.
- **Explicit Abstention:** If retrieved chunks fail relevance thresholds or evidence is insufficient, the assistant explicitly states: *"Based on approved NileOps Demo Bank documentation, I do not have sufficient information to answer this inquiry."*
- **Contradiction Detection:** If retrieved chunks contain conflicting provisions across different active documents, the assistant identifies the ambiguity and flags the case for compliance review.
- **Simulated Escalation Paths:** Inquiries involving customer disputes, repeated ungrounded queries, or explicit requests for human support automatically create a simulated ticket in the customer service queue (`conversations.escalation_status = 'pending_escalation'`).
- **Feedback Collection:** Every assistant response supports thumbs up/down and groundedness rating captured in `rag_feedbacks`.

### Agent Tool Registry and Permissions

The AI Operations Agent operates under a **strict tool allowlist** — the LLM can only invoke pre-registered, explicitly permitted tools. Each tool has a risk classification that determines whether human approval is required.

| Tool | Description | Risk Level | Requires Approval |
|---|---|---|---|
| `lookup_customer` | Retrieve customer details by ID | Low | No |
| `search_customers` | Search customers by criteria | Low | No |
| `get_account_balance` | Check account balance | Low | No |
| `get_transaction_history` | List recent transactions | Low | No |
| `open_account` | Create new bank account | High | **Yes** |
| `update_kyc_status` | Change customer KYC status | High | **Yes** |
| `initiate_workflow` | Start banking workflow | Medium | **Yes** |
| `approve_loan` | Approve a loan application | Critical | **Yes** |
| `search_knowledge_base` | Query banking knowledge base | Low | No |
| `generate_report` | Create analytics report | Low | No |

> [!CAUTION]
> The agent **cannot** execute arbitrary code, run shell commands, or call tools outside the registered allowlist. Any tool call not on the allowlist is rejected at the registry level before reaching execution. This is a hard security boundary, not an LLM instruction.

### LangGraph Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> Planning: Task received

    Planning --> ToolSelection: Plan generated
    Planning --> Failed: Planning error

    ToolSelection --> AllowlistCheck: Tool identified
    AllowlistCheck --> ApprovalRequired: Tool needs approval
    AllowlistCheck --> Executing: Tool auto-approved
    AllowlistCheck --> Failed: Tool not in allowlist

    ApprovalRequired --> WaitingForApproval: Request sent to HITL
    WaitingForApproval --> Executing: Human approved
    WaitingForApproval --> Failed: Human rejected

    Executing --> ResultProcessing: Tool executed
    Executing --> Failed: Execution error

    ResultProcessing --> ToolSelection: More tools needed
    ResultProcessing --> Completed: Task finished

    Completed --> [*]
    Failed --> [*]
```

---

## 8. Deployment Architecture

### Docker Compose Services

```mermaid
graph TB
    subgraph Docker["Docker Compose Stack"]
        subgraph Frontend_Container["frontend"]
            NGINX["Nginx<br/>:80 / :443"]
            REACT["React SPA<br/>(static build)"]
            NGINX --> REACT
        end

        subgraph Backend_Container["backend"]
            UVICORN["Uvicorn<br/>:8000"]
            FASTAPI_APP["FastAPI Application"]
            UVICORN --> FASTAPI_APP
        end

        subgraph Ollama_Container["ollama"]
            OLLAMA_BIN["Ollama Server<br/>:11434"]
            MODEL["qwen3:8b"]
            OLLAMA_BIN --> MODEL
        end

        subgraph Qdrant_Container["qdrant"]
            QDRANT_BIN["Qdrant Server<br/>:6333 / :6334"]
        end

        subgraph Postgres_Container["postgres"]
            PG_BIN["PostgreSQL 16<br/>:5432"]
        end
    end

    subgraph Volumes["Docker Volumes"]
        PG_DATA["pg_data<br/>(Database files)"]
        QD_DATA["qdrant_data<br/>(Vector storage)"]
        UPLOAD_VOL["uploads<br/>(Documents)"]
        OLLAMA_MODELS["ollama_models<br/>(Model weights)"]
    end

    NGINX -->|"Reverse proxy<br/>/api/*"| UVICORN
    FASTAPI_APP --> PG_BIN
    FASTAPI_APP --> QDRANT_BIN
    FASTAPI_APP --> OLLAMA_BIN

    PG_BIN --> PG_DATA
    QDRANT_BIN --> QD_DATA
    FASTAPI_APP --> UPLOAD_VOL
    OLLAMA_BIN --> OLLAMA_MODELS

    classDef container fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef volume fill:#6b7280,stroke:#374151,color:#fff

    class NGINX,REACT,UVICORN,FASTAPI_APP,OLLAMA_BIN,MODEL,QDRANT_BIN,PG_BIN container
    class PG_DATA,QD_DATA,UPLOAD_VOL,OLLAMA_MODELS volume
```

### Service Configuration Matrix

| Service | Image | Port(s) | Resources | Health Check |
|---|---|---|---|---|
| `frontend` | `node:20-alpine` (build) → `nginx:alpine` | 80, 443 | 256MB RAM | `GET /` |
| `backend` | `python:3.11-slim` | 8000 | 1GB RAM | `GET /api/v1/health` |
| `postgres` | `postgres:16-alpine` | 5432 | 512MB RAM | `pg_isready` |
| `qdrant` | `qdrant/qdrant:latest` | 6333, 6334 | 512MB RAM | `GET /healthz` |
| `ollama` | `ollama/ollama:latest` | 11434 | 8GB+ RAM / GPU | `GET /api/tags` |

### Container Dependencies

```
frontend ──depends_on──► backend (healthy)
backend  ──depends_on──► postgres (healthy)
backend  ──depends_on──► qdrant (healthy)
backend  ──depends_on──► ollama (healthy)
```

---

## 9. Directory Structure

```
NileOps_V4/
├── docker-compose.yml                  # Multi-service orchestration
├── .env.example                        # Environment variable template
├── README.md                           # Project overview and quickstart
│
├── docs/                               # Documentation
│   ├── ARCHITECTURE.md                 # This document
│   ├── API.md                          # API reference
│   └── DEPLOYMENT.md                   # Deployment guide
│
├── frontend/                           # React SPA
│   ├── Dockerfile
│   ├── nginx.conf                      # Nginx reverse proxy config
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   ├── public/
│   │   └── assets/                     # Static assets
│   └── src/
│       ├── main.tsx                    # Application entry point
│       ├── App.tsx                     # Root component with routing
│       ├── api/                        # API client layer
│       │   ├── client.ts              # Axios instance + interceptors
│       │   ├── endpoints.ts           # Endpoint constants
│       │   └── types.ts              # API response types
│       ├── components/                 # Shared UI components
│       │   ├── layout/               # Shell, sidebar, header
│       │   ├── common/               # Tables, modals, forms, alerts
│       │   └── charts/               # Dashboard chart components
│       ├── pages/                     # Route-level page components
│       │   ├── Dashboard/
│       │   ├── Customers/
│       │   ├── Accounts/
│       │   ├── Transactions/
│       │   ├── Loans/
│       │   ├── Documents/
│       │   ├── KnowledgeBase/
│       │   ├── Assistant/
│       │   ├── Agent/
│       │   ├── Workflows/
│       │   ├── Reviews/
│       │   ├── AuditTrail/
│       │   └── Analytics/
│       ├── hooks/                     # Custom React hooks
│       │   ├── useAuth.ts
│       │   ├── useApi.ts
│       │   └── useWebSocket.ts
│       ├── context/                   # React contexts
│       │   ├── AuthContext.tsx
│       │   └── ThemeContext.tsx
│       ├── i18n/                      # Internationalization
│       │   ├── en.json
│       │   └── ar.json
│       ├── utils/                     # Utility functions
│       └── types/                     # TypeScript type definitions
│
├── backend/                           # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini                    # Alembic configuration
│   ├── alembic/                       # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app factory
│       ├── config.py                  # Settings (Pydantic BaseSettings)
│       ├── dependencies.py            # Dependency injection
│       │
│       ├── api/                       # API layer
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py          # Aggregated v1 router
│       │       ├── auth.py
│       │       ├── dashboard.py
│       │       ├── customers.py
│       │       ├── accounts.py
│       │       ├── transactions.py
│       │       ├── loans.py
│       │       ├── documents.py
│       │       ├── knowledge_base.py
│       │       ├── assistant.py
│       │       ├── agent.py
│       │       ├── workflows.py
│       │       ├── reviews.py
│       │       ├── audit.py
│       │       └── analytics.py
│       │
│       ├── models/                    # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── customer.py
│       │   ├── account.py
│       │   ├── transaction.py
│       │   ├── loan.py
│       │   ├── document.py
│       │   ├── knowledge_base.py
│       │   ├── chat.py
│       │   ├── agent.py
│       │   ├── workflow.py
│       │   ├── review.py
│       │   └── audit.py
│       │
│       ├── schemas/                   # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── customer.py
│       │   ├── account.py
│       │   ├── transaction.py
│       │   ├── loan.py
│       │   ├── document.py
│       │   ├── knowledge_base.py
│       │   ├── chat.py
│       │   ├── agent.py
│       │   ├── workflow.py
│       │   ├── review.py
│       │   └── common.py              # Shared schemas (pagination, errors)
│       │
│       ├── services/                  # Business logic services
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── customer_service.py
│       │   ├── account_service.py
│       │   ├── transaction_service.py
│       │   ├── loan_service.py
│       │   ├── document_service.py
│       │   ├── knowledge_base_service.py
│       │   ├── assistant_service.py
│       │   ├── agent_service.py
│       │   ├── workflow_service.py
│       │   ├── hitl_service.py
│       │   ├── audit_service.py
│       │   └── analytics_service.py
│       │
│       ├── ai/                        # AI subsystems
│       │   ├── __init__.py
│       │   ├── llm/
│       │   │   ├── client.py          # Ollama API client
│       │   │   ├── prompts.py         # System prompts per task
│       │   │   └── streaming.py       # SSE streaming handler
│       │   ├── rag/
│       │   │   ├── embeddings.py      # Embedding model wrapper
│       │   │   ├── chunker.py         # Document chunking logic
│       │   │   ├── retriever.py       # Qdrant search + rerank
│       │   │   └── pipeline.py        # End-to-end RAG pipeline
│       │   ├── ocr/
│       │   │   ├── engine.py          # PaddleOCR wrapper
│       │   │   ├── preprocessor.py    # OpenCV image preprocessing
│       │   │   ├── extractor.py       # Field extraction logic
│       │   │   └── confidence.py      # Confidence scoring
│       │   └── agent/
│       │       ├── graph.py           # LangGraph state graph definition
│       │       ├── tools.py           # Tool implementations
│       │       ├── registry.py        # Tool allowlist + permissions
│       │       └── nodes.py           # Graph node functions
│       │
│       ├── core/                      # Cross-cutting concerns
│       │   ├── __init__.py
│       │   ├── security.py            # JWT, hashing, encryption
│       │   ├── database.py            # SQLAlchemy engine + session
│       │   ├── exceptions.py          # Custom exception hierarchy
│       │   ├── middleware.py           # CORS, rate limit, audit logging
│       │   └── events.py              # Application lifecycle events
│       │
│       └── utils/                     # Utility functions
│           ├── __init__.py
│           ├── pagination.py
│           ├── validators.py
│           └── file_utils.py
│
├── tests/                             # Test suite
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/
│   │   ├── test_services/
│   │   ├── test_ai/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_database/
│   └── e2e/
│
└── scripts/                           # DevOps and utility scripts
    ├── seed_data.py                   # Database seeding
    ├── pull_models.sh                 # Ollama model download
    └── run_migrations.sh              # Alembic migration runner
```

---

## 10. Integration Points

### Internal Module Communication Map

```mermaid
graph LR
    subgraph Core_Modules["Core Banking"]
        CUST_M["Customer<br/>Management"]
        ACC_M["Account<br/>Management"]
        TXN_M["Transaction<br/>Management"]
        LOAN_M["Loan<br/>Management"]
    end

    subgraph AI_Modules["AI Modules"]
        DOC_M["Document<br/>Intelligence"]
        KB_M["Knowledge<br/>Base"]
        ASSIST_M["AI<br/>Assistant"]
        AGENT_M["AI<br/>Agent"]
    end

    subgraph Ops_Modules["Operations"]
        WF_M["Workflow<br/>Engine"]
        HITL_M["Human-in-the-<br/>Loop"]
        AUDIT_M["Audit<br/>Trail"]
    end

    %% Core banking relationships
    CUST_M --> ACC_M
    ACC_M --> TXN_M
    CUST_M --> LOAN_M
    LOAN_M --> ACC_M

    %% AI into core
    DOC_M -->|"Extracted data"| CUST_M
    AGENT_M -->|"Tool calls"| CUST_M
    AGENT_M -->|"Tool calls"| ACC_M
    AGENT_M -->|"Tool calls"| LOAN_M
    ASSIST_M -->|"Context queries"| KB_M

    %% Workflows
    CUST_M -->|"KYC trigger"| WF_M
    ACC_M -->|"Opening trigger"| WF_M
    LOAN_M -->|"Approval trigger"| WF_M
    WF_M -->|"Approval request"| HITL_M
    DOC_M -->|"Low confidence"| HITL_M
    AGENT_M -->|"High-risk tool"| HITL_M

    %% Audit everything
    CUST_M --> AUDIT_M
    ACC_M --> AUDIT_M
    TXN_M --> AUDIT_M
    WF_M --> AUDIT_M
    AGENT_M --> AUDIT_M
    HITL_M --> AUDIT_M

    classDef core fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef ai fill:#f59e0b,stroke:#b45309,color:#fff
    classDef ops fill:#10b981,stroke:#047857,color:#fff

    class CUST_M,ACC_M,TXN_M,LOAN_M core
    class DOC_M,KB_M,ASSIST_M,AGENT_M ai
    class WF_M,HITL_M,AUDIT_M ops
```

### Integration Contracts

| Producer | Consumer | Method | Data Format | Trigger |
|---|---|---|---|---|
| Document Intelligence | Customer Management | Internal service call | `ExtractedDocumentData` schema | OCR completion event |
| Workflow Engine | HITL Service | Internal service call | `ReviewRequest` schema | State transition to review |
| AI Agent | Any service module | Tool registry dispatch | Tool-specific Pydantic schema | LangGraph tool node |
| HITL Service | Workflow Engine | Callback | `ReviewDecision` schema | Human approval/rejection |
| All state-changing services | Audit Service | Middleware + explicit | `AuditEvent` schema | Post-commit hook |
| Backend | Frontend | WebSocket | JSON messages | Real-time notifications |
| KB Service | Qdrant | HTTP client | Qdrant REST API | Document ingestion/search |
| Assistant/Agent Service | Ollama | HTTP client | Ollama API format | LLM inference request |

---

## 11. Configuration Management

### Environment Variables

All configuration is driven through environment variables, loaded via Pydantic `BaseSettings` with `.env` file support.

#### Application Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `APP_ENV` | Environment name | `development` | No |
| `APP_DEBUG` | Enable debug mode | `false` | No |
| `APP_SECRET_KEY` | JWT signing secret | — | **Yes** |
| `APP_HOST` | API bind host | `0.0.0.0` | No |
| `APP_PORT` | API bind port | `8000` | No |
| `APP_CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:5173"]` | No |

#### Database Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — | **Yes** |
| `DATABASE_POOL_SIZE` | Connection pool size | `10` | No |
| `DATABASE_MAX_OVERFLOW` | Pool overflow limit | `20` | No |
| `DATABASE_ECHO` | Log SQL queries | `false` | No |

#### AI / LLM Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://ollama:11434` | No |
| `OLLAMA_MODEL` | LLM model name | `qwen3:8b` | No |
| `OLLAMA_TIMEOUT` | Request timeout (seconds) | `120` | No |
| `LLM_TEMPERATURE_CHAT` | Temperature for chat | `0.4` | No |
| `LLM_TEMPERATURE_AGENT` | Temperature for agent planning | `0.0` | No |
| `LLM_TEMPERATURE_EXTRACTION` | Temperature for extraction | `0.1` | No |
| `LLM_MAX_TOKENS` | Maximum generation tokens | `2048` | No |

#### RAG Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `QDRANT_URL` | Qdrant server URL | `http://qdrant:6333` | No |
| `QDRANT_COLLECTION` | Default collection name | `nileops_kb` | No |
| `EMBEDDING_MODEL` | Embedding model identifier | `sentence-transformers/all-MiniLM-L6-v2` | No |
| `EMBEDDING_DIMENSION` | Discovered dynamically at startup via model probe | `dynamic (probed from model)` | No |
| `RAG_CHUNK_SIZE` | Chunk size in tokens | `512` | No |
| `RAG_CHUNK_OVERLAP` | Chunk overlap in tokens | `50` | No |
| `RAG_TOP_K` | Retrieval top-k results | `5` | No |
| `RAG_SCORE_THRESHOLD` | Minimum similarity score | `0.7` | No |

#### OCR Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `OCR_LANGUAGE` | PaddleOCR language(s) | `en,ar` | No |
| `OCR_CONFIDENCE_THRESHOLD` | Minimum confidence for auto-accept | `0.85` | No |
| `OCR_MAX_FILE_SIZE_MB` | Maximum upload file size | `20` | No |

#### Security Configuration

| Variable | Description | Default | Required |
|---|---|---|---|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` | No |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` | No |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` | No |
| `BCRYPT_ROUNDS` | bcrypt cost factor | `12` | No |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per user | `60` | No |

### Model Configuration

The LLM model is configured via Ollama's model management. System prompts are templated per task type:

| Task Type | Prompt Template | Temperature | Max Tokens |
|---|---|---|---|
| Banking Chat | `prompts/chat_system.txt` | 0.4 | 2048 |
| Document Extraction | `prompts/extraction_system.txt` | 0.1 | 1024 |
| Agent Planning | `prompts/agent_system.txt` | 0.0 | 4096 |
| RAG Augmented Response | `prompts/rag_system.txt` | 0.3 | 2048 |
| Workflow Summarization | `prompts/workflow_system.txt` | 0.2 | 1024 |

---

## 12. Scalability Considerations

### Current Architecture — Single-Node Deployment

The v1 architecture is designed for single-node Docker Compose deployment, suitable for pilot programs and branch-level operations.

### Future Scaling Paths

```mermaid
graph TD
    subgraph Current["Phase 1: Single Node"]
        SINGLE["Docker Compose<br/>All services co-located"]
    end

    subgraph Phase2["Phase 2: Vertical + Separation"]
        GPU_NODE["GPU Node<br/>Ollama + Qwen3"]
        APP_NODE["Application Node<br/>FastAPI + Frontend"]
        DB_NODE["Database Node<br/>PostgreSQL + Qdrant"]
    end

    subgraph Phase3["Phase 3: Horizontal Scale"]
        LB["Load Balancer<br/>Nginx / Traefik"]
        API_1["API Instance 1"]
        API_2["API Instance 2"]
        API_N["API Instance N"]
        PG_PRIMARY["PostgreSQL Primary"]
        PG_REPLICA["PostgreSQL Replica(s)"]
        QD_CLUSTER["Qdrant Cluster<br/>(Sharded)"]
    end

    subgraph Phase4["Phase 4: Cloud-Native"]
        K8S["Kubernetes<br/>Orchestration"]
        AUTOSCALE["Horizontal Pod Autoscaler"]
        MANAGED_DB["Managed PostgreSQL<br/>(RDS / Cloud SQL)"]
        MULTI_GPU["Multi-GPU Inference<br/>(vLLM / TGI)"]
        OBJ_STORE["Object Storage<br/>(S3 / GCS)"]
    end

    SINGLE --> Phase2
    Phase2 --> Phase3
    Phase3 --> Phase4

    classDef current fill:#10b981,stroke:#047857,color:#fff
    classDef future fill:#6366f1,stroke:#3730a3,color:#fff

    class SINGLE current
    class GPU_NODE,APP_NODE,DB_NODE,LB,API_1,API_2,API_N,PG_PRIMARY,PG_REPLICA,QD_CLUSTER,K8S,AUTOSCALE,MANAGED_DB,MULTI_GPU,OBJ_STORE future
```

### Scaling Strategy per Component

| Component | Bottleneck | Scaling Strategy |
|---|---|---|
| **FastAPI Backend** | Request throughput | Horizontal: multiple Uvicorn workers → multiple container replicas behind load balancer |
| **PostgreSQL** | Read throughput, storage | Vertical first (more RAM, SSD) → Read replicas → Managed service with auto-scaling |
| **Qdrant** | Collection size, query throughput | Vertical (more RAM) → Sharded collections → Multi-node Qdrant cluster |
| **Ollama / LLM** | Inference latency, concurrency | GPU acceleration → Multi-GPU → Switch to vLLM or TGI for batched inference |
| **PaddleOCR** | CPU-bound processing | Worker pool (multiprocessing) → Dedicated OCR container replicas |
| **File Storage** | Disk I/O, capacity | Local volume → NFS mount → Object storage (S3-compatible) |
| **Frontend** | Static asset delivery | CDN distribution → Edge caching |

### Performance Targets

| Metric | Target (v1) | Target (Scaled) |
|---|---|---|
| API response time (p95) | < 200ms | < 100ms |
| LLM first-token latency | < 2s | < 500ms |
| OCR processing time (single page) | < 5s | < 2s |
| RAG retrieval time | < 500ms | < 200ms |
| Concurrent users | 20 | 500+ |
| Document storage | 50GB | 10TB+ |
| Audit events per day | 10,000 | 1,000,000+ |

> [!TIP]
> The most impactful performance optimization for v1 is GPU acceleration for Ollama inference. A single NVIDIA GPU (e.g., RTX 4090 with 24GB VRAM) can reduce Qwen3 8B inference latency by 5–10x compared to CPU-only execution.

---

> **Document maintained by:** NileOps Engineering Team  
> **Review cycle:** Updated with each architectural decision record (ADR)
