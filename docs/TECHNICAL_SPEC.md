# Technical Specification
## AI-Assisted Clinical Coder — CMS-HCC Version 28
**Version:** 1.1  
**Date:** March 31, 2026  
**Audience:** Engineering Team  
**Status:** Draft — Updated for 90+ condition V28_MAP and two-step OCR pipeline

---

## 1. System Overview

### Architecture
Single-tier web application built with Streamlit (Python). All processing is server-side. No persistent database in v1.0 — state is managed in Streamlit session state per user session. AI inference is delegated to OpenAI GPT-5 via Replit AI Integrations (managed billing, no customer API key required).

```
Browser (User)
    │
    ▼
Streamlit App (Python 3.11, port 5000)
    │
    ├── PyMuPDF (fitz)         — PDF → image conversion
    ├── OpenAI Python SDK      — GPT-5 vision OCR + condition extraction
    └── Streamlit Session State — per-session data store
```

---

## 2. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.11 |
| Web Framework | Streamlit | 1.55.0 |
| AI Provider | OpenAI (via Replit AI Integrations) | GPT-5 |
| PDF Processing | PyMuPDF (fitz) | 1.27.x |
| Data Manipulation | pandas | 2.3.x |
| HTTP Client | httpx (via openai SDK) | 0.28.x |
| Hosting | Replit Autoscale | — |

---

## 3. File Structure

```
/
├── app.py                  # Main application (single-file Streamlit app)
├── requirements.txt        # Python dependencies
├── replit.md               # Project documentation
├── .replit                 # Replit workflow & deployment config
└── docs/
    ├── PRD.md
    ├── TECHNICAL_SPEC.md
    └── AI_EVAL_MATRIX.md
```

---

## 4. Core Data Models

### 4.1 V28_MAP — HCC Condition Registry
```python
V28_MAP = {
    "<Condition Name>": {
        "hcc": "<HCC Code>",       # CMS-HCC V28 category number
        "coef": <float>,           # RAF coefficient (community, non-dual)
        "icd10": "<ICD-10-CM>"     # Primary ICD-10-CM code
    }
}
```

**Coverage: 90+ conditions across all major CMS-HCC V28 disease groups:**

| Disease Group | Example Conditions |
|---|---|
| Diabetes | Without complications → DKA, neuropathy, nephropathy, retinopathy, foot ulcer |
| Chronic Kidney Disease | Stage 3a through ESRD/Dialysis and Renal Transplant |
| Heart Conditions | CHF (systolic/diastolic), CAD, Acute MI, AFib, Cardiomyopathy, Cardiac Arrest |
| COPD & Lung Disease | COPD, COPD exacerbation, Pulmonary Fibrosis, Pulmonary HTN, Chronic Resp Failure |
| Cancer | Metastatic (RAF 2.488), Lung, Breast, Colorectal, Lymphoma, Leukemia, Remission |
| Stroke & Neurological | Ischemic/Hemorrhagic Stroke, Sequelae, TIA, Hemiplegia, MS, Parkinson's, Epilepsy |
| Vascular Disease | PVD, Atherosclerosis ± Gangrene, Aortic Aneurysm, DVT, Pulmonary Embolism |
| HIV/AIDS | HIV Infection, AIDS |
| Major Psychiatric | Schizophrenia, Bipolar, Major Depression, Dysthymia, Anxiety, PTSD |
| Substance Use | Alcohol, Opioid, Cocaine, Cannabis, Polysubstance Use Disorders |
| Pressure Ulcers | Stages 2, 3 (necrosis), 4, Unstageable |
| Amputations | Lower, Upper, Bilateral |
| Dementia | With/without behavioral, Alzheimer's, Vascular Dementia |
| IBD | Crohn's Disease, Ulcerative Colitis |
| Rheumatoid/Inflammatory | RA, Psoriatic Arthritis, SLE, Inflammatory Arthritis |
| Liver Disease | Cirrhosis, Hepatitis B/C, Liver Failure/Encephalopathy |
| Opportunistic Infections | PCP, Cryptococcal Meningitis, CMV, Candidiasis, Toxoplasmosis |
| Other | Obesity, Morbid Obesity, Malnutrition, Sepsis, Diabetic Foot Ulcer, Chronic Pancreatitis |

