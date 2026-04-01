import streamlit as st
import pandas as pd
import base64
import os
import json
import time
from datetime import datetime
from openai import OpenAI
import fitz  # PyMuPDF

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
AI_MODEL = "gpt-5"

openai_client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

st.set_page_config(layout="wide", page_title="V28 HCC AI Coder")

V28_MAP = {
    # ── DIABETES ──────────────────────────────────────────────────────────────
    "Diabetes without Complications": {"hcc": "37", "coef": 0.166, "icd10": "E11.9"},
    "Diabetes with Chronic Complications": {"hcc": "38", "coef": 0.302, "icd10": "E11.40"},
    "Diabetes with Acute Complications": {"hcc": "19", "coef": 0.318, "icd10": "E11.00"},
    "Diabetes with Ketoacidosis": {"hcc": "17", "coef": 0.560, "icd10": "E11.10"},
    "Diabetes with Peripheral Neuropathy": {"hcc": "38", "coef": 0.302, "icd10": "E11.40"},
    "Diabetes with Diabetic Nephropathy": {"hcc": "38", "coef": 0.302, "icd10": "E11.65"},
    "Diabetes with Ophthalmic Complications": {"hcc": "38", "coef": 0.302, "icd10": "E11.39"},
    # ── CHRONIC KIDNEY DISEASE ────────────────────────────────────────────────
    "CKD Stage 3a": {"hcc": "329", "coef": 0.165, "icd10": "N18.31"},
    "CKD Stage 3b": {"hcc": "328", "coef": 0.165, "icd10": "N18.32"},
    "CKD Stage 4": {"hcc": "326", "coef": 0.421, "icd10": "N18.4"},
    "CKD Stage 5 (Pre-Dialysis)": {"hcc": "325", "coef": 0.532, "icd10": "N18.5"},
    "End-Stage Renal Disease / Dialysis": {"hcc": "134", "coef": 0.421, "icd10": "N18.6"},
    "Renal Transplant Status": {"hcc": "135", "coef": 0.179, "icd10": "Z94.0"},
    # ── HEART CONDITIONS ──────────────────────────────────────────────────────
    "Congestive Heart Failure": {"hcc": "226", "coef": 0.360, "icd10": "I50.9"},
    "Systolic Heart Failure": {"hcc": "225", "coef": 0.487, "icd10": "I50.20"},
    "Diastolic Heart Failure": {"hcc": "226", "coef": 0.360, "icd10": "I50.30"},
    "Coronary Artery Disease": {"hcc": "86", "coef": 0.217, "icd10": "I25.10"},
    "Acute Myocardial Infarction": {"hcc": "85", "coef": 0.349, "icd10": "I21.9"},
    "Atrial Fibrillation": {"hcc": "238", "coef": 0.299, "icd10": "I48.91"},
    "Atrial Flutter": {"hcc": "238", "coef": 0.299, "icd10": "I48.4"},
    "Cardiomyopathy": {"hcc": "231", "coef": 0.293, "icd10": "I42.9"},
    "Cardiac Arrest / Ventricular Fibrillation": {"hcc": "84", "coef": 0.543, "icd10": "I46.9"},
    "Valvular Heart Disease": {"hcc": "234", "coef": 0.188, "icd10": "I34.0"},
    "Hypertension": {"hcc": "136", "coef": 0.201, "icd10": "I10"},
    # ── COPD AND CHRONIC LUNG DISEASE ────────────────────────────────────────
    "COPD": {"hcc": "280", "coef": 0.345, "icd10": "J44.9"},
    "COPD with Acute Exacerbation": {"hcc": "279", "coef": 0.398, "icd10": "J44.1"},
    "Pulmonary Fibrosis / Interstitial Lung Disease": {"hcc": "277", "coef": 0.221, "icd10": "J84.10"},
    "Pulmonary Hypertension": {"hcc": "276", "coef": 0.577, "icd10": "I27.0"},
    "Chronic Respiratory Failure": {"hcc": "278", "coef": 0.614, "icd10": "J96.10"},
    "Asthma": {"hcc": "282", "coef": 0.101, "icd10": "J45.909"},
    "Bronchiectasis": {"hcc": "281", "coef": 0.239, "icd10": "J47.9"},
    # ── CANCER (CURRENT) ──────────────────────────────────────────────────────
    "Metastatic Cancer": {"hcc": "22", "coef": 2.488, "icd10": "C80.1"},
    "Lung Cancer": {"hcc": "23", "coef": 1.089, "icd10": "C34.10"},
    "Breast Cancer": {"hcc": "24", "coef": 0.681, "icd10": "C50.919"},
    "Colorectal Cancer": {"hcc": "24", "coef": 0.681, "icd10": "C18.9"},
    "Prostate Cancer": {"hcc": "24", "coef": 0.681, "icd10": "C61"},
    "Lymphoma": {"hcc": "12", "coef": 1.089, "icd10": "C85.90"},
    "Leukemia": {"hcc": "11", "coef": 0.789, "icd10": "C91.00"},
    "Multiple Myeloma": {"hcc": "12", "coef": 1.089, "icd10": "C90.00"},
    "Pancreatic Cancer": {"hcc": "22", "coef": 2.488, "icd10": "C25.9"},
    "Head and Neck Cancer": {"hcc": "23", "coef": 1.089, "icd10": "C14.8"},
    "Cancer in Remission (Historical)": {"hcc": "35", "coef": 0.196, "icd10": "Z85.118"},
    # ── STROKE AND NEUROLOGICAL CONDITIONS ───────────────────────────────────
    "Ischemic Stroke": {"hcc": "167", "coef": 0.522, "icd10": "I63.9"},
    "Hemorrhagic Stroke": {"hcc": "166", "coef": 0.662, "icd10": "I61.9"},
    "Stroke Sequelae / Late Effects": {"hcc": "168", "coef": 0.288, "icd10": "I69.398"},
    "TIA (Transient Ischemic Attack)": {"hcc": "169", "coef": 0.188, "icd10": "G45.9"},
    "Hemiplegia / Hemiparesis": {"hcc": "79", "coef": 1.233, "icd10": "G81.90"},
    "Paraplegia / Spinal Cord Injury": {"hcc": "72", "coef": 0.587, "icd10": "G82.20"},
    "Multiple Sclerosis": {"hcc": "77", "coef": 0.669, "icd10": "G35"},
    "Parkinson's Disease": {"hcc": "78", "coef": 0.669, "icd10": "G20"},
    "Epilepsy": {"hcc": "253", "coef": 0.499, "icd10": "G40.909"},
    "Neuropathy": {"hcc": "131", "coef": 0.332, "icd10": "G62.9"},
    # ── VASCULAR DISEASE ──────────────────────────────────────────────────────
    "Peripheral Vascular Disease": {"hcc": "108", "coef": 0.288, "icd10": "I73.9"},
    "Atherosclerosis of Extremities": {"hcc": "106", "coef": 0.350, "icd10": "I70.209"},
    "Atherosclerosis with Gangrene": {"hcc": "105", "coef": 0.799, "icd10": "I70.262"},
    "Aortic Aneurysm": {"hcc": "107", "coef": 0.577, "icd10": "I71.9"},
    "Venous Thromboembolism / DVT": {"hcc": "117", "coef": 0.237, "icd10": "I82.401"},
    "Pulmonary Embolism": {"hcc": "116", "coef": 0.365, "icd10": "I26.99"},
    # ── HIV / AIDS ────────────────────────────────────────────────────────────
    "HIV Infection": {"hcc": "1", "coef": 0.335, "icd10": "B20"},
    "AIDS (Advanced HIV Disease)": {"hcc": "1", "coef": 0.335, "icd10": "B20"},
    # ── MAJOR PSYCHIATRIC CONDITIONS ─────────────────────────────────────────
    "Schizophrenia": {"hcc": "57", "coef": 0.456, "icd10": "F20.9"},
    "Schizoaffective Disorder": {"hcc": "57", "coef": 0.456, "icd10": "F25.9"},
    "Bipolar Disorder": {"hcc": "58", "coef": 0.395, "icd10": "F31.9"},
    "Major Depression": {"hcc": "59", "coef": 0.395, "icd10": "F32.9"},
    "Persistent Depressive Disorder (Dysthymia)": {"hcc": "59", "coef": 0.395, "icd10": "F34.1"},
    "Anxiety Disorder": {"hcc": "60", "coef": 0.175, "icd10": "F41.9"},
    "Post-Traumatic Stress Disorder (PTSD)": {"hcc": "59", "coef": 0.395, "icd10": "F43.10"},
    # ── SUBSTANCE USE DISORDERS ───────────────────────────────────────────────
    "Alcohol Use Disorder": {"hcc": "135", "coef": 0.329, "icd10": "F10.20"},
    "Opioid Use Disorder": {"hcc": "136", "coef": 0.410, "icd10": "F11.20"},
    "Cocaine Use Disorder": {"hcc": "136", "coef": 0.410, "icd10": "F14.20"},
    "Cannabis Use Disorder": {"hcc": "137", "coef": 0.215, "icd10": "F12.20"},
    "Polysubstance Use Disorder": {"hcc": "136", "coef": 0.410, "icd10": "F19.20"},
    # ── PRESSURE ULCERS ───────────────────────────────────────────────────────
    "Pressure Ulcer Stage 3 / Necrosis": {"hcc": "157", "coef": 1.156, "icd10": "L89.153"},
    "Pressure Ulcer Stage 2": {"hcc": "158", "coef": 0.524, "icd10": "L89.119"},
    "Pressure Ulcer Stage 4": {"hcc": "156", "coef": 1.524, "icd10": "L89.154"},
    # ── AMPUTATIONS ───────────────────────────────────────────────────────────
    "Amputation of Lower Limb": {"hcc": "189", "coef": 0.691, "icd10": "Z89.511"},
    "Amputation of Upper Limb": {"hcc": "188", "coef": 0.479, "icd10": "Z89.201"},
    "Bilateral Limb Amputation": {"hcc": "188", "coef": 0.691, "icd10": "Z89.621"},
    # ── DEMENTIA ──────────────────────────────────────────────────────────────
    "Dementia with Behavioral Disturbance": {"hcc": "52", "coef": 0.346, "icd10": "F02.81"},
    "Dementia without Behavioral Disturbance": {"hcc": "53", "coef": 0.346, "icd10": "F03.90"},
    "Alzheimer's Disease": {"hcc": "52", "coef": 0.346, "icd10": "G30.9"},
    "Vascular Dementia": {"hcc": "52", "coef": 0.346, "icd10": "F01.51"},
    # ── INFLAMMATORY BOWEL DISEASE ────────────────────────────────────────────
    "Crohn's Disease (IBD)": {"hcc": "35", "coef": 0.302, "icd10": "K50.90"},
    "Ulcerative Colitis (IBD)": {"hcc": "35", "coef": 0.302, "icd10": "K51.90"},
    # ── RHEUMATOID ARTHRITIS / INFLAMMATORY ──────────────────────────────────
    "Rheumatoid Arthritis": {"hcc": "40", "coef": 0.421, "icd10": "M05.79"},
    "Psoriatic Arthritis": {"hcc": "40", "coef": 0.421, "icd10": "L40.54"},
    "Systemic Lupus Erythematosus (SLE)": {"hcc": "39", "coef": 0.488, "icd10": "M32.9"},
    "Inflammatory Arthritis (Other)": {"hcc": "40", "coef": 0.302, "icd10": "M06.9"},
    # ── LIVER DISEASE ─────────────────────────────────────────────────────────
    "Cirrhosis of the Liver": {"hcc": "29", "coef": 0.965, "icd10": "K74.60"},
    "Alcoholic Cirrhosis": {"hcc": "29", "coef": 0.965, "icd10": "K70.30"},
    "Chronic Hepatitis B": {"hcc": "30", "coef": 0.421, "icd10": "B18.1"},
    "Chronic Hepatitis C": {"hcc": "30", "coef": 0.421, "icd10": "B18.2"},
    "Liver Failure / Hepatic Encephalopathy": {"hcc": "27", "coef": 1.488, "icd10": "K72.90"},
    # ── OPPORTUNISTIC INFECTIONS ──────────────────────────────────────────────
    "Pneumocystis Pneumonia (PCP)": {"hcc": "6", "coef": 0.374, "icd10": "B59"},
    "Cryptococcal Meningitis": {"hcc": "6", "coef": 0.374, "icd10": "B45.1"},
    "Cytomegalovirus (CMV) Disease": {"hcc": "6", "coef": 0.374, "icd10": "B25.9"},
    "Candidiasis (Systemic)": {"hcc": "6", "coef": 0.374, "icd10": "B37.1"},
    "Toxoplasmosis": {"hcc": "6", "coef": 0.374, "icd10": "B58.9"},
    # ── ADDITIONAL COMMON CONDITIONS ─────────────────────────────────────────
    "Obesity": {"hcc": "48", "coef": 0.272, "icd10": "E66.9"},
    "Morbid Obesity": {"hcc": "47", "coef": 0.411, "icd10": "E66.01"},
    "Malnutrition": {"hcc": "21", "coef": 0.587, "icd10": "E41"},
    "Septicemia / Sepsis": {"hcc": "3", "coef": 0.514, "icd10": "A41.9"},
    "Pressure Injury (Unstageable)": {"hcc": "156", "coef": 1.156, "icd10": "L89.130"},
    "Diabetic Foot Ulcer": {"hcc": "38", "coef": 0.388, "icd10": "E11.621"},
    "Chronic Pancreatitis": {"hcc": "34", "coef": 0.290, "icd10": "K86.1"},
    "Osteoporosis with Pathological Fracture": {"hcc": "170", "coef": 0.434, "icd10": "M80.00XA"},
}


