"""
Streamlit Clinician Portal & EMR Dual Coding Interface
Smart India Hackathon 2025 Prototype
Demonstrating real-time mapping between AYUSH (NAMASTE) and WHO ICD-11
conforming to HL7 FHIR Release 4 & ABDM standards.
"""

import json
import streamlit as st
import pandas as pd

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder

# Page configuration
st.set_page_config(
    page_title="FHIR Dual-Coding EMR | NAMASTE & ICD-11",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clean healthcare UI
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.2rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .badge-green { background-color: #d1fae5; color: #065f46; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .card-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #edf2f7;
        border-left: 4px solid #3182ce;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Engine
@st.cache_resource
def get_engine():
    return MappingEngine()

engine = get_engine()

# Sidebar: Configuration & Patient Details
with st.sidebar:
    st.image("https://img.icons8.com/color/96/caduceus.png", width=64)
    st.markdown("### 🏥 EMR Encounter Simulator")
    st.caption("Smart India Hackathon 2025 Demo")
    
    st.divider()
    st.markdown("#### 👤 Patient Details (ABDM)")
    patient_name = st.text_input("Patient Full Name", value="Rahul Sharma")
    patient_abha = st.text_input("ABHA ID (National Health ID)", value="ABHA-91-8765-4321-0987")
    doctor_name = st.text_input("Attending Practitioner", value="Dr. S. K. Roy (BAMS)")
    
    st.divider()
    st.markdown("#### ⚙️ Clinical Settings")
    clinical_status = st.selectbox(
        "Clinical Status",
        options=["active", "recurrence", "relapse", "remission", "resolved"],
        index=0,
    )
    verification_status = st.selectbox(
        "Verification Status",
        options=["confirmed", "provisional", "differential", "unconfirmed"],
        index=0,
    )

    st.divider()
    stats = engine.get_summary_stats()
    st.markdown("#### 📊 Terminology Coverage")
    st.metric("Total Dual-Coded Diagnoses", stats["total_records"])
    for sys_name, count in stats["systems"].items():
        st.write(f"- **{sys_name}**: {count} mapped terms")

# Main Header
st.markdown('<div class="main-title">🌿 FHIR-Based Dual Coding Microservice</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Bridging India\'s <b>NAMASTE (AYUSH)</b> & WHO <b>ICD-11</b> into Standardized EMR Systems using HL7 FHIR R4</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <span class="badge-pill badge-green">✓ HL7 FHIR R4 Compliant</span>
    <span class="badge-pill badge-blue">✓ EHR Standards of India (2016)</span>
    <span class="badge-pill badge-purple">✓ Smart India Hackathon 2025</span>
    """,
    unsafe_allow_html=True,
)
st.write("")

# Navigation Tabs
tabs = st.tabs([
    "🩺 Clinician Dual-Coding Entry",
    "🔍 Search & Vocabulary Directory",
    "🔄 Bidirectional Translator",
    "🗺️ FHIR ConceptMap & CodeSystem",
    "📄 Problem List Bundle",
    "ℹ️ SIH Project Overview",
])

# TAB 1: Clinician Dual-Coding Entry
with tabs[0]:
    st.subheader("1. Patient Diagnosis & Automatic Dual Coding")
    st.write(
        "A clinician selects or searches for an AYUSH diagnosis in NAMASTE. The microservice automatically resolves the "
        "matching WHO ICD-11 code and generates a standardized, dual-coded **FHIR R4 Condition resource**."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        # Search dropdown
        system_filter = st.selectbox(
            "Filter by Traditional System:",
            ["All Systems", "Ayurveda", "Unani", "Siddha", "Homeopathy"],
            index=0,
        )
        filter_val = None if system_filter == "All Systems" else system_filter

        records = engine.search(query="", system=filter_val, limit=100)
        record_options = {
            f"[{r['namaste_code']}] {r['traditional_term']} ({r['system']}) → {r['icd11_title']} [{r['icd11_code']}]": r
            for r in records
        }

        selected_label = st.selectbox("Select Diagnosis from NAMASTE Directory:", list(record_options.keys()))
        selected_record = record_options[selected_label]

    with col2:
        st.markdown("#### 📋 Diagnostic Preview")
        st.info(
            f"**NAMASTE Code:** `{selected_record['namaste_code']}`\n\n"
            f"**Term:** {selected_record['traditional_term']} ({selected_record['system']})\n\n"
            f"**Mapped ICD-11:** `{selected_record['icd11_code']}` - {selected_record['icd11_title']}\n\n"
            f"**Confidence:** `{selected_record['mapping_confidence'] * 100:.0f}%` ({selected_record['mapping_equivalence']})"
        )

    clinical_note = st.text_area(
        "Clinician Consultation Notes / Observations:",
        value=f"Patient diagnosed with {selected_record['traditional_term']}. Presenting with complaints related to {selected_record['english_description']}.",
        height=80,
    )

    if st.button("🚀 Generate & Upload Dual-Coded FHIR R4 Record", type="primary", use_container_width=True):
        condition_json = FHIRBuilder.create_dual_coded_condition(
            namaste_record=selected_record,
            patient_id=patient_abha,
            patient_name=patient_name,
            doctor_name=doctor_name,
            clinical_status=clinical_status,
            verification_status=verification_status,
            notes=clinical_note,
        )

        st.success("✅ Dual-Coded FHIR R4 Condition Resource Generated Successfully!")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🔍 Coding Comparison")
            comp_df = pd.DataFrame([
                {
                    "Standard": "NAMASTE (AYUSH)",
                    "Code": selected_record["namaste_code"],
                    "Display": selected_record["traditional_term"],
                    "System URI": "https://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
                    "Status": "Primary User Diagnosis",
                },
                {
                    "Standard": "WHO ICD-11 MMS",
                    "Code": selected_record["icd11_code"],
                    "Display": selected_record["icd11_title"],
                    "System URI": "http://id.who.int/icd/release/11/mms",
                    "Status": f"Auto-Mapped ({selected_record['mapping_equivalence']})",
                },
            ])
            st.dataframe(comp_df, hide_index=True, use_container_width=True)

        with col_b:
            st.markdown("#### ⚡ Clinical Description")
            st.write(f"**Category:** {selected_record['category']}")
            st.write(f"**English Clinical Sense:** {selected_record['english_description']}")
            st.write(f"**WHO Entity URI:** [{selected_record['icd11_uri']}]({selected_record['icd11_uri']})")

        st.markdown("#### 📄 Exported HL7 FHIR R4 JSON Resource")
        st.json(condition_json)

        st.download_button(
            label="📥 Download FHIR Condition JSON",
            data=json.dumps(condition_json, indent=2),
            file_name=f"fhir_condition_{selected_record['namaste_code']}.json",
            mime="application/json",
        )

# TAB 2: Search & Vocabulary Directory
with tabs[1]:
    st.subheader("2. Search NAMASTE & ICD-11 Terminology")
    st.write("Fuzzy search across traditional names, clinical descriptions, NAMASTE codes, and ICD-11 terms.")

    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        search_query = st.text_input("Enter disease name, symptom, or code (e.g., 'Amlapitta', 'Asthma', 'Diabetes', 'Jaundice'):", "")
    with s_col2:
        search_sys = st.selectbox("System:", ["All", "Ayurveda", "Unani", "Siddha", "Homeopathy"], index=0)

    results = engine.search(query=search_query, system=None if search_sys == "All" else search_sys, limit=50)

    st.write(f"Found **{len(results)}** matching terminology records:")

    table_data = []
    for r in results:
        table_data.append({
            "NAMASTE Code": r["namaste_code"],
            "System": r["system"],
            "Traditional Term": r["traditional_term"],
            "Clinical Description": r["english_description"],
            "ICD-11 Code": r["icd11_code"],
            "ICD-11 Title": r["icd11_title"],
            "Equivalence": r["mapping_equivalence"],
            "Confidence": f"{r['mapping_confidence'] * 100:.0f}%",
        })

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No records matched your search query.")

# TAB 3: Bidirectional Translator
with tabs[2]:
    st.subheader("3. Bidirectional Terminology Translator")
    st.write("Translate directly between NAMASTE and WHO ICD-11 codes.")

    trans_mode = st.radio(
        "Choose Translation Direction:",
        ["NAMASTE → WHO ICD-11", "WHO ICD-11 → NAMASTE"],
        horizontal=True,
    )

    if trans_mode == "NAMASTE → WHO ICD-11":
        input_code = st.text_input("Enter NAMASTE Code:", value="NAM-AYU-001")
        if st.button("Translate to ICD-11"):
            res = engine.translate(code=input_code, source_type="namaste")
            if res.get("status") == "success":
                st.success("✅ Translation Match Found!")
                st.write(f"**Traditional Term:** {res['source_term']} ({res['ayush_system']})")
                st.write(f"**Target ICD-11 Code:** `{res['target_code']}`")
                st.write(f"**Target ICD-11 Title:** {res['target_title']}")
                st.write(f"**Semantic Equivalence:** `{res['equivalence']}` (Confidence: {res['confidence'] * 100:.1f}%)")
                st.write(f"**Clinical Description:** {res['clinical_description']}")
            else:
                st.error(res.get("message"))
    else:
        input_icd = st.text_input("Enter ICD-11 Code (e.g., 5A11, CA23, DA42):", value="5A11")
        if st.button("Translate to NAMASTE"):
            res = engine.translate(code=input_icd, source_type="icd11")
            if res.get("status") == "success":
                st.success(f"✅ Found {res['mappings_count']} corresponding NAMASTE diagnoses for ICD-11 '{res['source_code']}':")
                for m in res["mappings"]:
                    st.write(f"- **{m['target_term']}** (`{m['target_code']}`) | **System:** {m['ayush_system']} | Equivalence: `{m['equivalence']}`")
            else:
                st.error(res.get("message"))

# TAB 4: FHIR ConceptMap & CodeSystem
with tabs[3]:
    st.subheader("4. HL7 FHIR R4 Standards Specifications")
    st.write(
        "Under the **EHR Standards of India (2016)**, all clinical vocabularies and mappings must be published as "
        "interoperable FHIR `CodeSystem` and `ConceptMap` resources."
    )

    spec_choice = st.radio("Select FHIR Resource to inspect:", ["ConceptMap (NAMASTE to ICD-11)", "CodeSystem (NAMASTE)"], horizontal=True)

    if spec_choice.startswith("ConceptMap"):
        concept_map = FHIRBuilder.create_concept_map(engine.records)
        st.caption(f"Resource Type: `{concept_map['resourceType']}` | Total Mapped Elements: {len(concept_map['group'][0]['element'])}")
        st.json(concept_map)
        st.download_button(
            "📥 Download FHIR ConceptMap JSON",
            data=json.dumps(concept_map, indent=2),
            file_name="fhir_conceptmap_namaste_icd11.json",
            mime="application/json",
        )
    else:
        code_sys = FHIRBuilder.create_code_system(engine.records)
        st.caption(f"Resource Type: `{code_sys['resourceType']}` | Total Concepts: {code_sys['count']}")
        st.json(code_sys)
        st.download_button(
            "📥 Download FHIR CodeSystem JSON",
            data=json.dumps(code_sys, indent=2),
            file_name="fhir_codesystem_namaste.json",
            mime="application/json",
        )

# TAB 5: Problem List Bundle
with tabs[4]:
    st.subheader("5. Patient Problem List & FHIR Bundle Builder")
    st.write("Combine multiple patient diagnoses into a standardized FHIR `Bundle` (Collection) for EMR interchange.")

    multi_conditions = st.multiselect(
        "Select Multiple Patient Diagnoses:",
        options=[r["namaste_code"] for r in engine.records],
        default=["NAM-AYU-001", "NAM-AYU-003"],
        format_func=lambda c: f"{c} - {engine.get_by_namaste_code(c)['traditional_term']} ({engine.get_by_namaste_code(c)['system']})",
    )

    if st.button("📦 Build FHIR Bundle (ProblemList)", type="primary"):
        condition_resources = []
        for c_code in multi_conditions:
            rec = engine.get_by_namaste_code(c_code)
            c_res = FHIRBuilder.create_dual_coded_condition(
                namaste_record=rec,
                patient_id=patient_abha,
                patient_name=patient_name,
                doctor_name=doctor_name,
            )
            condition_resources.append(c_res)

        bundle = FHIRBuilder.create_problem_list_bundle(condition_resources)
        st.success(f"✅ Generated FHIR R4 Bundle containing {bundle['total']} dual-coded condition entries!")
        st.json(bundle)
        st.download_button(
            "📥 Download FHIR Bundle JSON",
            data=json.dumps(bundle, indent=2),
            file_name="fhir_problem_list_bundle.json",
            mime="application/json",
        )

# TAB 6: SIH Project Overview
with tabs[5]:
    st.subheader("6. Smart India Hackathon 2025 Background & Project Scope")
    st.markdown(
        """
        ### 🎯 Problem Statement & Need
        In India's digital health ecosystem (ABDM / Ayushman Bharat Digital Mission), millions of patients consult AYUSH 
        (Ayurveda, Yoga & Naturopathy, Unani, Siddha, Homeopathy) practitioners. However:
        - **AYUSH diagnoses** are codified under the **NAMASTE** portal.
        - **Modern global healthcare systems and health insurers** rely on **WHO ICD-11**.
        - Lack of semantic alignment leads to **claim processing delays**, **limited clinical documentation exchange**, 
          and **fragmented healthcare analytics**.

        ### 💡 Our Proposed Solution
        A **FHIR-Based Dual Coding Microservice** that acts as an automated translation layer:
        1. **Transforms NAMASTE datasets** into standardized HL7 FHIR `CodeSystem` entities.
        2. **Maps terms to WHO ICD-11** via HL7 FHIR `ConceptMap` specifications.
        3. **Emits Dual-Coded FHIR R4 Condition & ProblemList resources**, satisfying both traditional practitioners and global EMR standards.
        4. **ABDM & ABHA Ready**: Aligns directly with EHR Standards of India (2016).

        ---
        ### 👥 Hackathon Team Credits (Assam Down Town University)
        - **MD Arif Ul Islam**
        - **MD Samiur Rahman Tanim**
        - **Atikur Rahman**
        - **Farhan Masud**
        - **S M Zafor Abbasi**
        - **Soudamoni Pandit**
        
        *Achievement: Qualified and advanced to Round 2 in Smart India Hackathon 2025.*

        ---
        > **Disclaimer:** This software is an open-source research and educational prototype developed to demonstrate 
        > the architectural feasibility of traditional and modern health code interoperability. It is not intended for direct clinical decision-making.
        """
    )
