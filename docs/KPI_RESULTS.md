# NileOps — Official Handbook KPI Results & Empirical Integrity Report

> **Evaluation Date:** 2026-11-16  
> **Integrity Verification Branch:** `integrity/check` (Merging to `master`)  
> **Environment:** Windows 11 Native Host, PostgreSQL 16 (Docker), Qdrant v1.20 (Docker), Python 3.11 (`backend/.venv`), Node 20+ / Vite  
> **Methodology:** 100% empirical measurement executed via automated benchmark scripts in `scripts/eval/` against strictly separated DEV and HELD-OUT synthetic partitions. Zero fabricated, estimated, or hand-tuned numbers.

---

## 1. Executive Summary & Status Overview

This report provides an empirical evaluation of the **NileOps Digital Banking Operations Simulation Platform** against the quantitative benchmarks and operational requirements established in the Egyptian Digital Banking Operations Handbook.

### Current Empirical Status
- **Audit Completeness:** **100.0% (MET)** on live PostgreSQL database ledger.
- **Exception Detection Recall:** **96.7% (MET)** on DEV (60 cards) and **100.0% (MET)** on HELD-OUT (60 cards).
- **Correct Escalation Rate:** **96.7% (MET)** on DEV (60 cards) and **100.0% (MET)** on HELD-OUT (60 cards).
- **RAG Grounded-Answer Rate (Hit@1):**
  - **DEV Set (N=40, 25 in-domain):** **76.0% (NOT MET)** vs target $\ge 90.0\%$.
  - **Held-Out Set 1 (N=30, 25 in-domain):** **52.0% (NOT MET)** vs target $\ge 90.0\%$.
  - **New Held-Out Set 2 (Colloquial / Typos / Fragments, N=30, 20 in-domain):** **45.0% (NOT MET)** vs target $\ge 90.0\%$.
- **RAG Abstention Rate:**
  - **DEV Set (N=15 out-of-domain):** **73.3% (NOT MET)** vs target $\ge 90.0\%$ (Abstention Precision: 68.8%).
  - **Held-Out Set 1 (N=5 out-of-domain):** **100.0% (MET)** vs target $\ge 90.0\%$ (Abstention Precision: 33.3%).
  - **New Held-Out Set 2 (N=10 out-of-domain):** **60.0% (NOT MET)** vs target $\ge 90.0\%$ (Abstention Precision: 37.5%).
- **OCR Field Extraction $F_1$ (40 cards across Clean, Glare, Blur, Shadow):**
  - **National ID Field $F_1$:** **87.5% (NOT MET)** vs target $\ge 90.0\%$.
  - **Citizen Name Field $F_1$:** **62.5% (NOT MET)** vs target $\ge 90.0\%$.
  - **Residential Address Field $F_1$:** **50.0% (NOT MET)** vs target $\ge 90.0\%$.
  - **Factory Code Field $F_1$:** **90.0% (MET)** vs target $\ge 90.0\%$.
  - *Statement on Preprocessing:* Advanced image preprocessing (such as super-resolution, morphological binarization, or localized CLAHE de-glaring before PaddleOCR) was **not implemented**. Raw or mildly filtered card images are fed directly to PaddleOCR, causing degraded character recognition on cursive Arabic text under glare and blur.
- **Automated Test Suite:** 131 tests passed in `backend/tests`. Frontend `tsc && vite build` passed with zero errors.

---

## 2. Complete Handbook KPI Results Table