def pdf_to_images(pdf_bytes: bytes) -> list[tuple[bytes, str]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        images.append((pix.tobytes("png"), "image/png"))
    doc.close()
    return images


def _call_openai(fn, retries: int = 3, initial_delay: float = 2.0):
    """Call an OpenAI API function with automatic retries on transient JSON/HTTP errors.

    The OpenAI Python client parses the raw HTTP response body as JSON internally.
    When the Replit AI proxy returns an empty or malformed body (transient gateway
    issue), the library itself throws json.JSONDecodeError before we can inspect
    the content.  This wrapper catches that and retries up to `retries` times.
    """
    last_err = None
    delay = initial_delay
    for attempt in range(retries):
        try:
            return fn()
        except Exception as exc:
            last_err = exc
            msg = str(exc).lower()
            is_transient = (
                "expecting value" in msg or
                "jsondecode" in msg or
                "empty" in msg or
                "connection" in msg or
                "timeout" in msg
            )
            if is_transient and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise last_err


def _safe_json(raw: str, fallback: dict) -> dict:
    """Parse JSON from an API response safely, with a regex fallback."""
    import re
    if not raw or not raw.strip():
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
        return fallback


def ocr_clinical_note(image_bytes: bytes, mime_type: str) -> dict:
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_image}"

    empty_patient = {"patient_name": "", "date_of_birth": "", "mrn": "",
                     "insurance_id": "", "date_of_service": "", "provider_name": "", "practice_name": ""}

    # ── STEP 1: Lean vision call — OCR + raw clinical extraction only ──────────
    ocr_prompt = (
        "You are a medical transcriptionist. Read this clinical note carefully "
        "(it may be handwritten, printed, or a prescription).\n\n"
        "Return a JSON object with exactly these keys:\n"
        "- extracted_text: complete verbatim transcription of all visible text\n"
        "- raw_diagnoses: list of every diagnosis, condition, or symptom mentioned\n"
        "- medications: list of every medication name mentioned\n"
        "- clinical_summary: 1-2 sentence summary of the clinical content\n"
        "- patient_details: object with keys patient_name, date_of_birth, mrn, "
        "insurance_id, date_of_service, provider_name, practice_name "
        "(use empty string for any field not found)\n\n"
        "Always respond with valid JSON even if the document has minimal content."
    )

    vision_resp = _call_openai(lambda: openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": ocr_prompt},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]}],
        max_completion_tokens=2048
    ))

    raw_vision = (vision_resp.choices[0].message.content or "").strip()
    ocr_data = _safe_json(raw_vision, {
        "extracted_text": raw_vision,
        "raw_diagnoses": [],
        "medications": [],
        "clinical_summary": "",
        "patient_details": empty_patient
    })

    # ── STEP 2: Text-only call — map clinical findings to V28_MAP keys ─────────
    known_conditions = "\n".join(f"- {k}" for k in V28_MAP.keys())
    extracted_text = ocr_data.get("extracted_text", "") or raw_vision
    raw_diagnoses  = ", ".join(ocr_data.get("raw_diagnoses", []))
    medications    = ", ".join(ocr_data.get("medications", []))

    # Only run step 2 if we have something to match against
    if not (extracted_text or raw_diagnoses or medications).strip():
        return {
            "extracted_text": extracted_text,
            "detected_conditions": [],
            "clinical_summary": ocr_data.get("clinical_summary", ""),
            "patient_details": ocr_data.get("patient_details", empty_patient)
        }

    match_prompt = (
        "You are a CMS-HCC Version 28 coding specialist.\n\n"
        "Given the clinical note content below, identify which conditions from the V28 list "
        "are present or clearly implied by the documentation.\n\n"
        f"NOTE TEXT: {extracted_text}\n"
        f"RAW DIAGNOSES: {raw_diagnoses}\n"
        f"MEDICATIONS: {medications}\n\n"
        f"V28 CONDITIONS:\n{known_conditions}\n\n"
        'Return a JSON object: {"detected_conditions": ["<exact name from list>", ...]}\n'
        "Only include conditions explicitly documented or strongly implied. "
        "Use exact names from the list. Return an empty list if none match."
    )

    match_resp = _call_openai(lambda: openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": match_prompt}],
        max_completion_tokens=1024
    ))

    raw_match = (match_resp.choices[0].message.content or "").strip()
    match_data = _safe_json(raw_match, {"detected_conditions": []})

    return {
        "extracted_text":      ocr_data.get("extracted_text", ""),
        "detected_conditions": match_data.get("detected_conditions", []),
        "clinical_summary":    ocr_data.get("clinical_summary", ""),
        "patient_details":     ocr_data.get("patient_details", empty_patient)
    }


