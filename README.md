# AI-Assisted Clinical Coder — CMS-HCC Version 28
**Medicare Advantage Risk Adjustment Prototype**  
Built with GPT-5 Vision · Streamlit · Python · Replit Autoscale

---

## What It Does

This tool automates the end-to-end HCC (Hierarchical Condition Category) coding workflow for Medicare Advantage risk adjustment. A coder uploads a handwritten or printed clinical note; the system reads it, extracts diagnoses, maps them to CMS-HCC Version 28 codes, computes the RAF score, and generates a CMS-ready RAPS/EDS submission document — all within a single web interface.

It also handles the **provider documentation loop**: when a diagnosis lacks sufficient supporting documentation, the tool auto-generates a condition-specific provider query pre-filled with the exact clinical evidence required, sending it to the provider in under 60 seconds.

---

## Key Capabilities

### Comprehensive HCC Coverage — 90+ Conditions Across All Major Disease Groups

The V28_MAP condition registry covers the full spectrum of clinically significant HCC categories from the CMS-HCC Version 28 model:

| Disease Group | Conditions Covered |
|---|---|
| **Diabetes** | Without complications, with chronic/acute complications, DKA, neuropathy, nephropathy, retinopathy, foot ulcer |
| **Chronic Kidney Disease** | Stages 3a/3b/4/5, ESRD/Dialysis, Renal Transplant |
| **Heart Conditions** | CHF (systolic/diastolic), CAD, Acute MI, AFib, Flutter, Cardiomyopathy, Cardiac Arrest, Valvular disease |
| **COPD & Lung Disease** | COPD, COPD exacerbation, Pulmonary Fibrosis, Pulmonary HTN, Chronic Resp Failure, Asthma, Bronchiectasis |
| **Cancer** | Metastatic, Lung, Breast, Colorectal, Prostate, Lymphoma, Leukemia, Multiple Myeloma, Pancreatic, H&N, Remission |
| **Stroke & Neurological** | Ischemic/Hemorrhagic Stroke, Sequelae, TIA, Hemiplegia, MS, Parkinson's, Epilepsy, Neuropathy |
| **Vascular Disease** | PVD, Atherosclerosis ± Gangrene, Aortic Aneurysm, DVT, Pulmonary Embolism |
| **HIV/AIDS** | HIV Infection, AIDS (Advanced) |
| **Major Psychiatric** | Schizophrenia, Schizoaffective, Bipolar, Major Depression, Dysthymia, Anxiety, PTSD |
| **Substance Use** | Alcohol, Opioid, Cocaine, Cannabis, Polysubstance use disorders |
| **Pressure Ulcers** | Stages 2, 3 (necrosis), 4, Unstageable |
| **Amputations** | Lower limb, Upper limb, Bilateral |
| **Dementia** | With/without behavioral disturbance, Alzheimer's, Vascular Dementia |
| **Inflammatory Bowel Disease** | Crohn's Disease, Ulcerative Colitis |
| **Rheumatoid/Inflammatory** | Rheumatoid Arthritis, Psoriatic Arthritis, SLE, Inflammatory Arthritis |
| **Liver Disease** | Cirrhosis, Alcoholic Cirrhosis, Hepatitis B/C, Liver Failure/Encephalopathy |
| **Opportunistic Infections** | PCP, Cryptococcal Meningitis, CMV, Systemic Candidiasis, Toxoplasmosis |
| **Other High-RAF Conditions** | Obesity, Morbid Obesity, Malnutrition, Sepsis, Osteoporosis with Fracture, Chronic Pancreatitis, Diabetic Foot Ulcer |

Each condition includes the CMS-HCC V28 category number, primary ICD-10-CM code, and RAF coefficient.

### Two-Step AI OCR Pipeline (Optimized for Speed)
The AI processing uses a purpose-built two-step pipeline to maximize both accuracy and speed:

1. **Step 1 — Lean Vision Call:** GPT-5 Vision reads the uploaded image or PDF and performs OCR-only extraction: full text transcription, raw diagnoses as written, medications, patient details, and a clinical summary. This call uses a minimal prompt (no condition checklist) to keep the vision call fast.

2. **Step 2 — Text-Only Matching:** The transcribed text and extracted diagnoses are passed to a second, image-free GPT-5 call that maps clinical findings to the 90+ condition V28_MAP. Text-only inference is significantly faster than vision calls, keeping total processing time well under 90 seconds.

This architecture means coder-facing response time scales independently from the size of the condition library — adding more conditions to V28_MAP does not slow down the vision step.

### Full Workflow
- Upload handwritten or printed clinical notes (image or multi-page PDF)
- AI reads the note and pre-fills the HCC worklist and patient form
- Coder reviews the note side-by-side with AI-extracted data, confirming or rejecting each condition
- RAF score updates in real-time including CMS-defined interaction bonuses (e.g., Diabetes × CHF = +0.112)
- One-click CMS RAPS/EDS submission document generation (with 45 CFR §153.610 attestation)
- Condition-specific provider query composer for the HCP documentation loop — draft and send in under 60 seconds

---

## Technology Stack

| Layer | Technology |
|---|---|
| AI Vision & OCR | GPT-5 Vision (OpenAI, via Replit AI Integrations) |
| HCC Engine | CMS-HCC Version 28 — 90+ conditions, ICD-10-CM, RAF coefficients |
| PDF Rendering | PyMuPDF (fitz) — multi-page support, 2× zoom for OCR quality |
| Web Framework | Streamlit (Python 3.11) |
| Submission Generator | Python — RAPS/EDS format, CMS attestation |
| Deployment | Replit Autoscale |
| Version Control | GitHub |

---

## Getting Started (Development)

The app runs automatically on Replit. For local development:

```bash
pip install streamlit openai pymupdf pandas reportlab
streamlit run app.py --server.port 5000
```

Required environment variables (auto-injected by Replit AI Integrations):
- `AI_INTEGRATIONS_OPENAI_API_KEY`
- `AI_INTEGRATIONS_OPENAI_BASE_URL`

---
## Demo

- **Demo Video:** [meghna1298-cyber.github.io/hcc-prototype](https://meghna1298-cyber.github.io/hcc-prototype/)
- **Live App:** https://hcc-prototype-1--meghna1298.replit.app/ 

---

## Documentation

| Document | Description |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Product Requirements Document |
| [`docs/TECHNICAL_SPEC.md`](docs/TECHNICAL_SPEC.md) | Technical Specification |
| [`docs/AI_EVAL_MATRIX.md`](docs/AI_EVAL_MATRIX.md) | AI Evaluation Matrix |
| [`docs/HCC_Product_Overview.pdf`](docs/HCC_Product_Overview.pdf) | 2-page executive product overview |

---

*Prototype built for Medicare Advantage Risk Adjustment · CMS-HCC Version 28 · March 2026*