| Operational / AI Metric | Handbook Target | DEV Measured | HELD-OUT 1 Measured | HELD-OUT 2 (Colloquial/Typos) | Status | Benchmark Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Audit Chain Completeness** | `100.0%` | **100.0%** (359 logs) | *N/A* | *N/A* | **MET** | `scripts/eval/eval_audit_completeness.py` |
| **Exception Detection Recall** | `recall >= 95.0%` | **96.7%** (29/30) | **100.0%** (30/30) | *N/A* | **MET** | `scripts/eval/eval_exceptions.py` (60 cards each) |
| **Correct Escalation Rate** | `recall >= 95.0%` | **96.7%** (29/30) | **100.0%** (30/30) | *N/A* | **MET** | `scripts/eval/eval_exceptions.py` (60 cards each) |
| **Exception Precision** | *No target* | **100.0%** (29/29) | **83.3%** (30/36) | *N/A* | **NO TARGET** | `scripts/eval/eval_exceptions.py` (30 clean cards) |
| **Exception Specificity** | *No target* | **100.0%** (30/30) | **80.0%** (24/30) | *N/A* | **NO TARGET** | `scripts/eval/eval_exceptions.py` (30 clean cards) |
| **RAG Grounded Hit@1 Rate** | `hit1 >= 90.0%` | **76.0%** (19/25) | **52.0%** (13/25) | **45.0%** (9/20) | **NOT MET** | `scripts/eval/eval_rag.py` |
| **RAG Retrieval Hit@3 Rate** | `hit3 >= 90.0%` | **80.0%** (20/25) | **60.0%** (15/25) | **50.0%** (10/20) | **NOT MET** | `scripts/eval/eval_rag.py` |
| **RAG Mean Reciprocal Rank (MRR)** | *No target* | **0.7800** | **0.5600** | **0.4750** | **NO TARGET** | `scripts/eval/eval_rag.py` |
| **RAG Correct Abstention Rate** | `abstention >= 90.0%`| **73.3%** (11/15) | **100.0%** (5/5) | **60.0%** (6/10) | **NOT MET** | `scripts/eval/eval_rag.py` (Out-of-domain) |
| **RAG Abstention Precision** | *No target* | **68.8%** (11/16) | **33.3%** (5/15) | **37.5%** (6/16) | **NO TARGET** | `scripts/eval/eval_rag.py` |
| **RAG Retrieval Latency** | `< 1000ms` | **82.9ms** | **23.3ms** | **24.8ms** | **MET** | `scripts/eval/eval_rag.py` |
| **RAG Cross-Portal Leakage** | `0` | **0** | **0** | **0** | **MET** | `backend/tests/test_rag.py` |
| **OCR National ID Field $F_1$** | `field F1 >= 90.0%` | **87.5%** | *N/A* | *N/A* | **NOT MET** | `scripts/eval/eval_ocr_extraction.py` (40 cards) |
| **OCR Citizen Name Field $F_1$** | `field F1 >= 90.0%` | **62.5%** | *N/A* | *N/A* | **NOT MET** | `scripts/eval/eval_ocr_extraction.py` (40 cards) |
| **OCR Address Field $F_1$** | `field F1 >= 90.0%` | **50.0%** | *N/A* | *N/A* | **NOT MET** | `scripts/eval/eval_ocr_extraction.py` (40 cards) |
| **OCR Factory Code Field $F_1$** | `field F1 >= 90.0%` | **90.0%** | *N/A* | *N/A* | **MET** | `scripts/eval/eval_ocr_extraction.py` (40 cards) |

---

## 3. Empirical Benchmark Details

### 3.1 RAG Semantic Retrieval Benchmark
- **Model:** `intfloat/multilingual-e5-small` (384-dimensional dense semantic vectors, offline cached).
- **Threshold Policy:** `RAG_SIMILARITY_THRESHOLD = 0.75` (calibrated on DEV to balance in-domain retrieval against out-of-domain abstention).
- **General Normalization:** All question-derived synonym dictionaries and keyword substitution rules were removed. `query_normalizer.py` applies only general Arabic diacritic (tashkeel) removal and whitespace normalization.
- **DEV Partition (N=40: 25 In-Domain, 15 Out-of-Domain):**
  - Hit@1: 76.0% (19/25)
  - Hit@3: 80.0% (20/25)
  - MRR: 0.7800
  - Abstention Recall: 73.3% (11/15)
  - Abstention Precision: 68.8% (11/16, with 5 in-domain queries false-positive abstaining)
- **Held-Out Partition 1 (N=30: 25 In-Domain, 5 Out-of-Domain):**
  - Hit@1: 52.0% (13/25)
  - Hit@3: 60.0% (15/25)
  - MRR: 0.5600
  - Abstention Recall: 100.0% (5/5)
  - Abstention Precision: 33.3% (5/15, with 10 in-domain queries scoring $< 0.75$)
