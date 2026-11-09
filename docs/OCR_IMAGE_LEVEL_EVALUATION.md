# NileOps V4 — Image-Level OCR Evaluation & Measurement Report
**Document:** `docs/OCR_IMAGE_LEVEL_EVALUATION.md`  
**System:** NileOps V4 Document Intelligence Pipeline  
**Execution Timestamp:** 2026-11-08T23:25:00+02:00 (21:25:00 UTC)  
**Dataset:** 40 Code-Generated Synthetic Egyptian National ID Cards (`data/synthetic_cards/`, git-ignored)  
**Test Suite:** 72 tests passed vs `nileops_test` (100% pass rate)  
**Security Posture:** Zero Real-Person PII, Zero Git Commits, Zero Git Pushes, Zero Database Deletions  

---

## 1. Executive Summary & Security Compliance

This report details the image-level OCR measurement, diagnosis, dataset expansion (40 cards), and algorithmic tuning conducted for the NileOps National ID Document Intelligence system (`ImageOCRPipeline`).

### 1.1 Strict Synthetic Isolation & Security Remediation
- **Hard Rule Compliance:** Under strict operational instructions, `C:\AI\NileOps_V4\tests\ocr\fixtures` was never opened, read, or listed during evaluation.
- **Security Test Remediation:** In `backend/tests/test_ocr_security.py` (line 70), a historical dependency that read `tests\ocr\fixtures\card_01.jpg` was removed. The test was rewritten to validate PII masking using code-generated synthetic cards from `data/synthetic_cards/`.
- **Repository-Wide Sanitization:** All test and script references to `tests/ocr/fixtures` across `backend/tests/` and `backend/app/scripts/` were eliminated and redirected to `data/synthetic_cards/`.
- **Database Persistence Audit:** Verification of dev database tables (`kyc_verifications`, `audit_logs`) and file storage (`data/kyc_uploads/`) confirmed that zero real card images or authentic citizen records exist or were persisted.

---

## 2. Dataset Architecture (40 Synthetic Cards)

A ground-truth labeled benchmark dataset of **40 cards** was generated purely in code and stored under `data/synthetic_cards/` with ground-truth annotations in `data/synthetic_cards/manifest.json`.

### 2.1 Visual Design Realism
1. **Geometric Pyramid Watermark:** Drawn in code using vector wireframe lines and masonry stepping in subtle pastel sage-green (`#DEEAE2`) with guilloche-style reference waves across the background.
2. **Neutral Gray Avatar Silhouette:** Standardized geometric head-and-shoulder avatar in `#A0AFA8` with a `"PHOTO FIXTURE"` text stamp, completely eliminating photographic facial data.
3. **Eastern Arabic Numerals:** Integrated across Egyptian address strings (street numbers, building numbers, e.g., `١٢`, `٤٥`, `١٠٥`).
4. **Valid Egyptian National ID Formats:** 14-digit synthetic numbers with authentic century codes (`2`, `3`), valid birthdates, Egyptian governorate administrative codes (`01`–`35`), and gender sequence digits.

### 2.2 Condition Distribution ($N=40$)
- **Clean ($N=10$, Cards 01–10):** Pristine rendering, high contrast, reference baseline.
- **Blur ($N=6$, Cards 11–16):** Gaussian blur progression ($r \in \{1.0, 1.8, 2.5, 3.2, 4.0, 5.0\}$).
- **Rotation & Perspective ($N=8$, Cards 17–24):** Affine angles ($+3^\circ, -3^\circ, +6^\circ, -6^\circ, +10^\circ, -10^\circ, +14^\circ$) and 3D keystone projective tilt.
- **Glare & Specular Reflection ($N=5$, Cards 25–29):** Top-right flash, center hotspot, diagonal daylight washout, bottom stripe, photo corner glare.
- **Low-Light & Noise ($N=6$, Cards 30–35):** Underexposure (brightness $0.35$–$0.45$), Gaussian sensor noise ($\sigma=25$), salt-and-pepper noise ($4\%$), low contrast ($\text{std} < 20$).
- **Partial Occlusion ($N=5$, Cards 36–40):** Masking tape over address, thumb shadow over bottom-left corner, dark header bar, top paper clip, barcode sticker over ID tail.

---

## 3. Step 2 Root-Cause Diagnosis (Name & Address Failures)

### 3.1 Initial Failure Diagnosis
In Phase 1b, raw clean cards produced degraded results where citizen Name was truncated or reported as 70% confidence, and Address had low exact match.