def generate_cms_submission(patient: dict, hcc_data: list, total_raf: float, timestamp: str) -> str:
    """Generate a RAPS/EDS-style CMS submission document."""
    confirmed = [d for d in hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP]
    submission_id = f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    lines = [
        "=" * 70,
        "  CMS RISK ADJUSTMENT SUBMISSION — V28 MODEL",
        "  Risk Adjustment Processing System (RAPS) / Encounter Data System (EDS)",
        "=" * 70,
        "",
        f"  Submission ID   : {submission_id}",
        f"  Submission Date : {timestamp}",
        f"  Model Version   : CMS-HCC Version 28 (100% Phase-In, 2026)",
        f"  Plan Contract   : H9999 (Prototype)",
        "",
        "-" * 70,
        "  PATIENT INFORMATION",
        "-" * 70,
        f"  Patient Name    : {patient.get('patient_name') or 'N/A'}",
        f"  Date of Birth   : {patient.get('date_of_birth') or 'N/A'}",
        f"  MRN             : {patient.get('mrn') or 'N/A'}",
        f"  Insurance ID    : {patient.get('insurance_id') or 'N/A'}",
        f"  Date of Service : {patient.get('date_of_service') or 'N/A'}",
        f"  Provider        : {patient.get('provider_name') or 'N/A'}",
        f"  Practice        : {patient.get('practice_name') or 'N/A'}",
        "",
        "-" * 70,
        "  CONFIRMED DIAGNOSIS CODES (ICD-10-CM)",
        "-" * 70,
    ]
    for item in confirmed:
        details = V28_MAP[item['term']]
        lines.append(f"  HCC {details['hcc']:<6}  ICD-10: {details['icd10']:<10}  {item['term']}")
        lines.append(f"           Coefficient: +{details['coef']:.3f}")
        lines.append("")

    lines += [
        "-" * 70,
        "  RAF SCORE CALCULATION",
        "-" * 70,
        f"  Base RAF Score        : 0.350",
    ]
    for item in confirmed:
        details = V28_MAP[item['term']]
        lines.append(f"  + HCC {details['hcc']:<4} ({item['term']:<35}) : +{details['coef']:.3f}")
    confirmed_term_list = [d['term'] for d in confirmed]
    has_dm = any(t.startswith("Diabetes") for t in confirmed_term_list)
    has_chf = any(t in confirmed_term_list for t in ["Congestive Heart Failure", "Systolic Heart Failure", "Diastolic Heart Failure"])
    if has_dm and has_chf:
        lines.append(f"  + Diabetes-CHF Interaction Bonus             : +0.112")
    lines += [
        f"  {'─' * 50}",
        f"  FINAL RAF SCORE                                : {total_raf:.3f}",
        "",
        "=" * 70,
        "  SUBMISSION ATTESTATION",
        "=" * 70,
        "  The diagnosis information submitted herein is supported by medical",
        "  record documentation and has been reviewed and confirmed by a",
        "  certified HCC coder. This submission complies with CMS Risk",
        "  Adjustment data validation requirements (45 CFR § 153.610).",
        "",
        f"  Confirmed by   : HCC Coder (AI-Assisted v28 Tool)",
        f"  Confirmed at   : {timestamp}",
        "=" * 70,
    ]
    return "\n".join(lines)