- **New Held-Out Partition 2 (Colloquial Egyptian, Typos, Fragments; N=30: 20 In-Domain, 10 Out-of-Domain):**
  - Hit@1: 45.0% (9/20)
  - Hit@3: 50.0% (10/20)
  - MRR: 0.4750
  - Abstention Recall: 60.0% (6/10)
  - Abstention Precision: 37.5% (6/16, with 10 in-domain queries false-positive abstaining)
  - Confusion Matrix: True Positives = 6, False Negatives = 4, False Positives = 10, True Negatives = 10.
  - Cross-Portal Leakage: 0 (Strict portal isolation verified).

### 3.2 Exception Detection & Escalation Benchmark
- **DEV Corpus (60 Synthetic Cards: 30 Clean, 30 Planted Exceptions):**
  - Exception Detection Recall: **96.7%** (29/30) $\ge 95.0\%$ (**MET**).
  - Correct Escalation Rate: **96.7%** (29/30) (**MET**).
  - Precision: **100.0%** (29/29).
  - Specificity: **100.0%** (30/30).
  - False Negatives: 1 (`card_mismatch_24`, Category: `MISSING_FIELD_NAME`).
- **HELD-OUT Corpus (60 Synthetic Cards: 30 Clean, 30 Planted Exceptions):**
  - Generated with fresh seed and unchanged generator logic (`scratch/generate_held_out_60_cards.py`).
  - Evaluated ONCE (`scratch/evaluate_held_out_60.py`).
  - Exception Detection Recall: **100.0%** (30/30) $\ge 95.0\%$ (**MET**).
  - Correct Escalation Rate: **100.0%** (30/30) (**MET**).
  - Precision: **83.3%** (30/36).
  - Specificity: **80.0%** (24/30).
  - False Negatives by Category: **0** (Zero false negatives across all categories: governorate mismatch, birthdate mismatch, invalid ID structure, missing fields, and optical degradation were 100% escalated to human review).
  - False Positives: 6 clean cards with tight margins flagged `LOW_OCR_CONFIDENCE` or missing field due to OCR font rendering noise, safely routing to human review.

### 3.3 OCR Field Extraction $F_1$ Benchmark (40 Cards)
- **National ID Field $F_1$:** **87.5%** (Clean: 100%, Glare: 90%, Blur: 80%, Shadow: 80%) -> **NOT MET**.
- **Citizen Name Field $F_1$:** **62.5%** (Clean: 90%, Glare: 60%, Blur: 40%, Shadow: 60%) -> **NOT MET**.
- **Residential Address Field $F_1$:** **50.0%** (Clean: 80%, Glare: 50%, Blur: 30%, Shadow: 40%) -> **NOT MET**.
- **Factory Code Field $F_1$:** **90.0%** (Clean: 100%, Glare: 90%, Blur: 80%, Shadow: 90%) -> **MET**.
- **Human Review Routing Rate:** 55.0% of degraded card images routed to compliance queue.
- **Statement on Preprocessing:** No custom image preprocessing pipeline (super-resolution, localized contrast equalization, or morphological binarization) was built. The platform relies on raw images passed to PaddleOCR Arabic mobile model, which explains why cursive Arabic name and address extraction targets are not met under blur and glare.

---

## 4. Architectural Scope Checklist

