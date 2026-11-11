# NileOps V4 — Operations & Developer Runbook

**Environment Target:** Windows 10/11 Development Workstation & Standard Linux/CI Containers  
**Application Architecture:** FastAPI (Python 3.11) + React 18 / TypeScript / Vite + PostgreSQL 16 + Qdrant Vector Store + PaddleOCR Document AI

---

## 1. System Services Overview

| Service | Port | Default Host | Process / Command | Description |
|---|---|---|---|---|
| **PostgreSQL** | `5432` | `127.0.0.1` | `postgres.exe -D <data_dir>` | Primary relational database (`nileops` dev, `nileops_test` isolated test). |
| **Qdrant Vector Store** | `6333` | `127.0.0.1` | `qdrant` binary or Python dev substitute | Vector database for RAG policy retrieval (`nileops_kb` / `nileops_kb_test`). |
| **FastAPI Backend** | `8000` | `127.0.0.1` | `uvicorn app.main:app --port 8000` | Asynchronous REST API, RBAC, KYC, RAG, and KPI engine. |
| **Vite Frontend** | `5173` | `127.0.0.1` | `npm run dev` | React SPA supporting English (LTR) and Arabic (RTL). |
| **Ollama (Optional)** | `11434` | `127.0.0.1` | `ollama serve` | Local LLM (`qwen3:8b`). When offline, extractive fallback operates autonomously. |

---

## 2. Machine-Specific Workarounds (Windows Smart App Control)

> [!IMPORTANT]
> The workarounds documented below are **machine-specific mitigations** tailored strictly for Windows development hosts where **Windows Smart App Control (SAC)**, **Windows Defender Application Control (WDAC)**, or **AppLocker** policies restrict unsigned third-party native binaries and C-extension `.pyd` modules. **They are NOT intended for CI/CD runners or Linux/Docker deployments**, where standard containerized binaries should be executed.

### 2.1 Runtime Meta-Path Import Hook (`_PandasShimFinder`)
- **Root Cause:** On Windows hosts with Smart App Control enforced, importing `pandas` fails with `ImportError: DLL load failed while importing _libs: Access is denied` (or `PermissionError` when loading unsigned native C-extension `.pyd` files like `pandas_parser.cp311-win_amd64.pyd`).
- **Mitigation:** A runtime meta-path import hook (`_PandasShimFinder`) intercepts `import pandas` and provides a lightweight mock interface without modifying the `.venv` or patching third-party packages on disk.
- **Scope:** PaddleX and PaddleOCR dynamically check for pandas when tabulating training metrics; in inference mode (`predict()`), pandas is never invoked for image processing. The hook satisfies the top-level import safely.
- **CI/Production Behavior:** On standard Linux or unconstrained Windows environments, standard `pandas` packages install and import normally without any shim.

### 2.2 Pure-Python Qdrant Substitute (`scratch/run_qdrant_service.py`)
- **Root Cause:** The upstream Qdrant standalone executable (`bin/qdrant.exe`) is an unsigned Rust binary compiled for Windows. On workstations with Smart App Control active, Windows Code Integrity blocks its execution (System Event 3077 / 3118).
- **Alternative Evaluated:** We evaluated `QdrantClient(path="data/qdrant_storage")` (local disk-based mode). However, local disk mode enforces exclusive single-process file locking; concurrent access from `uvicorn`, `pytest`, and evaluation scripts causes immediate process collision crashes (`RuntimeError: Storage folder is already accessed by another instance`).
- **Mitigation:** `scratch/run_qdrant_service.py` runs a lightweight, pure-Python asynchronous HTTP service on `127.0.0.1:6333` implementing the exact subset of the Qdrant v1 REST API needed by NileOps:
  - `GET /collections`
  - `GET /collections/{name}`
  - `PUT /collections/{name}`
  - `POST /collections/{name}/points/search` (supporting cosine distance, payload filtering by `portal_access`, `is_active`, `code`, and score thresholds)
  - `POST /collections/{name}/points`
  - `POST /collections/{name}/points/payload`
- **Data Parity:** The service loads points directly from `data/backups/nileops_kb_payload_export_*.json` with 100% hash and cosine similarity parity.
- **CI/Production Behavior:** In CI/CD pipelines and production deployments, run the official Qdrant Docker container:
  ```bash
  docker run -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant:v1.12.0
  ```

---

## 3. Step-by-Step Native Execution

### Step 1: Start PostgreSQL
```powershell
& "C:\PostgreSQL\16\pgsql\bin\postgres.exe" -D "C:\PostgreSQL\data"
```

### Step 2: Start Qdrant Vector Service
```powershell
# On machines with Smart App Control:
& "backend\.venv\Scripts\python.exe" -u "scratch\run_qdrant_service.py"

# On standard systems with Docker:
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

### Step 3: Run Test Suite
All automated tests must run against the isolated test database `nileops_test` and test collection `nileops_kb_test`:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

### Step 4: Launch Backend API
```powershell
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Launch Frontend
```powershell
cd frontend
npm run dev
```
Navigate to `http://localhost:5173`.