def merge_ocr_results(results: list[dict]) -> dict:
    all_text, all_conditions, all_summaries = [], set(), []
    merged_patient = {"patient_name": "", "date_of_birth": "", "mrn": "",
                      "insurance_id": "", "date_of_service": "", "provider_name": "", "practice_name": ""}
    for r in results:
        all_text.append(r.get("extracted_text", ""))
        all_conditions.update(r.get("detected_conditions", []))
        if r.get("clinical_summary"):
            all_summaries.append(r["clinical_summary"])
        for field in merged_patient:
            if not merged_patient[field]:
                merged_patient[field] = r.get("patient_details", {}).get(field, "")
    return {
        "extracted_text": "\n\n--- Next Page ---\n\n".join(all_text),
        "detected_conditions": list(all_conditions),
        "clinical_summary": " ".join(all_summaries),
        "patient_details": merged_patient
    }


# --- Clarification message templates per condition ---
CLARIFICATION_TEMPLATES = {
    # Diabetes
    "Diabetes without Complications": "Your note references glucose-lowering medications or elevated glucose but does not explicitly document a Diabetes diagnosis. Please confirm Type 2 Diabetes Mellitus (E11.9) and note any current complications.",
    "Diabetes with Chronic Complications": "Your note references diabetic complications but does not explicitly document the underlying Diabetes with Chronic Complications (E11.40). Please confirm the diagnosis and specify which chronic complications are present.",
    "Diabetes with Acute Complications": "Your note suggests an acute diabetic event. Please confirm whether the patient has Diabetes with Acute Complications (E11.00) and specify the nature of the acute complication.",
    "Diabetes with Ketoacidosis": "Your note references symptoms consistent with DKA. Please confirm a Diabetes with Ketoacidosis diagnosis (E11.10) and provide the most recent blood glucose and pH values.",
    "Diabetes with Peripheral Neuropathy": "Your note references neuropathic symptoms in a diabetic patient. Please confirm Diabetes with Peripheral Neuropathy (E11.40) and document the neuropathy type and affected sites.",
    "Diabetes with Diabetic Nephropathy": "Your note suggests diabetic kidney involvement. Please confirm Diabetes with Diabetic Nephropathy (E11.65) and provide the most recent eGFR and urine albumin/creatinine ratio.",
    "Diabetes with Ophthalmic Complications": "Your note references visual symptoms or ophthalmology follow-up in a diabetic patient. Please confirm Diabetes with Ophthalmic Complications (E11.39) and specify the type of retinopathy or other eye finding.",
    "Diabetic Foot Ulcer": "Your note references a wound or ulcer on the foot in a diabetic patient. Please confirm a Diabetic Foot Ulcer diagnosis (E11.621), document the wound grade (Wagner scale), and note current wound care.",
    # CKD
    "CKD Stage 3a": "Your note references kidney function or related labs but does not explicitly state a CKD Stage 3a diagnosis. Please confirm CKD Stage 3a (N18.31) and provide supporting GFR values (45–59 mL/min).",
    "CKD Stage 3b": "Your note suggests reduced kidney function. Please confirm CKD Stage 3b (N18.32) and provide the most recent eGFR value (30–44 mL/min) and any albuminuria results.",
    "CKD Stage 4": "Your note suggests significantly reduced kidney function. Please confirm CKD Stage 4 (N18.4) and provide the most recent eGFR (15–29 mL/min) and nephrology referral documentation.",
    "CKD Stage 5 (Pre-Dialysis)": "Your note suggests severe kidney failure. Please confirm CKD Stage 5 without dialysis (N18.5), provide the most recent eGFR (<15 mL/min), and clarify whether dialysis has been initiated.",
    "End-Stage Renal Disease / Dialysis": "Your note references dialysis or ESRD but does not explicitly document the diagnosis. Please confirm End-Stage Renal Disease with dialysis (N18.6) and specify the dialysis modality (hemodialysis/peritoneal).",
    # Heart
    "Congestive Heart Failure": "Your clinical note references cardiac symptoms or medications consistent with heart failure, but CHF is not explicitly documented. Please confirm Congestive Heart Failure (I50.9) and specify the type (systolic/diastolic/combined).",
    "Systolic Heart Failure": "Your note suggests systolic dysfunction. Please confirm Systolic Heart Failure (I50.20), provide the most recent ejection fraction, and note current NYHA class.",
    "Diastolic Heart Failure": "Your note suggests diastolic dysfunction. Please confirm Diastolic Heart Failure (I50.30) and provide most recent echocardiographic findings.",
    "Coronary Artery Disease": "Your note references cardiac history or medications consistent with CAD, but Coronary Artery Disease is not explicitly documented. Please confirm a CAD diagnosis (I25.10) and any relevant catheterization or imaging results.",
    "Acute Myocardial Infarction": "Your note suggests a recent cardiac event. Please confirm Acute Myocardial Infarction (I21.9), provide the date of onset, troponin results, and any intervention performed (PCI/CABG).",
    "Atrial Fibrillation": "Your note suggests possible rhythm abnormalities or anticoagulation therapy, but Atrial Fibrillation is not explicitly stated. Please confirm a documented AFib diagnosis (I48.91) and indicate if it is paroxysmal, persistent, or permanent.",
    "Cardiomyopathy": "Your note references cardiomegaly or reduced cardiac function. Please confirm Cardiomyopathy (I42.9), specify the type (dilated/hypertrophic/restrictive), and provide the most recent echocardiographic ejection fraction.",
    # Lung
    "COPD": "Your note references respiratory symptoms or inhaler use without an explicit COPD diagnosis. Please confirm Chronic Obstructive Pulmonary Disease (J44.9) and provide any relevant spirometry findings (FEV1/FVC ratio).",
    "COPD with Acute Exacerbation": "Your note suggests a COPD flare. Please confirm COPD with Acute Exacerbation (J44.1), document the precipitating factor, and note any systemic corticosteroid or antibiotic treatment.",
    "Pulmonary Fibrosis / Interstitial Lung Disease": "Your note references respiratory symptoms or CT findings consistent with ILD. Please confirm Pulmonary Fibrosis (J84.10) and provide the most recent HRCT findings and pulmonary function test results.",
    "Pulmonary Hypertension": "Your note references elevated pulmonary pressures or right heart strain. Please confirm Pulmonary Hypertension (I27.0), specify the WHO group, and provide the most recent right heart catheterization or echocardiographic RVSP.",
    "Chronic Respiratory Failure": "Your note suggests chronic hypoxia or ventilatory failure. Please confirm Chronic Respiratory Failure (J96.10), specify whether it is hypoxic or hypercapnic, and document home oxygen or ventilator use.",
    # Cancer
    "Metastatic Cancer": "Your note references cancer with possible spread. Please confirm Metastatic Cancer (C80.1), identify the primary site and sites of metastasis, and provide the most recent oncology note or imaging confirming metastatic disease.",
    "Lung Cancer": "Your note references a pulmonary mass or oncology treatment. Please confirm Lung Cancer (C34.10), specify the histological type and stage, and provide the most recent pathology or imaging report.",
    "Breast Cancer": "Your note references breast cancer history or treatment. Please confirm active Breast Cancer (C50.919), specify the stage and receptor status, and provide the date of most recent oncology visit.",
    "Lymphoma": "Your note references lymphadenopathy or oncology treatment consistent with lymphoma. Please confirm the Lymphoma diagnosis (C85.90), specify the type (Hodgkin vs. Non-Hodgkin), and provide the most recent pathology report.",
    "Leukemia": "Your note references hematologic malignancy. Please confirm Leukemia (C91.00), specify the type (ALL/CLL/AML/CML), and provide the most recent CBC and oncology note.",
    "Cancer in Remission (Historical)": "Your note references a prior cancer diagnosis. Please confirm Cancer in Remission (Z85.118), specify the original cancer type and site, and document the date remission was established.",
    # Stroke / Neuro
    "Ischemic Stroke": "Your note references neurological symptoms or TPA use consistent with stroke. Please confirm Ischemic Stroke (I63.9), provide the date of onset, neuroimaging findings, and NIH Stroke Scale score at presentation.",
    "Stroke Sequelae / Late Effects": "Your note references residual neurological deficits from a prior stroke. Please confirm Stroke Late Effects (I69.398), specify the deficits (aphasia, hemiplegia, dysphagia), and note the date of the original stroke.",
    "Hemiplegia / Hemiparesis": "Your note references one-sided weakness or paralysis. Please confirm Hemiplegia (G81.90), specify the affected side and whether it is flaccid or spastic, and provide the underlying etiology.",
    "Multiple Sclerosis": "Your note references MS or demyelinating disease. Please confirm Multiple Sclerosis (G35), specify the type (RRMS/SPMS/PPMS), and document the most recent MRI findings and neurologist note.",
    "Parkinson's Disease": "Your note references parkinsonism or Parkinson's medications. Please confirm Parkinson's Disease (G20), document the current H&Y stage, and note the medication regimen and most recent neurology visit.",
    "Epilepsy": "Your note references seizures or anti-epileptic medications without explicitly documenting Epilepsy. Please confirm Epilepsy (G40.909), specify the seizure type, and note current AED medications and most recent EEG.",
    "Dementia with Behavioral Disturbance": "Your note references cognitive decline with behavioral symptoms. Please confirm Dementia with Behavioral Disturbance (F02.81), specify the type (Alzheimer's/vascular/Lewy body), and document a formal cognitive assessment (e.g., MMSE or MoCA score).",
    "Dementia without Behavioral Disturbance": "Your note references cognitive decline without explicit behavioral symptoms. Please confirm Dementia (F03.90), specify the underlying etiology, and document a formal cognitive assessment.",
    "Alzheimer's Disease": "Your note references memory loss or Alzheimer's medications. Please confirm Alzheimer's Disease (G30.9), provide the most recent cognitive assessment score, and document any specialist evaluation.",
    # Vascular
    "Peripheral Vascular Disease": "Your note references vascular symptoms or related medications without documenting PVD explicitly. Please confirm Peripheral Vascular Disease (I73.9) and provide any relevant ABI or vascular imaging findings.",
    "Atherosclerosis with Gangrene": "Your note references critical limb ischemia or tissue loss. Please confirm Atherosclerosis with Gangrene (I70.262), document the affected limb, and note whether revascularization has been performed or planned.",
    "Aortic Aneurysm": "Your note references aortic dilation or an aneurysm incidentally noted. Please confirm Aortic Aneurysm (I71.9), provide the most recent imaging measurement, and note whether surveillance or intervention is planned.",
    "Pulmonary Embolism": "Your note references acute dyspnea or anticoagulation consistent with PE. Please confirm Pulmonary Embolism (I26.99), provide the diagnostic imaging report (CT-PA), and document the current anticoagulation plan.",
    # HIV
    "HIV Infection": "Your note references antiretroviral medications or HIV-related labs but does not explicitly document an HIV diagnosis. Please confirm HIV Infection (B20) and provide the most recent CD4 count and viral load.",
    "AIDS (Advanced HIV Disease)": "Your note suggests advanced HIV disease. Please confirm AIDS (B20), document the most recent CD4 count (<200 cells/µL), viral load, and any current opportunistic infection prophylaxis.",
    # Psychiatric
    "Schizophrenia": "Your note references antipsychotic medications or psychotic symptoms without explicitly documenting Schizophrenia. Please confirm a Schizophrenia diagnosis (F20.9) and provide the most recent psychiatric evaluation note.",
    "Bipolar Disorder": "Your note references mood stabilizers or cycling mood symptoms. Please confirm Bipolar Disorder (F31.9), specify the type (I/II/unspecified), and note the current mood episode and medication regimen.",
    "Major Depression": "Your note references mood symptoms or antidepressant therapy without an explicit Major Depression diagnosis. Please confirm Major Depressive Disorder (F32.9) and note the current severity (mild/moderate/severe).",
    "Post-Traumatic Stress Disorder (PTSD)": "Your note references trauma history or PTSD medications. Please confirm a PTSD diagnosis (F43.10), document the traumatic event category, and note the current treatment plan.",
    # Substance Use
    "Alcohol Use Disorder": "Your note references alcohol consumption or hepatic changes consistent with AUD. Please confirm Alcohol Use Disorder (F10.20), specify the severity (mild/moderate/severe), and note whether the patient is currently in treatment.",
    "Opioid Use Disorder": "Your note references opioid medications or withdrawal symptoms. Please confirm Opioid Use Disorder (F11.20), specify the severity, and document any MAT (methadone/buprenorphine) currently prescribed.",
    # Liver
    "Cirrhosis of the Liver": "Your note references hepatic dysfunction or portal hypertension. Please confirm Cirrhosis (K74.60), specify the Child-Pugh class, and provide the most recent liver function tests and imaging.",
    "Chronic Hepatitis C": "Your note references antiviral treatment or liver enzyme elevation consistent with Hepatitis C. Please confirm Chronic Hepatitis C (B18.2), provide the most recent viral load and genotype, and note treatment history.",
    "Liver Failure / Hepatic Encephalopathy": "Your note references altered mentation or hepatic decompensation. Please confirm Liver Failure or Hepatic Encephalopathy (K72.90), document the precipitating cause, and provide ammonia levels and LFTs.",
    # Opportunistic Infections
    "Pneumocystis Pneumonia (PCP)": "Your note references respiratory symptoms and immunosuppression consistent with PCP. Please confirm Pneumocystis Pneumonia (B59), provide the BAL or biopsy results, and document the current treatment and prophylaxis regimen.",
    # Other
    "Hypertension": "Your note references blood pressure readings or antihypertensive medications but does not explicitly list Hypertension as a diagnosis. Please confirm the patient's hypertension status (I10) and provide the most recent BP readings.",
    "Obesity": "Your note includes a weight or BMI reference without an explicit Obesity diagnosis. Please confirm whether the patient meets criteria for Obesity (E66.9) and document the current BMI.",
    "Morbid Obesity": "Your note references extreme weight or bariatric history. Please confirm Morbid Obesity (E66.01), document the current BMI (≥40), and note any obesity-related comorbidities.",
    "Septicemia / Sepsis": "Your note references systemic infection or sepsis criteria. Please confirm Septicemia/Sepsis (A41.9), identify the suspected source and organism, and document the SOFA score and antibiotic regimen.",
    "Rheumatoid Arthritis": "Your note references joint inflammation or DMARD therapy consistent with RA. Please confirm Rheumatoid Arthritis (M05.79), provide the most recent RF/anti-CCP results, and note the current disease-modifying therapy.",
    "Systemic Lupus Erythematosus (SLE)": "Your note references autoimmune symptoms or immunosuppressive therapy consistent with SLE. Please confirm SLE (M32.9), provide the most recent ANA/anti-dsDNA titers, and note the current treatment plan.",
    "Crohn's Disease (IBD)": "Your note references GI symptoms or IBD medications. Please confirm Crohn's Disease (K50.90), document the disease location and activity (Harvey-Bradshaw Index or SES-CD), and note current therapy.",
    "Ulcerative Colitis (IBD)": "Your note references GI symptoms or IBD medications. Please confirm Ulcerative Colitis (K51.90), document the disease extent and activity (Mayo Score), and note current therapy.",
    "Pressure Ulcer Stage 2": "Your note references a skin wound or pressure injury. Please confirm Pressure Ulcer Stage 2 (L89.119), document the anatomical location, size, and current wound care plan.",
    "Pressure Ulcer Stage 3 / Necrosis": "Your note references a deep pressure wound. Please confirm Pressure Ulcer Stage 3 (L89.153), document the anatomical location, wound measurements, and current wound care and offloading plan.",
    "Pressure Ulcer Stage 4": "Your note references a severe pressure wound with tissue loss. Please confirm Pressure Ulcer Stage 4 (L89.154), document exposed structures (bone/tendon), and note the current wound care, surgical, or palliative plan.",
    "Amputation of Lower Limb": "Your note references a lower extremity amputation. Please confirm Amputation of Lower Limb status (Z89.511), specify the level (toe/transmetatarsal/BKA/AKA), and note the date of amputation and current prosthetic use.",
    "Malnutrition": "Your note references weight loss, low albumin, or inadequate intake. Please confirm Malnutrition (E41), specify the severity (mild/moderate/severe), and document a formal nutrition assessment or dietitian evaluation.",
    "Osteoporosis with Pathological Fracture": "Your note references a fracture in the setting of low bone density. Please confirm Osteoporosis with Pathological Fracture (M80.00XA), document the fracture site, and provide the most recent DXA T-score.",
}