| # | Handbook Scope Requirement | Status | Evidence File Path | Automated Test Evidence |
|---|---|:---:|---|---|
| **1** | **Four Flows:** KYC data update, Account opening (draft $\to$ review), Card request (queue + status), Complaint intake (classification + suggested team + draft reply) | **IMPLEMENTED** | `backend/app/api/v1/customer.py`<br/>`backend/app/api/v1/employee.py` | `tests/test_simulated_requests.py`<br/>`tests/test_complaint_intelligence.py`<br/>`tests/test_kyc_document_ai.py` |
| **2** | **Document AI:** Extraction of name, address, synthetic ID, expiry date; field metadata (doc/page/region/bbox); missing/mismatch detection between two documents | **IMPLEMENTED** | `backend/app/services/image_pipeline.py`<br/>`backend/app/services/kyc_checks.py`<br/>`backend/app/services/document_matching.py` | `tests/test_ocr.py`<br/>`tests/test_kyc_document_ai.py`<br/>`tests/test_document_matching.py` |
| **3** | **Deterministic Rules Deciding Completeness/Routing:** LLM cannot change rules or create approvals | **IMPLEMENTED** | `backend/app/services/request_rules.py`<br/>`backend/app/services/ops_agent.py` | `tests/test_simulated_requests.py`<br/>`tests/test_adversarial_agent.py` |
| **4** | **RAG with Policy Version + Source & Abstention:** Versioned citations, portal filtering, out-of-scope abstention | **IMPLEMENTED** | `backend/app/services/rag.py`<br/>`backend/app/services/vector_store.py` | `tests/test_rag.py` |
| **5** | **Agent with Tool Allowlist:** Read status, create draft, suggest queue, request review. No financial/permission actions | **IMPLEMENTED** | `backend/app/services/ops_agent.py`<br/>`backend/app/api/v1/agent.py` | `tests/test_adversarial_agent.py` |
| **6** | **Workflow State & Next Owner:** State visualization, next operational owner, approve/reject/request-more-info UI screen | **IMPLEMENTED** | `frontend/src/portals/employee/EmployeePortal.tsx` | `tests/test_simulated_requests.py` |
| **7** | **Immutable Audit Trail:** Every state change, approval, policy/model version logged. Zero secrets/PII in logs | **IMPLEMENTED** | `backend/app/models/audit.py`<br/>`backend/app/services/ops_agent.py` | `tests/test_kyc_document_ai.py`<br/>`tests/test_mvp.py` |
| **8** | **Small KPI Dashboard:** Operational metrics, compliance KPIs, benchmark summaries | **IMPLEMENTED** | `backend/app/services/kpi_service.py`<br/>`frontend/src/portals/employee/EmployeePortal.tsx` | `tests/test_kpi_service.py` |
| **9** | **Mock APIs Only / Zero External Network Dependency:** Ollama local only; no external cloud calls at runtime | **IMPLEMENTED** | `backend/app/core/config.py`<br/>`backend/app/services/rag.py` | `tests/test_health.py`<br/>`tests/test_rag.py` |
| **10** | **Failure Scenarios Covered by Tests:** Timeout, failing mock API, unsupported file, idempotency | **IMPLEMENTED** | `backend/tests/test_ocr_security.py`<br/>`backend/tests/test_simulated_requests.py`<br/>`backend/tests/test_production_guards.py` | `tests/test_ocr_security.py`<br/>`tests/test_production_guards.py` |

---

## 5. Known Limitations

1. **OCR Arabic Name & Address $F_1$ Deficit:**
   - On synthetic images with blur or glare, Arabic cursive text recognition drops sharply (Name $F_1 = 62.5\%$, Address $F_1 = 50.0\%$).
   - Image enhancement preprocessing (super-resolution, morphological binarization) was not built. The system compensates by deterministically routing degraded cards to human compliance review (`is_escalated: true`).
2. **RAG Hit@1 on Colloquial Phrasing & Out-of-Domain Abstention:**
   - While `intfloat/multilingual-e5-small` significantly outperforms character feature hashing, short fragments, misspelled queries, and heavy Egyptian dialect phrasing without keyword expansion achieve **45.0% to 52.0% Hit@1** at threshold 0.75.
   - At threshold 0.75, abstention precision is between 33% and 38% because valid queries with lower similarity scores trigger false-positive abstentions.
3. **Statutory Expiry Date Rule Assumption:**
   - Egyptian National ID expiry dates are computed assuming a 7-year validity period from synthetic issue dates.
   - *Legal Notice:* This is a **training assumption on synthetic data, not legal advice** or official Civil Status Ministry policy.
4. **Permanent NOT_VERIFIED Identity Status:**
   - NileOps is a digital banking operations simulation platform without integration into live CBE core settlement switches or the Ministry of Interior Civil Status database.
   - All identities remain permanently tagged as `NOT_VERIFIED`.
5. **No Production Cloud Deployment:**
   - The platform is engineered and verified strictly for local developer native execution (Windows/Linux with Docker). CI/CD pipelines, Kubernetes helm charts, and public hosting infrastructure are out of scope.
