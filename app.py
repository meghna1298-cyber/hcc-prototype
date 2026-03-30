import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(layout="wide", page_title="V28 HCC AI Coder")

# --- V28 Logic Data ---
V28_MAP = {
    "Diabetes (Any Type)": {"hcc": "37", "coef": 0.166, "icd10": "E11.9"},
    "CKD Stage 3a": {"hcc": "329", "coef": 0.288, "icd10": "N18.31"},
    "Congestive Heart Failure": {"hcc": "226", "coef": 0.360, "icd10": "I50.9"},
    "Atrial Fibrillation": {"hcc": "238", "coef": 0.299, "icd10": "I48.0"},
}

if 'hcc_data' not in st.session_state:
    st.session_state.hcc_data = [
        {"id": 1, "term": "Diabetes (Any Type)", "status": "Pending"},
        {"id": 2, "term": "CKD Stage 3a", "status": "Pending"},
        {"id": 3, "term": "Congestive Heart Failure", "status": "Pending"}
    ]

st.title("🩺 AI-Assisted Clinical Coder (v28 Model)")
st.caption("CMS-HCC Version 28 | 100% Phase-in Compliance (2026)")
st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Clinical Documentation")
    st.image("https://via.placeholder.com/600x600.png?text=V28+Evidence+Tracing+Overlay", use_container_width=True)

with col2:
    base_raf = 0.350
    confirmed_hccs = [V28_MAP[d['term']] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
    hcc_sum = sum([item['coef'] for item in confirmed_hccs])
    
    interaction_bonus = 0.0
    confirmed_terms = [d['term'] for d in st.session_state.hcc_data if d['status'] == 'Confirmed']
    if "Diabetes (Any Type)" in confirmed_terms and "Congestive Heart Failure" in confirmed_terms:
        interaction_bonus = 0.112

    total_raf = base_raf + hcc_sum + interaction_bonus
    st.metric("Final RAF Score (v28)", f"{total_raf:.3f}", delta=f"+{hcc_sum + interaction_bonus:.3f}")

    for i, item in enumerate(st.session_state.hcc_data):
        details = V28_MAP[item['term']]
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{item['term']}**")
                st.caption(f"HCC {details['hcc']} | ICD-10: {details['icd10']}")
            with c2:
                if st.button("✅", key=f"c_{i}"):
                    st.session_state.hcc_data[i]['status'] = "Confirmed"
                    st.rerun()
            with c3:
                if st.button("❌", key=f"r_{i}"):
                    st.session_state.hcc_data[i]['status'] = "Rejected"
                    st.rerun()
