# hcc-prototype
HCC prototype 
streamlit
pandas

# AI-Assisted Clinical Coder for CMS-HCC V28

An AI-assisted prototype for Medicare Advantage risk adjustment coding that helps clinical coders review notes, identify HCC-relevant conditions, calculate RAF scores, generate a CMS-style submission document, and follow-up with the provider for further documentation, all in one workflow.

This prototype was built to explore how AI can improve the member risk adjudication and coding process by reducing manual chart review, improving coding consistency, and supporting faster downstream submission workflows. The current implementation uses Streamlit, GPT-5 via Replit AI Integrations, PyMuPDF, and pandas. 

## Problem

Today, HCC coding and risk adjustment workflows are often fragmented and manual. Coders must read scanned or handwritten notes clinical notes, identify eligible conditions, map them to ICD-10 and HCC categories, calculate RAF impact, and prepare data for submission. In practice, this can create delays, missed conditions, and inconsistent coding decisions. The PRD for this prototype targets reducing coding time per chart to under 3 minutes, improving HCC capture above 95%, and enabling same-day submission.

## What this prototype does

This prototype supports an end-to-end coding workflow:

- Upload a clinical note as an image or PDF
- Convert PDFs into page images for review
- Use AI-powered OCR to transcribe handwritten or printed notes
- Extract patient demographics and HCC-relevant conditions
- Map detected conditions to a constrained CMS-HCC V28 registry
- Let the coder confirm or reject suggested conditions
- Calculate RAF score impact in real time
- Generate a CMS-style RAPS/EDS submission document
- Trigger a clarification workflow when documentation is insufficient

The current app supports a constrained set of ten conditions in `V28_MAP`, including Diabetes, CKD Stage 3a, CHF, AFib, COPD, Hypertension, Obesity, PVD, CAD, and Major Depression. 

## Why the AI design is intentional

This is not designed as a black-box coding model.

The prototype uses AI for OCR and information extraction, while keeping coding logic constrained in the application layer. The model is instructed to return only conditions from the known `V28_MAP`, and the app computes RAF and generates the submission document deterministically. This reduces hallucination risk and keeps the workflow reviewable by a human coder. 

In other words:

- **AI handles unstructured input**: reading notes and extracting likely conditions
- **Application logic handles controlled decision support**: HCC mapping, RAF math, document generation
- **Human coder stays in the loop**: confirming or rejecting conditions before finalization

## Product goals

This prototype was framed around the following goals:

- Reduce coding time per chart from about 12 minutes to under 3 minutes
- Improve HCC capture rate to above 95%
- Reduce coding error rate
- Accelerate chart-to-submission turnaround to same day
- Improve provider clarification response rates

These goals and targets are documented in the PRD and reflected in the evaluation framework. 

## Evaluation approach

A core part of this project is not just building the workflow, but defining how it should be evaluated before production use.

The evaluation matrix breaks the AI component into three tasks:

1. OCR
2. HCC condition extraction
3. Patient demographics extraction

It measures these with task-specific metrics such as:

- Word Error Rate and Character Error Rate for OCR
- Precision, Recall, F1, and hallucination rate for condition extraction
- Field accuracy and completeness for patient details extraction
- End-to-end coder productivity metrics such as time per chart, throughput, and override rate

For example, the target condition extraction performance is above 92% precision, above 90% recall, and 0% hallucinated conditions outside the supported registry.

## Demo

- Demo video: https://meghna1298-cyber.github.io/hcc-prototype/
please view on laptop, not mobile friendly yet

- Live app: https://hcc-prototype-1--meghna1298.replit.app/ 
Instructions: Please use this prescription to upload to the OCR for demo purposes. [HCC_Prescription_DrChen.pdf](https://github.com/user-attachments/files/26384705/HCC_Prescription_DrChen.pdf)
Please view on laptop, not mobile friendly yet

## Repo structure

```text
.
├── app.py
├── requirements.txt
├── docs/
│   ├── PRD.md
│   ├── TECHNICAL_SPEC.md
│   └── AI_EVAL_MATRIX.md