Investigation of the raw PaddleOCR engine output revealed two distinct root causes:
1. **Fixture Rendering (Phase 1b cards):** Pillow on Windows lacks `libraqm` (`features.check('raqm') == False`). Basic PIL `draw.text` rendered Arabic text left-to-right as disconnected, isolated Unicode characters. PaddleOCR read the disjointed letters backwards (`'هلا دبع مي هارب إ روصنم دمحأ'`). Applying `arabic_reshaper` + `python-bidi` with Tahoma/Segoe UI fixed this at the rendering level, yielding individual line confidences above $95\%$.
2. **Downstream Field Extraction Parser:** On clean reshaped cards, PaddleOCR detected the field lines with high fidelity:
   ```text
   [03] Score: 0.8903 | Box: [(758,122)->(824,150)] | Text: 'الاسم:'
   [04] Score: 0.9612 | Box: [(579,157)->(822,188)] | Text: 'طارق محمود حسن علي'
   [07] Score: 0.9958 | Box: [(757,212)->(824,238)] | Text: 'العنوان'
   [08] Score: 0.9323 | Box: [(387,252)->(821,276)] | Text: '١٢شارع قصر العيني السيدة زينبالقاهرة'
   [09] Score: 0.9739 | Box: [(714,313)->(823,337)] | Text: 'الرقم القومي'
   [10] Score: 0.9997 | Box: [(610,342)->(821,369)] | Text: '28804150101234'
   ```
   However, `extract_fields_from_ocr` only filtered administrative document headers (`جمهورية مصر العربية`), allowing the field labels `'الاسم:'`, `'العنوان'`, and `'الرقم القومي'` to be gathered into `name_candidates`. As a result, the parser emitted:
   `Name: 'الاسم: طارق محمود حسن علي العنوان الرقم القومي'`
   This contaminated Name Exact Match to **0.0%** across the board.

---

## 4. Quantitative BEFORE vs. AFTER Evaluation (40 Cards)

### 4.1 Side-by-Side Performance Matrix
*BEFORE* reflects the pipeline prior to field label filtering. *AFTER* reflects the tuned pipeline incorporating structural label discard (`CARD_FIELD_LABELS`) and token prefix stripping.

| Condition | $N$ | National ID EM | National ID CER | Name EM (BEFORE) | Name EM (AFTER) | Name CER (AFTER) | Address EM | Address CER | Factory Code EM | % Human Review |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ALL (Overall)** | **40** | **87.5%** | **10.2%** | **0.0%** | **62.5%** | **30.8%** | **50.0%** | **12.5%** | **90.0%** | **12.5%** |
| `clean` | 10 | 100.0% | 0.0% | 0.0% | **90.0%** | **10.0%** | 60.0% | 1.7% | 100.0% | 0.0% |
| `blur` | 6 | 50.0% | 34.5% | 0.0% | **0.0%** | **85.6%** | 16.7% | 39.4% | 66.7% | 33.3% |
| `rotation_perspective` | 8 | 87.5% | 12.5% | 0.0% | **75.0%** | **25.0%** | 62.5% | 13.2% | 87.5% | 12.5% |
| `glare` | 5 | 100.0% | 0.0% | 0.0% | **60.0%** | **38.4%** | 40.0% | 1.8% | 100.0% | 0.0% |
| `low_light_noise` | 6 | 100.0% | 0.0% | 0.0% | **50.0%** | **34.1%** | 50.0% | 4.0% | 83.3% | 0.0% |
| `partial_occlusion` | 5 | 80.0% | 20.0% | 0.0% | **80.0%** | **4.0%** | 60.0% | 21.4% | 100.0% | 40.0% |

### 4.2 Key Performance Shifts
1. **Name Extraction:** On clean cards, Name Exact Match jumped from **0.0%** to **90.0%**, with Character Error Rate dropping from $100.0\%$ to **$10.0\%$**. Across all 40 cards (including heavy blur and occlusions), Name Exact Match improved from $0.0\%$ to **$62.5\%$**.
2. **National ID Reliability:** Maintained **100% exact match** on clean, glare, and low-light cards. Across the full 40-card dataset, National ID achieved **87.5% EM** with **90.0% extraction recall**.
3. **Factory Code:** Achieved **90.0% EM** and **10.0% CER** across the entire dataset (100% on clean, glare, and occlusion).
4. **Human Review Routing:** 5 of 40 cards ($12.5\%$) were routed to human review (`REQUIRES_HUMAN_REVIEW`):
   - Severe blur: `card_15` ($r=4.0$) and `card_16` ($r=5.0$)
   - Extreme skew: `card_23` ($+14^\circ$)
   - Critical field occlusion: `card_36` (tape over address) and `card_40` (barcode over National ID)

---

