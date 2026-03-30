# AI Evaluation Matrix
## AI-Assisted Clinical Coder — CMS-HCC Version 28
**Version:** 1.0  
**Date:** March 30, 2026  
**Purpose:** Evaluate AI model performance across clinical coding tasks  
**Status:** Draft

---

## 1. Evaluation Overview

The AI component performs three distinct tasks in this system:
1. **OCR** — Transcribing handwritten or printed clinical notes
2. **Condition Extraction** — Identifying HCC-relevant diagnoses from note text
3. **Patient Demography Extraction** — Pulling structured patient fields from unstructured notes

Each task is evaluated independently across the dimensions below.

---

## 2. Evaluation Dimensions

| Dimension | Definition |
|-----------|------------|
| **Accuracy** | % of correct outputs vs. gold standard |
| **Precision** | Of conditions flagged, % that are truly present |
| **Recall** | Of conditions present, % that were captured |
| **F1 Score** | Harmonic mean of precision and recall |
| **Latency** | Wall-clock time from API call to response |
| **Hallucination Rate** | % of outputs containing fabricated conditions or data |
| **Field Completeness** | % of patient fields successfully extracted |
| **Coder Override Rate** | % of AI suggestions rejected or edited by coders |

---

## 3. Task 1: OCR — Handwriting Transcription

### Evaluation Method
Compare AI-transcribed text to human-transcribed gold standard. Measure Character Error Rate (CER) and Word Error Rate (WER).

| Metric | Definition | Target | Threshold (Fail) |
|--------|-----------|--------|-----------------|
| Word Error Rate (WER) | % of words incorrect | < 5% | > 15% |
| Character Error Rate (CER) | % of characters incorrect | < 3% | > 10% |
| Clinical Term Accuracy | % of clinical terms correct | > 98% | < 90% |
| Latency (single page) | API response time | < 10s | > 30s |
| Latency (multi-page PDF, 5pp) | Total processing time | < 45s | > 120s |

### Test Cases

| Test ID | Input Type | Difficulty | Expected Outcome |
|---------|-----------|------------|-----------------|
| OCR-01 | Typed/printed note | Easy | WER < 1% |
| OCR-02 | Neat handwriting | Medium | WER < 5% |
| OCR-03 | Physician scrawl | Hard | WER < 15% |
| OCR-04 | Mixed handwritten + printed | Medium | WER < 8% |
| OCR-05 | Low-resolution scan (150 DPI) | Hard | WER < 20% |
| OCR-06 | Multi-page PDF (5 pages) | Medium | All pages transcribed |
| OCR-07 | Non-English characters (Spanish patient name) | Medium | Characters preserved |

---

## 4. Task 2: HCC Condition Extraction

### Evaluation Method
Given a clinical note with known ground-truth conditions, evaluate how many are correctly identified. Evaluate against a labeled dataset of 500 de-identified notes with expert-coded HCCs.

| Metric | Definition | Target | Threshold (Fail) |
|--------|-----------|--------|-----------------|
| Precision | True positives / (TP + FP) | > 92% | < 80% |
| Recall | True positives / (TP + FN) | > 90% | < 75% |
| F1 Score | 2×(P×R)/(P+R) | > 91% | < 77% |
| Hallucination Rate | Conditions returned not in V28_MAP | 0% | > 0% |
| Out-of-scope conditions | Conditions not supported by note text | < 3% | > 10% |
| Missed HCC Rate | % of eligible HCCs not detected | < 10% | > 25% |

### Condition-Level Performance Matrix

| Condition | HCC | Expected Recall | Risk of Miss | Risk of Hallucination |
|-----------|-----|----------------|-------------|----------------------|
| Diabetes (Any Type) | 37 | High | Low (common keywords) | Low |
| CKD Stage 3a | 329 | Medium | Medium (lab-dependent) | Low |
| Congestive Heart Failure | 226 | High | Low (distinct presentation) | Low |
| Atrial Fibrillation | 238 | High | Low (distinct terminology) | Low |
| COPD | 280 | High | Low (common keywords) | Low |
| Hypertension | 136 | High | Low (very common) | Medium (mild symptoms) |
| Obesity | 48 | Medium | Medium (requires BMI) | Medium |
| Peripheral Vascular Disease | 108 | Medium | Medium (vague symptoms) | Medium |
| Coronary Artery Disease | 86 | High | Low (distinct history) | Low |
| Major Depression | 59 | Medium | High (underreported) | Medium |

### Test Cases

