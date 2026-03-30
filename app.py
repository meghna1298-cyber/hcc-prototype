import streamlit as st
import pandas as pd
import base64
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
AI_MODEL = "gpt-5"

openai_client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

# --- Page Config ---
st.set_page_config(layout="wide", page_title="V28 HCC AI Coder")

# --- V28 Logic Data ---
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

def ocr_clinical_note(image_bytes: bytes, mime_type: str) -> dict:
    """Send a clinical note image to GPT vision and extract HCC conditions."""
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_image}"

    known_conditions = "\n".join(f"- {k}" for k in V28_MAP.keys())

    prompt = f"""You are a clinical coding assistant specializing in CMS-HCC Version 28.

Carefully read this handwritten clinical note image and:
1. Extract all the raw text from the handwritten note (OCR)
2. Identify which of the following HCC-relevant conditions are mentioned or implied:

{known_conditions}

Respond in this exact JSON format:
{{
  "extracted_text": "<full transcription of the handwritten note>",
  "detected_conditions": ["<condition name from list above>", ...],
  "clinical_summary": "<1-2 sentence summary of the note>"
}}

Only include conditions from the provided list. If a condition is not clearly present, do not include it."""

    response = openai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=8192
    )

    import json
    return json.loads(response.choices[0].message.content)


# --- Session State Init ---
if 'hcc_data' not in st.session_state:
    st.session_state.hcc_data = []

if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None

if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None

# --- Header ---
st.title("🩺 AI-Assisted Clinical Coder (v28 Model)")
st.caption("CMS-HCC Version 28 | 100% Phase-in Compliance (2026)")
st.divider()

# --- Upload Section ---
st.subheader("📄 Upload Clinical Note")
st.write("Upload a photo or scan of a handwritten clinical note. The AI will read it and automatically identify HCC conditions.")

uploaded_file = st.file_uploader(
    "Choose an image file",
    type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
    help="Upload a clear photo or scan of the handwritten prescription or clinical note."
)

if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    mime_type = uploaded_file.type or "image/jpeg"
    st.session_state.uploaded_image = image_bytes

    col_img, col_btn = st.columns([3, 1])
    with col_img:
        st.image(image_bytes, caption="Uploaded Clinical Note", use_container_width=True)
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔍 Run OCR & Extract HCCs", type="primary", use_container_width=True):
            with st.spinner("Reading handwritten note and identifying HCC conditions..."):
                try:
                    result = ocr_clinical_note(image_bytes, mime_type)
                    st.session_state.ocr_result = result

                    detected = result.get("detected_conditions", [])
                    existing_terms = {d['term'] for d in st.session_state.hcc_data}
                    next_id = max((d['id'] for d in st.session_state.hcc_data), default=0) + 1

                    added = []
                    for condition in detected:
                        if condition in V28_MAP and condition not in existing_terms:
                            st.session_state.hcc_data.append({
                                "id": next_id,
                                "term": condition,
                                "status": "Pending"
                            })
                            existing_terms.add(condition)
                            next_id += 1
                            added.append(condition)

                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "FREE_CLOUD_BUDGET_EXCEEDED" in error_msg:
                        st.error("Your Replit AI cloud budget has been exceeded. Please check your account.")
                    else:
                        st.error(f"Error processing image: {error_msg}")

# --- Show OCR Results ---
if st.session_state.ocr_result:
    result = st.session_state.ocr_result
    with st.expander("📝 OCR Results — Extracted Note Text", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Transcribed Text:**")
            st.text_area("", value=result.get("extracted_text", ""), height=150, disabled=True, label_visibility="collapsed")
        with col2:
            st.markdown("**Clinical Summary:**")
            st.info(result.get("clinical_summary", ""))
            detected = result.get("detected_conditions", [])
            if detected:
                st.markdown("**Detected Conditions:**")
                for c in detected:
                    st.success(f"✓ {c}")
            else:
                st.warning("No known HCC conditions detected in this note.")

st.divider()

# --- HCC Coding Panel ---
col1, col2 = st.columns([1, 1])

with col2:
    base_raf = 0.350
    confirmed_hccs = [V28_MAP[d['term']] for d in st.session_state.hcc_data if d['status'] == 'Confirmed' and d['term'] in V28_MAP]
    hcc_sum = sum([item['coef'] for item in confirmed_hccs])

    interaction_bonus = 0.0
    confirmed_terms = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
    if "Diabetes (Any Type)" in confirmed_terms and "Congestive Heart Failure" in confirmed_terms:
        interaction_bonus = 0.112

    total_raf = base_raf + hcc_sum + interaction_bonus

    st.subheader("📊 HCC Coding Worklist")
    st.metric("Final RAF Score (v28)", f"{total_raf:.3f}", delta=f"+{hcc_sum + interaction_bonus:.3f}")

    if not st.session_state.hcc_data:
        st.info("Upload a clinical note above to automatically populate HCC conditions, or add one manually below.")
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
                    if st.button("✅ Confirm", key=f"c_{i}"):
                        st.session_state.hcc_data[i]['status'] = "Confirmed"
                        st.rerun()
                with c3:
                    if st.button("❌ Reject", key=f"r_{i}"):
                        st.session_state.hcc_data[i]['status'] = "Rejected"
                        st.rerun()

    # Manual add
    st.markdown("---")
    st.markdown("**Add a condition manually:**")
    available = [k for k in V28_MAP.keys() if k not in {d['term'] for d in st.session_state.hcc_data}]
    if available:
        selected = st.selectbox("Select condition", options=available, label_visibility="collapsed")
        if st.button("➕ Add Condition"):
            next_id = max((d['id'] for d in st.session_state.hcc_data), default=0) + 1
            st.session_state.hcc_data.append({"id": next_id, "term": selected, "status": "Pending"})
            st.rerun()
    else:
        st.caption("All available conditions have been added.")

    if st.session_state.hcc_data:
        if st.button("🗑️ Clear All", type="secondary"):
            st.session_state.hcc_data = []
            st.session_state.ocr_result = None
            st.session_state.uploaded_image = None
            st.rerun()

with col1:
    st.subheader("📋 Interaction Bonuses")
    if interaction_bonus > 0:
        st.success(f"**Diabetes + CHF Interaction:** +{interaction_bonus:.3f}")
    else:
        st.info("No active interaction bonuses. Confirm both Diabetes and Congestive Heart Failure to trigger the +0.112 interaction.")

    if confirmed_hccs:
        st.markdown("**Confirmed HCC Summary:**")
        summary_data = [
            {
                "Condition": d['term'],
                "HCC": V28_MAP[d['term']]['hcc'],
                "ICD-10": V28_MAP[d['term']]['icd10'],
                "Coefficient": V28_MAP[d['term']]['coef']
            }
            for d in st.session_state.hcc_data
            if d['status'] == 'Confirmed' and d['term'] in V28_MAP
        ]
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