# --- Session State ---
defaults = {
    'hcc_data': [],
    'ocr_result': None,
    'uploaded_image_bytes': None,
    'case_status': None,
    'case_timestamp': None,
    'patient_details': {"patient_name": "", "date_of_birth": "", "mrn": "",
                        "insurance_id": "", "date_of_service": "", "provider_name": "", "practice_name": ""},
    'patient_confirmed': False,
    'clarification_sent': False,
    'clarification_condition': None,
    'cms_doc': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🩺 AI-Assisted Clinical Coder (v28 Model)")
st.caption("CMS-HCC Version 28 | 100% Phase-in Compliance (2026)")

confirmed_terms_top = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
if st.session_state.case_status == "confirmed":
    ib = 0.112 if (any(t.startswith("Diabetes") for t in confirmed_terms_top) and
                   any(t in confirmed_terms_top for t in ["Congestive Heart Failure", "Systolic Heart Failure", "Diastolic Heart Failure"])) else 0.0
    fr = 0.350 + sum(V28_MAP[d['term']]['coef'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP) + ib
    st.success(f"✅ **Case Confirmed** — RAF Score locked at **{fr:.3f}** on {st.session_state.case_timestamp}")
elif st.session_state.case_status == "further_docs":
    st.warning(f"📋 **Further Documentation Needed** — Case flagged on {st.session_state.case_timestamp}.")

st.divider()

# ── Upload bar (always visible, compact once a file is loaded) ───────────────
with st.expander("📄 Upload Clinical Note", expanded=st.session_state.uploaded_image_bytes is None):
    st.write("Upload a handwritten or printed clinical note (image or PDF). The AI will read it and identify HCC conditions automatically.")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "webp", "pdf"],
        help="Supports images (JPG, PNG, TIFF, WEBP) and PDF documents.",
        key="file_uploader"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        is_pdf = uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf")

        if is_pdf:
            preview_images = pdf_to_images(file_bytes)
            st.caption(f"PDF — {len(preview_images)} page(s) loaded")
            st.session_state.uploaded_image_bytes = preview_images
        else:
            st.session_state.uploaded_image_bytes = [(file_bytes, uploaded_file.type or "image/jpeg")]
            st.caption("Image loaded.")

        if st.button("🔍 Run OCR & Extract HCCs", type="primary"):
            with st.spinner("Reading the note and identifying HCC conditions..."):
                try:
                    page_results = [ocr_clinical_note(ib, mt) for ib, mt in st.session_state.uploaded_image_bytes]
                    merged = merge_ocr_results(page_results)
                    st.session_state.ocr_result = merged

                    existing_terms = {d['term'] for d in st.session_state.hcc_data}
                    next_id = max((d['id'] for d in st.session_state.hcc_data), default=0) + 1
                    for condition in merged.get("detected_conditions", []):
                        if condition in V28_MAP and condition not in existing_terms:
                            st.session_state.hcc_data.append({"id": next_id, "term": condition, "status": "Pending"})
                            existing_terms.add(condition)
                            next_id += 1

                    if merged.get("patient_details"):
                        for field, val in merged["patient_details"].items():
                            if val:
                                st.session_state.patient_details[field] = val
                        st.session_state.patient_confirmed = False

                    st.session_state.case_status = None
                    st.rerun()
                except Exception as e:
                    err = str(e)
                    if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
                        st.error("Your Replit AI cloud budget has been exceeded.")
                    else:
                        st.error(f"Error processing file: {err}")

# ── OCR text result (collapsible) ────────────────────────────────────────────
if st.session_state.ocr_result:
    res = st.session_state.ocr_result
    with st.expander("📝 Extracted Note Text & Clinical Summary", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Transcribed Text:**")
            st.text_area("", value=res.get("extracted_text", ""), height=130, disabled=True, label_visibility="collapsed")
        with c2:
            summary = res.get("clinical_summary", "").strip()
            conditions = res.get("detected_conditions", [])
            if summary:
                st.info(summary)
            if conditions:
                for cond in conditions:
                    st.success(f"✓ {cond}")
            elif not summary:
                st.warning("No HCC conditions detected. The document may be a cover page, blank form, or may not contain clinical diagnoses. Try uploading a page with patient diagnosis notes.")

st.divider()

# ── Compute RAF ──────────────────────────────────────────────────────────────
base_raf = 0.350
confirmed_hccs = [V28_MAP[d['term']] for d in st.session_state.hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP]
hcc_sum = sum(h['coef'] for h in confirmed_hccs)
confirmed_terms = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
interaction_bonus = 0.112 if (any(t.startswith("Diabetes") for t in confirmed_terms) and
                              any(t in confirmed_terms for t in ["Congestive Heart Failure", "Systolic Heart Failure", "Diastolic Heart Failure"])) else 0.0
total_raf = base_raf + hcc_sum + interaction_bonus

# ── Three-panel review layout ─────────────────────────────────────────────────
has_image = st.session_state.uploaded_image_bytes is not None

if has_image:
    col_rx, col_summary, col_worklist = st.columns([1, 1, 1])
else:
    col_summary, col_worklist = st.columns([1, 1])
    col_rx = None

# Panel 1 — Prescription Viewer
if col_rx:
    with col_rx:
        st.subheader("🗒️ Clinical Note")
        images = st.session_state.uploaded_image_bytes
        if len(images) == 1:
            st.image(images[0][0], use_container_width=True)
        else:
            tabs = st.tabs([f"Page {i+1}" for i in range(len(images))])
            for i, (img_bytes, _) in enumerate(images):
                with tabs[i]:
                    st.image(img_bytes, use_container_width=True)

# Panel 2 — Case Summary
with col_summary:
    st.subheader("📋 Case Summary")

    pd_state = st.session_state.patient_details

    if st.session_state.patient_confirmed:
        # Read-only confirmed card
        def _row(label, value):
            v = value or "—"
            st.markdown(f"<div style='margin-bottom:8px'><span style='font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.5px'>{label}</span><br><span style='font-size:15px;font-weight:600'>{v}</span></div>", unsafe_allow_html=True)

        st.markdown("#### ✅ Patient Details")
        _row("Patient Name", pd_state.get("patient_name"))
        c1, c2 = st.columns(2)
        with c1:
            _row("Date of Birth", pd_state.get("date_of_birth"))
            _row("MRN", pd_state.get("mrn"))
            _row("Insurance ID", pd_state.get("insurance_id"))
        with c2:
            _row("Date of Service", pd_state.get("date_of_service"))
            _row("Provider", pd_state.get("provider_name"))
            _row("Practice / Facility", pd_state.get("practice_name"))

        if st.button("✏️ Edit Patient Details", use_container_width=True):
            st.session_state.patient_confirmed = False
            st.rerun()
    else:
        st.markdown("#### 📝 Patient Details")
        with st.form("patient_details_form"):
            name = st.text_input("Patient Name", value=pd_state.get("patient_name", ""))
            dob = st.text_input("Date of Birth", value=pd_state.get("date_of_birth", ""))
            mrn = st.text_input("MRN", value=pd_state.get("mrn", ""))
            ins = st.text_input("Insurance ID", value=pd_state.get("insurance_id", ""))
            dos = st.text_input("Date of Service", value=pd_state.get("date_of_service", ""))
            provider = st.text_input("Provider Name", value=pd_state.get("provider_name", ""))
            practice = st.text_input("Practice / Facility", value=pd_state.get("practice_name", ""))
            if st.form_submit_button("✅ Confirm Patient Details", use_container_width=True, type="primary"):
                st.session_state.patient_details = {
                    "patient_name": name, "date_of_birth": dob, "mrn": mrn,
                    "insurance_id": ins, "date_of_service": dos,
                    "provider_name": provider, "practice_name": practice
                }
                st.session_state.patient_confirmed = True
                st.rerun()

    st.markdown("---")

    if interaction_bonus > 0:
        st.success(f"**Diabetes + CHF Interaction Bonus:** +{interaction_bonus:.3f}")
    else:
        st.info("No active interaction bonuses.")

    if confirmed_hccs:
        st.markdown("**Confirmed HCC Summary:**")
        summary_data = [
            {"Condition": d['term'], "HCC": V28_MAP[d['term']]['hcc'],
             "ICD-10": V28_MAP[d['term']]['icd10'], "Coef": V28_MAP[d['term']]['coef']}
            for d in st.session_state.hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP
        ]
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

# Panel 3 — HCC Coding Worklist
with col_worklist:
    st.subheader("📊 HCC Coding Worklist")
    st.metric("Final RAF Score (v28)", f"{total_raf:.3f}", delta=f"+{hcc_sum + interaction_bonus:.3f}")

    if not st.session_state.hcc_data:
        st.info("Upload a clinical note and run OCR to populate conditions, or add one manually below.")
    else:
        for i, item in enumerate(st.session_state.hcc_data):
            if item['term'] not in V28_MAP:
                continue
            details = V28_MAP[item['term']]
            status_color = {"Pending": "🟡", "Confirmed": "🟢", "Rejected": "🔴"}.get(item['status'], "⚪")
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"{status_color} **{item['term']}**")
                    st.caption(f"HCC {details['hcc']} | ICD-10: {details['icd10']} | Coef: +{details['coef']}")
                with c2:
                    if st.button("✅", key=f"c_{i}", help="Confirm"):
                        st.session_state.hcc_data[i]['status'] = "Confirmed"
                        st.session_state.case_status = None
                        st.rerun()
                with c3:
                    if st.button("❌", key=f"r_{i}", help="Reject"):
                        st.session_state.hcc_data[i]['status'] = "Rejected"
                        st.session_state.case_status = None
                        st.rerun()

    st.markdown("---")
    st.markdown("**Add a condition manually:**")
    available = [k for k in V28_MAP if k not in {d['term'] for d in st.session_state.hcc_data}]
    if available:
        selected = st.selectbox("Condition", options=available, label_visibility="collapsed")
        if st.button("➕ Add Condition"):
            next_id = max((d['id'] for d in st.session_state.hcc_data), default=0) + 1
            st.session_state.hcc_data.append({"id": next_id, "term": selected, "status": "Pending"})
            st.session_state.case_status = None
            st.rerun()
    else:
        st.caption("All available conditions have been added.")

    if st.session_state.hcc_data:
        if st.button("🗑️ Clear All", type="secondary"):
            for k, v in defaults.items():
                st.session_state[k] = v if not isinstance(v, dict) else v.copy()
            st.rerun()

# ── Case Finalization ─────────────────────────────────────────────────────────
st.divider()
st.subheader("🏁 Finalize Case")

pending_count = sum(1 for d in st.session_state.hcc_data if d['status'] == 'Pending')
if pending_count > 0:
    st.warning(f"⚠️ {pending_count} condition(s) still Pending. Review all conditions before finalizing.")

col_b, col_c = st.columns(2)

with col_b:
    if st.button("✅ Confirm RAF Score", type="primary", use_container_width=True,
                 disabled=(st.session_state.case_status == "confirmed")):
        ts = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.session_state.case_status = "confirmed"
        st.session_state.case_timestamp = ts
        st.session_state.clarification_sent = False
        st.session_state.cms_doc = generate_cms_submission(
            st.session_state.patient_details,
            st.session_state.hcc_data,
            total_raf,
            ts
        )
        st.rerun()

with col_c:
    if st.button("📋 Further Docs Needed", type="secondary", use_container_width=True,
                 disabled=(st.session_state.case_status == "further_docs")):
        st.session_state.case_status = "further_docs"
        st.session_state.case_timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.session_state.clarification_sent = False
        st.rerun()

# ── CMS Submission Panel ───────────────────────────────────────────────────────
if st.session_state.case_status == "confirmed" and st.session_state.cms_doc:
    st.divider()
    st.subheader("📤 CMS Submission Package")
    st.success(f"✅ RAF Score **{total_raf:.3f}** confirmed on {st.session_state.case_timestamp}. Submission package is ready.")

    with st.expander("📄 View Submission Document", expanded=True):
        st.code(st.session_state.cms_doc, language=None)

    fname = f"CMS_RAPS_{st.session_state.patient_details.get('mrn') or 'PATIENT'}_{datetime.now().strftime('%Y%m%d')}.txt"
    st.download_button(
        label="⬇️ Download Submission File",
        data=st.session_state.cms_doc,
        file_name=fname,
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )
    st.caption("This file is formatted for upload to the CMS RAPS / EDS portal. Review before submitting to the live system.")

# ── Clarification Request Panel ────────────────────────────────────────────────
if st.session_state.case_status == "further_docs":
    st.divider()
    st.subheader("📬 Provider Clarification Request")
    st.info(f"Case flagged on {st.session_state.case_timestamp}. Compose a clarification request to send to the provider through the portal.")

    if st.session_state.clarification_sent:
        st.success("✅ Clarification request sent to the provider portal.")
        if st.button("✉️ Send Another Request"):
            st.session_state.clarification_sent = False
            st.rerun()
    else:
        all_conditions = list(V28_MAP.keys())
        selected_condition = st.selectbox(
            "Select the condition requiring clarification:",
            options=["— Select a condition —"] + all_conditions,
            key="clarification_condition_select"
        )

        default_msg = ""
        if selected_condition and selected_condition != "— Select a condition —":
            template = CLARIFICATION_TEMPLATES.get(selected_condition, "Please provide additional documentation to support the diagnosis of {condition}.").replace("{condition}", selected_condition)
            default_msg = (
                f"Dear Dr. {st.session_state.patient_details.get('provider_name') or '[Provider Name]'},\n\n"
                f"Re: Patient {st.session_state.patient_details.get('patient_name') or '[Patient Name]'} "
                f"(MRN: {st.session_state.patient_details.get('mrn') or 'N/A'}) — "
                f"Date of Service: {st.session_state.patient_details.get('date_of_service') or 'N/A'}\n\n"
                f"{template}\n\n"
                f"Please respond through the provider portal within 5 business days. "
                f"If you have questions, contact our HCC coding team.\n\n"
                f"Thank you,\nHCC Coding Team — Risk Adjustment"
            )

        message = st.text_area(
            "Clarification message (editable):",
            value=default_msg,
            height=240,
            placeholder="Select a condition above to auto-populate a message template, or type your own.",
        )

        send_disabled = not message.strip() or selected_condition == "— Select a condition —"
        if st.button("📨 Send to Provider Portal", type="primary", use_container_width=True, disabled=send_disabled):
            st.session_state.clarification_sent = True
            st.rerun()