| Test ID | Scenario | Conditions Present | Expected |
|---------|----------|-------------------|---------|
| CE-01 | Explicit multi-condition note | Diabetes, CHF, HTN | All 3 detected |
| CE-02 | Implied condition (Metformin mentioned, no DM dx) | Diabetes (implied) | Detected with low confidence |
| CE-03 | Single condition, detailed note | CKD Stage 3a | Detected, correct ICD |
| CE-04 | No HCC conditions present | None | Empty list returned |
| CE-05 | Condition outside V28_MAP (e.g., Asthma) | Asthma | Not returned |
| CE-06 | Conflicting signals (beta-blocker with no AFib dx) | Ambiguous | Not returned (no false positive) |
| CE-07 | Handwritten with abbreviations (DM2, CHF, CKD-3) | 3 conditions | All 3 detected |
| CE-08 | Minimal note ("follow up, stable") | None | Empty list returned |

---

## 5. Task 3: Patient Demographics Extraction

### Evaluation Method
Compare AI-extracted fields to structured source data. Measure field-level extraction accuracy.

| Field | Extraction Difficulty | Target Accuracy | Threshold (Fail) |
|-------|-----------------------|----------------|-----------------|
| Patient Name | Low | > 98% | < 90% |
| Date of Birth | Low | > 97% | < 90% |
| MRN | Medium | > 95% | < 85% |
| Insurance ID | Medium | > 93% | < 80% |
| Date of Service | Low | > 97% | < 90% |
| Provider Name | Medium | > 95% | < 85% |
| Practice / Facility | High | > 88% | < 75% |
| Field Completeness (all 7 fields) | — | > 85% of fields extracted | < 60% |

### Test Cases

| Test ID | Scenario | Expected Behavior |
|---------|----------|-----------------|
| DE-01 | Structured printed letterhead | All fields extracted |
| DE-02 | Handwritten note with partial info | Partial extraction, no hallucination |
| DE-03 | No patient info on note | All fields return empty string |
| DE-04 | Date in multiple formats (01/15/26, Jan 15 2026) | Extracted, format preserved |
| DE-05 | Multiple provider names on document | Primary provider extracted |
| DE-06 | Non-standard MRN format (alphanumeric) | Extracted as-is |

---

## 6. End-to-End Workflow Evaluation

### Coder Productivity Metrics

| Metric | Baseline (Manual) | With AI Tool | Target Improvement |
|--------|-------------------|-------------|-------------------|
| Time per chart | ~12 minutes | < 3 minutes | 75% reduction |
| Charts per coder per day | ~40 | > 120 | 3x throughput |
| HCC capture rate | ~82% | > 95% | +13 points |
| Coder error rate | ~8% | < 2% | 75% reduction |
| Days to submission | 3–5 days | Same day | Near real-time |

### Coder Override Analysis

Track cases where coders override AI suggestions. High override rates indicate model drift or prompt issues.

| Override Type | Acceptable Rate | Action Trigger |
|---------------|----------------|---------------|
| Condition confirmed by coder (AI was right) | — | — |
| Condition rejected by coder (AI false positive) | < 5% | > 10% → retune prompt |
| Condition added manually (AI missed) | < 8% | > 15% → expand condition set |
| Patient field edited by coder | < 10% | > 20% → retune extraction |

---

## 7. Model Risk & Bias Assessment

| Risk | Description | Mitigation |
|------|-------------|-----------|
| **Over-coding** | AI flags conditions not in the note | Human-in-the-loop confirm/reject required for all codes |
| **Under-coding** | AI misses conditions, reducing RAF score | Recall metric monitored; manual add always available |
| **Handwriting bias** | Lower accuracy for certain handwriting styles or languages | Test across diverse note samples; consider preprocessing |
| **Recency drift** | Model behavior changes with OpenAI version updates | Pin model version; run regression suite on updates |
| **PHI leakage** | Clinical note data transmitted to AI provider | Ensure BAA with provider; scrub PHI in pre-production |
| **ICD-10 hallucination** | Model returns wrong ICD-10 code | ICD-10 codes are hardcoded in V28_MAP, not generated by AI |

---

## 8. Evaluation Cadence

| Review Type | Frequency | Owner |
|-------------|-----------|-------|
| Shadow mode testing (AI vs. expert coder) | Weekly during pilot | QA + Coding Lead |
| Precision / Recall dashboard | Monthly | ML Engineer |
| Coder override rate review | Bi-weekly | Product Manager |
| Model version regression suite | On every OpenAI model update | Engineering |
| Full audit (sample of 100 charts) | Quarterly | Compliance |

---

## 9. Evaluation Dataset Requirements

For production validation, a labeled dataset is required:

- **Size:** Minimum 500 de-identified clinical notes
- **Label types:** Ground truth HCC codes (expert-coded), patient fields, extracted text
- **Diversity:** Mix of handwritten, printed, PDF, single-page, multi-page
- **Conditions:** At least 50 notes per HCC condition
- **Negative cases:** At least 100 notes with no HCC conditions present
- **De-identification:** All PHI must be removed per HIPAA Safe Harbor standard before evaluation use
