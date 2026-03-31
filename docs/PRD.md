# Product Requirements Document (PRD)
## AI-Assisted Clinical Coder — CMS-HCC Version 28
**Version:** 1.1  
**Date:** March 31, 2026  
**Organization:** Humana  
**Status:** Draft — Updated for expanded V28 condition coverage and optimized OCR pipeline

---

## 1. Executive Summary

The AI-Assisted Clinical Coder is a web-based tool designed to accelerate and improve the accuracy of HCC (Hierarchical Condition Category) coding for Medicare Advantage risk adjustment. Coders upload handwritten or printed clinical notes; the system reads them using AI-powered OCR, extracts patient demographics and diagnoses, maps them to CMS-HCC Version 28 codes, computes the RAF (Risk Adjustment Factor) score, and produces a CMS-ready submission document — all within a single workflow.

---

## 2. Problem Statement

### Current Pain Points
- Coders manually read paper or scanned clinical notes and look up ICD-10 codes
- High error rates from manual transcription of handwritten physician notes
- Slow turnaround time from chart receipt to RAF score submission
- Missed HCC conditions lead to under-coded RAF scores and revenue loss
- No structured feedback loop to physicians when documentation is insufficient
- CMS submission is a separate, manual process disconnected from the coding workflow

### Impact
- Average coder handles 30–50 charts per day; manual lookup adds 5–10 minutes per chart
- Under-coding is estimated to cost MA plans $1,000–$3,000 per member per year in risk adjustment revenue
- Audit risk from unsupported or inconsistent ICD-10 coding

---

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Reduce coding time per chart | Minutes per chart | < 3 min (from ~12 min) |
| Improve HCC capture rate | % of eligible HCCs captured | > 95% |
| Reduce coding errors | Error rate per 1,000 charts | < 5 errors |
| Accelerate CMS submission | Days from chart receipt to submission | Same day |
| Provider clarification response rate | % of clarification requests answered | > 80% within 5 days |

---

## 4. Users & Personas

### Primary: HCC Coder
- Certified Risk Adjustment Coder (CRC) or AAPC-certified coder
- Reviews 30–100 charts per day
- Needs fast, accurate condition identification and RAF computation
- Responsible for CMS submission compliance

### Secondary: Clinical Documentation Improvement (CDI) Specialist
- Reviews flagged cases for documentation gaps
- Sends queries to physicians requesting clarification
- Coordinates between coding and clinical teams

### Tertiary: Compliance / Audit Manager
- Reviews submission history and RAF score accuracy
- Needs audit trail of coder decisions and supporting documentation

---

## 5. Features & Requirements

### 5.1 Document Upload
| ID | Requirement | Priority |
|----|-------------|----------|
| F-01 | Accept image uploads: JPG, PNG, TIFF, WEBP, BMP | P0 |
| F-02 | Accept PDF uploads (single and multi-page) | P0 |
| F-03 | Render multi-page PDFs as tabbed page previews | P1 |
| F-04 | File size limit: 200MB per upload | P1 |
| F-05 | Display uploaded document alongside review panels | P0 |

### 5.2 AI-Powered OCR & Condition Extraction
| ID | Requirement | Priority |
|----|-------------|----------|
| F-06 | Transcribe handwritten and printed clinical notes using GPT-5 Vision | P0 |
| F-07 | Extract patient demographics (name, DOB, MRN, insurance ID, DOS, provider, practice) | P0 |
| F-08 | Identify HCC-relevant conditions from CMS-HCC V28 model — 90+ conditions across all major disease groups (see V28_MAP registry) | P0 |
| F-09 | Map detected conditions to ICD-10-CM codes with V28 HCC category numbers and RAF coefficients | P0 |
| F-10 | Display extracted text and clinical summary to coder | P1 |
| F-11 | Merge results across all pages of a multi-page PDF | P1 |
| F-12a | Two-step OCR pipeline: lean vision call for transcription followed by text-only call for V28 condition matching — keeps processing time under 90 seconds regardless of condition library size | P0 |

#### V28_MAP Condition Coverage (90+ conditions)
The condition registry covers all clinically significant HCC categories from the CMS-HCC V28 model, organized by disease group:

- **Diabetes:** Without complications, with chronic/acute complications, DKA, neuropathy, nephropathy, ophthalmic complications, diabetic foot ulcer
- **Chronic Kidney Disease:** Stages 3a, 3b, 4, 5 (pre-dialysis), ESRD/Dialysis, Renal Transplant
- **Heart Conditions:** CHF (systolic/diastolic), CAD, Acute MI, AFib, Atrial Flutter, Cardiomyopathy, Cardiac Arrest, Valvular Heart Disease
- **COPD & Lung Disease:** COPD, COPD with Acute Exacerbation, Pulmonary Fibrosis, Pulmonary Hypertension, Chronic Respiratory Failure, Asthma, Bronchiectasis
- **Cancer:** Metastatic, Lung, Breast, Colorectal, Prostate, Lymphoma, Leukemia, Multiple Myeloma, Pancreatic, Head & Neck, Cancer in Remission
- **Stroke & Neurological:** Ischemic/Hemorrhagic Stroke, Stroke Sequelae, TIA, Hemiplegia, MS, Parkinson's, Epilepsy, Neuropathy, Paraplegia
- **Vascular Disease:** PVD, Atherosclerosis (with/without gangrene), Aortic Aneurysm, DVT, Pulmonary Embolism
- **HIV/AIDS:** HIV Infection, AIDS (Advanced)
- **Major Psychiatric:** Schizophrenia, Schizoaffective Disorder, Bipolar, Major Depression, Dysthymia, Anxiety, PTSD
- **Substance Use:** Alcohol, Opioid, Cocaine, Cannabis, Polysubstance Use Disorders
- **Pressure Ulcers:** Stages 2, 3 (necrosis), 4, Unstageable
- **Amputations:** Lower limb, Upper limb, Bilateral
- **Dementia:** With/without behavioral disturbance, Alzheimer's, Vascular Dementia
- **Inflammatory Bowel Disease:** Crohn's Disease, Ulcerative Colitis
- **Rheumatoid/Inflammatory:** Rheumatoid Arthritis, Psoriatic Arthritis, SLE, Inflammatory Arthritis
- **Liver Disease:** Cirrhosis, Alcoholic Cirrhosis, Hepatitis B/C, Liver Failure/Hepatic Encephalopathy
- **Opportunistic Infections:** PCP, Cryptococcal Meningitis, CMV, Systemic Candidiasis, Toxoplasmosis
- **Other:** Obesity, Morbid Obesity, Malnutrition, Sepsis, Diabetic Foot Ulcer, Chronic Pancreatitis, Osteoporosis with Fracture

### 5.3 HCC Coding Worklist
| ID | Requirement | Priority |
|----|-------------|----------|
| F-12 | Display all detected conditions with HCC code, ICD-10, and coefficient | P0 |
| F-13 | Allow coder to Confirm or Reject each condition | P0 |
| F-14 | Allow manual addition of conditions not detected by AI | P1 |
| F-15 | Show real-time RAF score updated as conditions are confirmed | P0 |
| F-16 | Show pending condition warning before finalization | P1 |
| F-17 | Apply Diabetes + CHF interaction bonus automatically | P1 |

### 5.4 Patient Details Confirmation
| ID | Requirement | Priority |
|----|-------------|----------|
| F-18 | Pre-fill patient details from OCR extraction | P0 |
| F-19 | Allow coder to edit all patient detail fields | P0 |
| F-20 | Require coder to explicitly confirm patient details before finalizing | P1 |
| F-21 | Show confirmed details as read-only card with edit option | P2 |

### 5.5 Case Finalization
| ID | Requirement | Priority |
|----|-------------|----------|
| F-22 | "Confirm RAF Score" action locks the case and generates CMS submission document | P0 |
| F-23 | "Further Docs Needed" action opens provider clarification request workflow | P0 |
| F-24 | Finalized status persists in session with timestamp | P1 |

### 5.6 CMS Submission
| ID | Requirement | Priority |
|----|-------------|----------|
| F-25 | Generate structured RAPS/EDS submission document | P0 |
| F-26 | Include: Submission ID, patient info, all confirmed ICD-10 codes, RAF breakdown, attestation | P0 |
| F-27 | Allow download of submission file (.txt) | P0 |
| F-28 | Display submission document preview in-app | P1 |

### 5.7 Provider Clarification Workflow
| ID | Requirement | Priority |
|----|-------------|----------|
| F-29 | Condition-specific clarification message templates | P0 |
| F-30 | Coder selects condition and message auto-populates | P0 |
| F-31 | Message is editable before sending | P1 |
| F-32 | "Send to Provider Portal" action simulates portal submission | P1 |
| F-33 | Allow multiple clarification requests per case | P2 |

---

## 6. Out of Scope (v1.0)

- Real-time integration with live CMS RAPS/EDS API endpoints
- EHR system integration (Epic, Cerner, etc.)
- Multi-user / multi-tenant access control
- Audit log database persistence
- Provider portal real integration (currently simulated)
- Batch chart processing
- Mobile application

---

## 7. Assumptions & Dependencies

- Users have access to a modern web browser (Chrome, Edge, Safari)
- Clinical notes are legible enough for AI vision models to read
- OpenAI GPT-5 (or equivalent) is available via Replit AI Integrations
- Humana provides valid CMS Plan Contract IDs for production submission
- Provider portal API specs will be provided in a future phase

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | OCR response time < 15 seconds per page |
| Availability | 99.5% uptime during business hours |
| Security | No PHI stored on server; session-only data retention |
| Compliance | CMS 45 CFR § 153.610 attestation included in submission |
| Accessibility | WCAG 2.1 AA compliance for web UI |

---

## 9. Timeline

| Milestone | Target Date |
|-----------|-------------|
| Prototype complete | March 30, 2026 |
| Internal UAT | April 14, 2026 |
| Pilot (10 coders) | May 1, 2026 |
| Production rollout | June 1, 2026 |