RAF coefficients are sourced from the CMS-HCC Version 28 final model (community, non-dual, non-aged segment). Each entry maps the human-readable condition name (used throughout the UI) to its HCC category, primary ICD-10-CM code, and coefficient.

### 4.2 HCC Item (session state list)
```python
{
    "id": int,
    "term": str,       # Must be a key in V28_MAP
    "status": str      # "Pending" | "Confirmed" | "Rejected"
}
```

### 4.3 Patient Details (session state dict)
```python
{
    "patient_name": str,
    "date_of_birth": str,
    "mrn": str,
    "insurance_id": str,
    "date_of_service": str,
    "provider_name": str,
    "practice_name": str
}
```

### 4.4 OCR Result (session state dict)
```python
{
    "extracted_text": str,
    "detected_conditions": list[str],
    "clinical_summary": str,
    "patient_details": dict   # matches Patient Details shape
}
```

---

## 5. Session State Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `hcc_data` | list | `[]` | List of HCC items |
| `ocr_result` | dict\|None | `None` | Last OCR API response |
| `uploaded_image_bytes` | list\|None | `None` | List of `(bytes, mime_type)` tuples |
| `case_status` | str\|None | `None` | `"confirmed"` \| `"further_docs"` \| `None` |
| `case_timestamp` | str\|None | `None` | Human-readable finalization timestamp |
| `patient_details` | dict | empty strings | Extracted/edited patient info |
| `patient_confirmed` | bool | `False` | Whether coder confirmed patient details |
| `clarification_sent` | bool | `False` | Whether clarification request was sent |
| `clarification_condition` | str\|None | `None` | Selected condition for clarification |
| `cms_doc` | str\|None | `None` | Generated CMS submission text |

---

## 6. Key Functions

### 6.1 `pdf_to_images(pdf_bytes: bytes) -> list[tuple[bytes, str]]`
- Uses `fitz.open()` to parse PDF from bytes
- Renders each page at 2x zoom (`fitz.Matrix(2.0, 2.0)`) for OCR quality
- Returns list of `(png_bytes, "image/png")` tuples
- One tuple per page

### 6.2 `ocr_clinical_note(image_bytes: bytes, mime_type: str) -> dict`

Uses a **two-step pipeline** designed to maximize both accuracy and speed:

**Step 1 — Lean Vision Call (`max_completion_tokens=2048`)**
- Base64-encodes the image and sends to GPT-5 Vision with a minimal prompt
- Prompt does NOT include the 90+ condition checklist — keeps vision call fast
- Extracts: verbatim text transcription, raw diagnoses as written, medications, clinical summary, patient details
- Returns intermediate OCR dict (`extracted_text`, `raw_diagnoses`, `medications`, `patient_details`, `clinical_summary`)

**Step 2 — Text-Only Matching Call (`max_completion_tokens=1024`)**
- No image — sends only the transcribed text + raw diagnoses + medications to GPT-5
- Full 90+ condition V28_MAP list is included here (no image = much faster inference)
- GPT-5 maps clinical content to exact V28_MAP condition names
- Returns `detected_conditions` list of exact V28_MAP keys

**Architecture rationale:** Vision inference with a large prompt + high token budget (previous design: 8,192 tokens) was the primary source of 3-minute response times. The two-step approach decouples image reading from condition matching — the vision step stays fast (lean prompt, lower token limit), and the matching step runs as cheap text inference. Total end-to-end time: ~45–90 seconds.

Returns merged dict matching OCR Result shape.

### 6.3 `merge_ocr_results(results: list[dict]) -> dict`
- Merges results across multiple PDF pages
- Concatenates extracted text with page separators
- Unions detected conditions (set merge)
- Concatenates summaries
- Takes first non-empty value per patient detail field across pages

### 6.4 `generate_cms_submission(patient, hcc_data, total_raf, timestamp) -> str`
- Generates fixed-width text document
- Includes: Submission ID (timestamp-based), patient demographics, confirmed ICD-10 codes with HCC numbers and coefficients, RAF score breakdown, interaction bonus line if applicable, attestation citing 45 CFR § 153.610
- Returns formatted string for display and download

---

## 7. RAF Score Computation

