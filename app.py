import streamlit as st
import pandas as pd
import base64
import os
import json
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
    "Diabetes (Any Type)": {"hcc": "37", "coef": 0.166, "icd10": "E11.9"},
    "CKD Stage 3a": {"hcc": "329", "coef": 0.288, "icd10": "N18.31"},
    "Congestive Heart Failure": {"hcc": "226", "coef": 0.360, "icd10": "I50.9"},
    "Atrial Fibrillation": {"hcc": "238", "coef": 0.299, "icd10": "I48.0"},
    "COPD": {"hcc": "280", "coef": 0.345, "icd10": "J44.9"},
    "Hypertension": {"hcc": "136", "coef": 0.201, "icd10": "I10"},
    "Obesity": {"hcc": "48", "coef": 0.272, "icd10": "E66.9"},
    "Peripheral Vascular Disease": {"hcc": "108", "coef": 0.288, "icd10": "I73.9"},
    "Coronary Artery Disease": {"hcc": "86", "coef": 0.217, "icd10": "I25.10"},
    "Major Depression": {"hcc": "59", "coef": 0.395, "icd10": "F32.9"},
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


def ocr_clinical_note(image_bytes: bytes, mime_type: str) -> dict:
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_image}"
    known_conditions = "\n".join(f"- {k}" for k in V28_MAP.keys())
    prompt = f"""You are a clinical coding assistant specializing in CMS-HCC Version 28.

Carefully read this clinical note image (which may be handwritten or typed/printed) and:
1. Extract all the raw text from the note (OCR)
2. Identify which of the following HCC-relevant conditions are mentioned or implied:

{known_conditions}

3. Extract any patient details visible in the note. Use empty string "" if a field is not found.

Respond in this exact JSON format:
{{
  "extracted_text": "<full transcription of the note>",
  "detected_conditions": ["<condition name from list above>", ...],
  "clinical_summary": "<1-2 sentence summary of the note>",
  "patient_details": {{
    "patient_name": "",
    "date_of_birth": "",
    "mrn": "",
    "insurance_id": "",
    "date_of_service": "",
    "provider_name": "",
    "practice_name": ""
  }}
}}

Only include conditions from the provided list. If a condition is not clearly present, do not include it."""

    response = openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]}],
        response_format={"type": "json_object"},
        max_completion_tokens=8192
    )
    return json.loads(response.choices[0].message.content)


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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🩺 AI-Assisted Clinical Coder (v28 Model)")
st.caption("CMS-HCC Version 28 | 100% Phase-in Compliance (2026)")

confirmed_terms_top = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
if st.session_state.case_status == "confirmed":
    ib = 0.112 if ("Diabetes (Any Type)" in confirmed_terms_top and "Congestive Heart Failure" in confirmed_terms_top) else 0.0
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
            st.info(res.get("clinical_summary", ""))
            for cond in res.get("detected_conditions", []):
                st.success(f"✓ {cond}")

st.divider()

# ── Compute RAF ──────────────────────────────────────────────────────────────
base_raf = 0.350
confirmed_hccs = [V28_MAP[d['term']] for d in st.session_state.hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP]
hcc_sum = sum(h['coef'] for h in confirmed_hccs)
confirmed_terms = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
interaction_bonus = 0.112 if ("Diabetes (Any Type)" in confirmed_terms and "Congestive Heart Failure" in confirmed_terms) else 0.0
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

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    if st.session_state.case_status == "confirmed":
        st.success(f"✅ Case confirmed — RAF Score **{total_raf:.3f}**")
    elif st.session_state.case_status == "further_docs":
        st.warning("📋 Case flagged — further documentation required.")
    else:
        st.caption("Review all conditions and patient details above, then finalize.")
with col_b:
    if st.button("✅ Confirm RAF Score", type="primary", use_container_width=True,
                 disabled=(st.session_state.case_status == "confirmed")):
        st.session_state.case_status = "confirmed"
        st.session_state.case_timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.rerun()
with col_c:
    if st.button("📋 Further Docs Needed", type="secondary", use_container_width=True,
                 disabled=(st.session_state.case_status == "further_docs")):
        st.session_state.case_status = "further_docs"
        st.session_state.case_timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.rerun()