## 5. Detailed Breakdown of Failures & Edge Cases

### 5.1 Gaussian Blur Degradation ($r \ge 3.2$)
- At $r=1.0$ (`card_11`) and $r=1.8$ (`card_12`), the 14-digit National ID and Factory Code are extracted with 100% accuracy, while cursive Arabic diacritics begin to merge, increasing Name CER.
- At $r=2.5$ (`card_13`), digits remain recognizable ($100\%$ EM), but Arabic letter connections suffer.
- At $r=4.0$ (`card_15`) and $r=5.0$ (`card_16`), textline contrast falls below detector thresholds, causing total extraction failure. The system handles this gracefully by flagging low confidence and routing the cases to human review.

### 5.2 Address Tokenization & Spacing
- Address field presence recall reached **90.0%**, with very low character error rate (**1.7%** on clean cards, **12.5%** overall).
- Exact Match was **50.0%** overall (**60.0%** clean). The primary discrepancy is whitespace segmentation: PaddleOCR often merges street numbers and street prefixes (e.g., `'١٢شارع'` instead of `'١٢ شارع'`) and omits typographical hyphens between administrative segments.

### 5.3 Rotation & Perspective
- Skew angles up to $\pm 10^\circ$ (`card_21`, `card_22`) and keystone 3D perspective warp (`card_24`) are handled natively by PaddleOCR's textline orientation classifier with zero loss in National ID accuracy.
- At $+14^\circ$ (`card_23`), bounding box aspect ratio distortions lead to missing digit tokens, which routes the card to human review.

---

## 6. Honest Comparison to Handbook Target & Production Limitations

### 6.1 Evaluation Versus Handbook Target ($F_1 \ge 90\%$)
- **National ID Slot:** Precision = $97.2\%$, Recall = $90.0\%$, **$F_1 = 93.5\%$** $\rightarrow$ **Exceeds Target**.
- **Factory Code Slot:** Precision = $100.0\%$, Recall = $90.0\%$, **$F_1 = 94.7\%$** $\rightarrow$ **Exceeds Target**.
- **Citizen Name Slot:** Precision = $65.8\%$, Recall = $95.0\%$, **$F_1 = 77.7\%$** $\rightarrow$ **Below Target across degraded conditions** (Clean subset: $94.7\%$).
- **Address Slot:** Precision = $55.6\%$, Recall = $90.0\%$, **$F_1 = 68.7\%$** $\rightarrow$ **Below Target due to strict whitespace tokenization** (CER is $1.72\%$ on clean).

### 6.2 Critical Transferability Limitation (Synthetic vs. Authentic Layouts)
> [!WARNING]
> **Layout Transferability Caveat:**  
> The label-filtering heuristic (`CARD_FIELD_LABELS`) introduced in `image_pipeline.py` was specifically engineered around the synthetic fixture layout, where field labels like `"الاسم :"` and `"العنوان :"` precede data values.  
> Authentic Egyptian National ID cards issued by the Ministry of Interior do **NOT** print the label `"الاسم:"` on the card face. Instead, the citizen's 4-part name is positioned directly below the Republic header in a dedicated spatial band without a label prefix.  
> Consequently, the observed synthetic Name Exact Match improvement ($0\% \rightarrow 90\%$ clean) represents an operational baseline for structured synthetic testing, but **cannot be assumed to transfer directly to unconstrained authentic photo inputs** without implementing spatial region-of-interest (ROI) bounding box segmentation.

---

## 7. System Verification & Test Suite Evidence

### 7.1 Backend Test Suite Execution (`nileops_test`)
```text
C:\AI\NileOps_V4\backend\.venv\Scripts\python.exe -m pytest tests/ -q
........................................................................ [100%]
============================== warnings summary ===============================
5 warnings (FastAPI routing deprecations, Paddle ccache notice)
======================== 72 passed, 5 warnings in 55.03s =======================
```
- **Total Tests:** 72 passed, 0 failed, 0 skipped.
- **Security Tests:** `tests/test_ocr_security.py` (6 passed in 16.01s).

### 7.2 Database Entity Integrity (`nileops` Dev Database)
Row count verification confirms zero database records were modified or deleted:
- `users`: 7
- `accounts`: 4
- `transactions`: 4
- `complaints`: 21 (19 test, 2 non-test)
- `policy_documents`: 21
- `kyc_verifications`: 3
- `audit_logs`: 331
- `account_opening_requests`: 1
- `card_requests`: 1

### 7.3 Backend API Health Check
```json
{
  "status": "healthy",
  "service": "NileOps Backend",
  "version": "1.0.0",
  "database": "PostgreSQL 16"
}
```