```python
base_raf = 0.350
hcc_sum = sum(V28_MAP[term]["coef"] for term in confirmed_terms if term in V28_MAP)
# Interaction bonus: any Diabetes variant + any CHF variant
has_dm  = any(t.startswith("Diabetes") for t in confirmed_terms)
has_chf = any(t in confirmed_terms for t in
              ["Congestive Heart Failure", "Systolic Heart Failure", "Diastolic Heart Failure"])
interaction_bonus = 0.112 if (has_dm and has_chf) else 0.0
total_raf = base_raf + hcc_sum + interaction_bonus
```

**Interaction bonuses implemented:** Any Diabetes variant + Any CHF variant (Congestive/Systolic/Diastolic) → +0.112  
**Planned for future:** Full CMS V28 interaction table (HHS-HCC 2024 model interactions, including CKD × Diabetes, CHF × COPD, etc.)

---

## 8. AI Integration

### Provider
Replit AI Integrations (OpenAI-compatible endpoint)

### Environment Variables
| Variable | Description |
|----------|-------------|
| `AI_INTEGRATIONS_OPENAI_API_KEY` | Managed dummy key (auto-injected by Replit) |
| `AI_INTEGRATIONS_OPENAI_BASE_URL` | Proxy base URL (auto-injected by Replit) |

### Model
`gpt-5` — Released August 7, 2025. Supports image inputs via `image_url` content type.

### Prompt Design

**Step 1 — Vision prompt (lean, image-focused):**
- Role: Medical transcriptionist
- Task: Transcribe note text, list raw diagnoses and medications, extract patient details
- No condition checklist — keeps prompt short for fast vision inference
- Output format: `json_object`
- `max_completion_tokens=2048`
- Temperature: Not set (defaults to 1, required for gpt-5)

**Step 2 — Text-only matching prompt:**
- Role: CMS-HCC V28 coding specialist
- Input: Transcribed text + raw diagnoses + medications from Step 1
- Task: Map clinical content to exact V28_MAP condition names (full 90+ list provided)
- Constraint: Only return exact condition names from the list; omit uncertain conditions
- Output format: `json_object` (`{"detected_conditions": [...]}`)
- `max_completion_tokens=1024`
- Temperature: Not set

### Error Handling
```python
except Exception as e:
    if "FREE_CLOUD_BUDGET_EXCEEDED" in str(e):
        st.error("Cloud budget exceeded")
    else:
        st.error(f"Error: {str(e)}")
```

---

## 9. UI Layout

### Pre-upload State
```
Header
Upload Expander (expanded)
─────────────────────────────
[Case Summary]    [HCC Worklist]
─────────────────────────────
Finalize Case
```

### Post-upload State (3-column review)
```
Header
Upload Expander (collapsed)
OCR Results Expander
─────────────────────────────────────────
[Clinical Note] [Case Summary] [HCC Worklist]
   (image)       (patient form)  (conditions)
─────────────────────────────────────────
Finalize Case
  → CMS Submission Panel (if confirmed)
  → Clarification Panel (if further docs)
```

---

## 10. Deployment Configuration

```toml
# .replit [deployment] section
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000",
       "--server.address", "0.0.0.0", "--server.headless", "true"]
```

**Workflow command:**
```
streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
```

---

## 11. Known Limitations & Future Work

| Item | Description | Priority |
|------|-------------|----------|
| Session persistence | All state lost on page refresh (no DB) | High |
| Single-user sessions | No multi-user support; each browser tab is independent | High |
| PHI handling | No encryption at rest; data only in memory | High |
| Interaction bonuses | Only Diabetes×CHF implemented; full V28 interaction table has ~20 pairs | Medium |
| Real CMS API | Submission is document-only; no live RAPS/EDS API call | Medium |
| Provider portal | Clarification request is simulated only | Medium |
| HCC code expansion | 90+ conditions covered; full CMS V28 model has 115 HCC categories — remaining gap is ~25 rare/administrative codes | Low |
| Audit trail | No logging of coder actions | Low |
| PDF text layer | Currently renders to image even for digital PDFs (slower but required for handwriting support) | Low |
| OCR response time | Two-step pipeline targets ~45–90 sec; further reduction possible with caching or streaming | Low |

---

## 12. Security Considerations

- No PHI is written to disk or logged
- Session state is in-memory only (cleared on session end)
- OpenAI API calls transmit image data — ensure network security in production
- GitHub PAT stored as Replit Secret (not in source code)
- Production: Add authentication layer (SSO/OAuth) before clinical use
- HIPAA BAA required with OpenAI / Replit for production PHI processing
