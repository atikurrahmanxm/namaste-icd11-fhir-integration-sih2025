"""
Streamlit Clinician Portal & EMR Dual Coding Interface
Smart India Hackathon 2025 Prototype
Demonstrating real-time mapping between AYUSH (NAMASTE) and WHO ICD-11
conforming to HL7 FHIR Release 4 & ABDM standards.
"""

import json
import re
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder

# Configure page
st.set_page_config(
    page_title="AyurCode FHIR | Dual-Coding Microservice",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enterprise HealthTech Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f766e 100%);
        padding: 24px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.15);
    }
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-subtitle {
        font-size: 0.98rem;
        color: #cbd5e1;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    .pill-tag {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .pill-green { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.4); }
    .pill-blue  { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.4); }
    .pill-purple{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.4); }
    
    .clinical-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .status-badge {
        font-size: 0.8rem;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .status-active { background: #dcfce7; color: #166534; }
    .status-mapped { background: #e0f2fe; color: #075985; }

    .stat-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .stat-number {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f766e;
    }
    .stat-label {
        font-size: 0.78rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource
def get_engine():
    return MappingEngine()

engine = get_engine()

# Helper for ABHA format check
def validate_abha(abha_str: str) -> bool:
    pattern = r"^\d{2}-\d{4}-\d{4}-\d{4}$"
    return bool(re.match(pattern, abha_str.strip())) or abha_str.startswith("ABHA-")

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-heart.png", width=64)
    st.markdown("### 🏥 ABDM EMR Gateway")
    st.caption("Smart India Hackathon 2025 · Live Clinical Prototype")
    
    st.divider()
    st.markdown("#### 👤 Patient Demographics")
    patient_name = st.text_input("Patient Full Name", value="Rahul Sharma")
    patient_abha = st.text_input("ABHA Number (14 digits)", value="91-8765-4321-0987")
    
    is_valid_abha = validate_abha(patient_abha)
    if is_valid_abha:
        st.markdown('<span class="status-badge status-active">✓ Valid ABHA ID Format</span>', unsafe_allow_html=True)
    else:
        st.warning("Format: XX-XXXX-XXXX-XXXX")

    gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)
    age = st.number_input("Age (Years)", min_value=1, max_value=120, value=38)

    st.divider()
    st.markdown("#### 👨‍⚕️ Clinician Information")
    doctor_name = st.text_input("Consulting Doctor", value="Dr. S. K. Roy (BAMS)")
    facility_name = st.text_input("Facility Name", value="National AYUSH Integrated Hospital")
    clinical_status = st.selectbox("Clinical Status", ["active", "recurrence", "relapse", "remission", "resolved"], index=0)
    verification_status = st.selectbox("Verification Status", ["confirmed", "provisional", "differential", "unconfirmed"], index=0)

    st.divider()
    st.markdown("#### ⚡ System Telemetry")
    stats = engine.get_summary_stats()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{stats["total_records"]}</div><div class="stat-label">Mapped Diagnoses</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{stats["average_confidence_score"]}%</div><div class="stat-label">Avg Confidence</div></div>', unsafe_allow_html=True)

# Main Banner
st.markdown(
    """
    <div class="main-header">
        <h1 class="main-title">🌿 AyurCode FHIR: Dual-Coding Microservice</h1>
        <div class="main-subtitle">
            Automated semantic translation between India's <b>NAMASTE (AYUSH)</b> and <b>WHO ICD-11</b> 
            aligned with <b>EHR Standards of India (2016)</b> & <b>HL7® FHIR® R4</b>.
        </div>
        <div>
            <span class="pill-tag pill-green">✓ HL7 FHIR Release 4 Compliant</span>
            <span class="pill-tag pill-blue">✓ ABDM / NRCES Profile Compatible</span>
            <span class="pill-tag pill-purple">✓ Smart India Hackathon 2025 Prototype</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Tabs
tabs = st.tabs([
    "🩺 1. Live Dual-Coding Encounter",
    "🏥 2. ABDM Document Bundle",
    "🔍 3. Terminology & Symptom Directory",
    "🔄 4. Bidirectional Translator",
    "🗺️ 5. FHIR Standards Inspector",
    "🛡️ 6. ISO 22600 Audit & Security",
    "🏛️ 7. SIH Project Blueprint",
])

# -------------------------------------------------------------
# TAB 1: Live Dual-Coding Encounter
# -------------------------------------------------------------
with tabs[0]:
    st.markdown('<div class="section-title">Step 1: Clinical Diagnosis Entry & Dual-Coding Resolution</div>', unsafe_allow_html=True)
    st.write(
        "Select or search for a traditional diagnosis. The microservice instantaneously pairs it with its exact "
        "WHO ICD-11 counterpart (both MMS code and Chapter 26 Traditional Medicine Module 1 code)."
    )

    col_diag1, col_diag2 = st.columns([2, 1])
    with col_diag1:
        sys_filter = st.selectbox(
            "Filter by Traditional Medical System:",
            ["All Systems", "Ayurveda", "Unani", "Siddha", "Homeopathy"],
            index=0,
        )
        selected_sys = None if sys_filter == "All Systems" else sys_filter
        available_records = engine.search(query="", system=selected_sys, limit=100)

        record_map = {
            f"[{r['namaste_code']}] {r['traditional_term']} ({r['system']}) → {r['icd11_title']} [{r['icd11_code']}]": r
            for r in available_records
        }
        chosen_label = st.selectbox("Select Diagnosis from NAMASTE Directory:", list(record_map.keys()))
        rec = record_map[chosen_label]

    with col_diag2:
        st.markdown("#### 🎯 Semantic Resolution")
        conf_pct = int(rec["mapping_confidence"] * 100)
        st.progress(conf_pct / 100)
        st.markdown(
            f"""
            - **Confidence Score:** `{conf_pct}%`
            - **Equivalence:** `{rec['mapping_equivalence'].upper()}`
            - **WHO MMS Code:** `{rec['icd11_code']}`
            - **WHO TM-1 Code:** `{rec.get('icd11_tm1_code', 'N/A')}`
            """
        )

    # Disease Insight Card
    st.markdown(
        f"""
        <div class="clinical-card">
            <h4 style="margin-top:0; color:#0f766e;">📋 {rec['traditional_term']} ({rec['system']}) <span style="font-size:0.85rem; color:#64748b;">[{rec['namaste_code']}]</span></h4>
            <p><b>Clinical Category:</b> {rec['category']}</p>
            <p><b>Clinical Description:</b> {rec['english_description']}</p>
            <p><b>Scientific Mapping Rationale:</b> {rec.get('clinical_rationale', 'Direct semantic equivalence established.')}</p>
            <div>
                <b>Associated Symptoms:</b><br/>
                {' '.join([f'<span class="pill-tag pill-blue">{s}</span>' for s in rec.get('symptoms', [])])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    consult_note = st.text_area(
        "Practitioner Consultation Notes:",
        value=f"Patient presents with cardinal signs of {rec['traditional_term']}. Advised standard constitutional management.",
        height=70,
    )

    if st.button("🚀 Generate & Validate Dual-Coded FHIR R4 Condition", type="primary", use_container_width=True):
        cond_resource = FHIRBuilder.create_dual_coded_condition(
            namaste_record=rec,
            patient_id=patient_abha,
            patient_name=patient_name,
            doctor_name=doctor_name,
            clinical_status=clinical_status,
            verification_status=verification_status,
            notes=consult_note,
        )

        is_valid, validation_errors = FHIRBuilder.validate_resource(cond_resource)

        if is_valid:
            st.success("✅ HL7 FHIR R4 Condition Resource Generated and Successfully Validated against ABDM NRCES Profile!")
        else:
            st.error(f"Validation Warning: {validation_errors}")

        # Summary Table
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("#### 🔍 Coding Comparison Table")
            df_compare = pd.DataFrame([
                {
                    "Standard": "NAMASTE (AYUSH)",
                    "Code": rec["namaste_code"],
                    "Display Term": rec["traditional_term"],
                    "URI": "https://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
                    "Role": "Primary AYUSH Diagnosis",
                },
                {
                    "Standard": "WHO ICD-11 MMS",
                    "Code": rec["icd11_code"],
                    "Display Term": rec["icd11_title"],
                    "URI": "http://id.who.int/icd/release/11/mms",
                    "Role": f"International Equivalent ({rec['mapping_equivalence']})",
                },
                {
                    "Standard": "WHO ICD-11 Chapter 26 (TM-1)",
                    "Code": rec.get("icd11_tm1_code", "TM1-GEN-01"),
                    "Display Term": f"{rec['traditional_term']} (TM1)",
                    "URI": "http://id.who.int/icd/release/11/tm1",
                    "Role": "WHO Traditional Medicine Module",
                },
            ])
            st.dataframe(df_compare, hide_index=True, use_container_width=True)

        with c_right:
            st.markdown("#### 🏥 Encounter Overview")
            st.write(f"- **Patient Name:** {patient_name} ({gender}, {age} yrs)")
            st.write(f"- **ABHA ID:** `{patient_abha}`")
            st.write(f"- **Attending Practitioner:** {doctor_name}")
            st.write(f"- **Clinical Status:** `{clinical_status}` | Verification: `{verification_status}`")
            st.write(f"- **Timestamp:** `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`")

        # JSON Viewer
        st.markdown("#### 📄 Standardized HL7 FHIR R4 Condition JSON")
        st.json(cond_resource)

        st.download_button(
            label="📥 Download Condition JSON Resource",
            data=json.dumps(cond_resource, indent=2),
            file_name=f"fhir_condition_{rec['namaste_code']}_{patient_abha}.json",
            mime="application/json",
            use_container_width=True,
        )

# -------------------------------------------------------------
# TAB 2: ABDM Document Bundle
# -------------------------------------------------------------
with tabs[1]:
    st.markdown('<div class="section-title">ABDM OPConsultRecord Document Bundle Synthesizer</div>', unsafe_allow_html=True)
    st.write(
        "Under the **Ayushman Bharat Digital Mission (ABDM)**, an outpatient encounter is exchanged as a complete "
        "**FHIR Document Bundle** containing `Composition`, `Patient`, `Practitioner`, and dual-coded `Condition` resources."
    )

    multi_sel = st.multiselect(
        "Select Active Patient Diagnoses to Include in Bundle:",
        options=[r["namaste_code"] for r in engine.records],
        default=["NAM-AYU-001", "NAM-AYU-003"],
        format_func=lambda c: f"{c} - {engine.get_by_namaste_code(c)['traditional_term']} ({engine.get_by_namaste_code(c)['system']})",
    )

    if st.button("📦 Synthesize Complete ABDM Document Bundle", type="primary"):
        cond_list = []
        for c_code in multi_sel:
            r_rec = engine.get_by_namaste_code(c_code)
            cond = FHIRBuilder.create_dual_coded_condition(
                namaste_record=r_rec,
                patient_id=patient_abha,
                patient_name=patient_name,
                doctor_name=doctor_name,
            )
            cond_list.append(cond)

        bundle = FHIRBuilder.create_abdm_document_bundle(
            conditions=cond_list,
            patient_id=patient_abha,
            patient_name=patient_name,
            doctor_name=doctor_name,
            hospital_name=facility_name,
        )

        st.success(f"✅ Generated ABDM Document Bundle containing {bundle['total']} entries (Composition + Patient + Doctor + {len(cond_list)} Conditions)!")
        
        b1, b2 = st.columns(2)
        with b1:
            st.metric("Total Bundle Entries", bundle["total"])
        with b2:
            st.metric("Bundle Profile", "NRCES OPConsultRecord")

        st.json(bundle)
        st.download_button(
            label="📥 Download Full ABDM Bundle JSON",
            data=json.dumps(bundle, indent=2),
            file_name=f"abdm_bundle_{patient_abha}.json",
            mime="application/json",
            use_container_width=True,
        )

# -------------------------------------------------------------
# TAB 3: Terminology & Symptom Directory
# -------------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="section-title">Multi-Criteria Terminology & Symptom Directory</div>', unsafe_allow_html=True)
    st.write("Search effortlessly across traditional names, Sanskrit terms, cardinal symptoms, or ICD-11 codes.")

    sq1, sq2 = st.columns([3, 1])
    with sq1:
        query_input = st.text_input("Search by disease, symptom, or code (e.g. 'heartburn', 'Amlapitta', 'Asthma', 'Sandhivata'):", "")
    with sq2:
        query_system = st.selectbox("System Scope:", ["All", "Ayurveda", "Unani", "Siddha", "Homeopathy"])

    search_hits = engine.search(
        query=query_input,
        system=None if query_system == "All" else query_system,
        limit=50,
    )

    st.write(f"Matched **{len(search_hits)}** clinical concepts:")

    rows = []
    for hit in search_hits:
        rows.append({
            "NAMASTE Code": hit["namaste_code"],
            "System": hit["system"],
            "Traditional Term": hit["traditional_term"],
            "Symptoms": ", ".join(hit.get("symptoms", [])[:2]) + ("..." if len(hit.get("symptoms", [])) > 2 else ""),
            "ICD-11 Code": hit["icd11_code"],
            "ICD-11 Title": hit["icd11_title"],
            "TM-1 Code": hit.get("icd11_tm1_code", "-"),
            "Equivalence": hit["mapping_equivalence"],
            "Confidence": f"{hit['mapping_confidence'] * 100:.0f}%",
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No matching clinical terms found.")

# -------------------------------------------------------------
# TAB 4: Bidirectional Translator
# -------------------------------------------------------------
with tabs[3]:
    st.markdown('<div class="section-title">Bidirectional Terminology Translation Service</div>', unsafe_allow_html=True)
    st.write("Instant automated mapping from NAMASTE to WHO ICD-11, or reverse lookup from ICD-11 into AYUSH.")

    t_mode = st.radio("Translation Flow:", ["NAMASTE → WHO ICD-11", "WHO ICD-11 → NAMASTE"], horizontal=True)

    if t_mode.startswith("NAMASTE"):
        in_namaste = st.text_input("Enter NAMASTE Code (e.g., NAM-AYU-001, NAM-AYU-003, NAM-UNA-001):", value="NAM-AYU-001")
        if st.button("Translate NAMASTE Code"):
            res = engine.translate(code=in_namaste, source_type="namaste")
            if res.get("status") == "success":
                st.success("✅ Translation Found!")
                st.markdown(
                    f"""
                    <div class="clinical-card">
                        <h4>{res['source_term']} ({res['ayush_system']}) ➔ {res['target_title']}</h4>
                        <p><b>Target ICD-11 MMS Code:</b> <code>{res['target_code']}</code></p>
                        <p><b>Target ICD-11 TM-1 Code:</b> <code>{res.get('target_tm1_code', 'N/A')}</code></p>
                        <p><b>Semantic Equivalence:</b> <code>{res['equivalence']}</code> | <b>Confidence:</b> <code>{res['confidence']*100:.1f}%</code></p>
                        <p><b>Clinical Description:</b> {res['clinical_description']}</p>
                        <p><b>Mapping Rationale:</b> {res.get('clinical_rationale')}</p>
                        <p><b>WHO Entity URI:</b> <a href="{res['target_uri']}" target="_blank">{res['target_uri']}</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.error(res.get("message"))
    else:
        in_icd = st.text_input("Enter WHO ICD-11 Code (e.g., 5A11, CA23, DA42, FA00):", value="5A11")
        if st.button("Translate ICD-11 Code"):
            res = engine.translate(code=in_icd, source_type="icd11")
            if res.get("status") == "success":
                st.success(f"✅ Found {res['mappings_count']} corresponding NAMASTE diagnoses for ICD-11 '{res['source_code']}':")
                for m in res["mappings"]:
                    st.markdown(
                        f"""
                        <div class="clinical-card">
                            <h4>🌿 {m['target_term']} (<code>{m['target_code']}</code>)</h4>
                            <p><b>System:</b> {m['ayush_system']} | <b>TM-1 Code:</b> <code>{m.get('tm1_code', '-')}</code></p>
                            <p><b>Equivalence:</b> <code>{m['equivalence']}</code> | <b>Confidence:</b> <code>{m['confidence']*100:.1f}%</code></p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.error(res.get("message"))

# -------------------------------------------------------------
# TAB 5: FHIR Standards Inspector
# -------------------------------------------------------------
with tabs[4]:
    st.markdown('<div class="section-title">HL7 FHIR R4 Standards Specifications</div>', unsafe_allow_html=True)
    st.write("Inspect national-scale FHIR `ConceptMap` and `CodeSystem` entities.")

    choice = st.radio("Resource Type:", ["ConceptMap (NAMASTE to ICD-11)", "CodeSystem (NAMASTE)"], horizontal=True)

    if choice.startswith("ConceptMap"):
        cmap = FHIRBuilder.create_concept_map(engine.records)
        st.caption(f"Resource: ConceptMap | Version: {cmap['version']} | Mapped Elements: {len(cmap['group'][0]['element'])}")
        st.json(cmap)
        st.download_button("📥 Download ConceptMap JSON", json.dumps(cmap, indent=2), "fhir_conceptmap_namaste_icd11.json", "application/json")
    else:
        csys = FHIRBuilder.create_code_system(engine.records)
        st.caption(f"Resource: CodeSystem | Total Concepts: {csys['count']}")
        st.json(csys)
        st.download_button("📥 Download CodeSystem JSON", json.dumps(csys, indent=2), "fhir_codesystem_namaste.json", "application/json")

# -------------------------------------------------------------
# TAB 6: ISO 22600 Audit & Security
# -------------------------------------------------------------
with tabs[5]:
    st.markdown('<div class="section-title">ISO 22600 Audit Trail & Consent Management Simulator</div>', unsafe_allow_html=True)
    st.write(
        "Demonstrating compliance with **ISO 22600 Privilege Management and Access Control** & **ABDM Consent Manager**. "
        "Every clinical query, translation, and export is cryptographically logged."
    )

    st.markdown(
        """
        <div class="clinical-card">
            <h4>🔐 Security & Compliance Stack</h4>
            <ul>
                <li><b>ISO 22600:</b> Role-based access control and privilege verification for practitioner credentials.</li>
                <li><b>ABHA Consent Manager:</b> Validates patient data sharing consent artifacts before dual-coded bundles are uploaded.</li>
                <li><b>OAuth 2.0 / JWT:</b> Standardized token-based authentication for external hospital EMR integrations.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sample_logs = [
        {"Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "Event": "FHIR Condition Created", "User": doctor_name, "ABHA Context": patient_abha, "Status": "SUCCESS (200)"},
        {"Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "Event": "ConceptMap Translation", "User": "EMR-Service-Worker", "ABHA Context": "System-wide", "Status": "SUCCESS (200)"},
        {"Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "Event": "Consent Verification", "User": "ABDM-Gateway", "ABHA Context": patient_abha, "Status": "AUTHORIZED (ISO 22600)"},
    ]
    st.table(pd.DataFrame(sample_logs))

# -------------------------------------------------------------
# TAB 7: SIH Project Blueprint
# -------------------------------------------------------------
with tabs[6]:
    st.markdown('<div class="section-title">Smart India Hackathon 2025 · Project Blueprint</div>', unsafe_allow_html=True)
    st.markdown(
        """
        ### 🎯 Problem Statement
        In India, AYUSH systems (*Ayurveda, Yoga & Naturopathy, Unani, Siddha, Homeopathy*) serve hundreds of millions of citizens. 
        However:
        - **NAMASTE** codes are not recognized by global health systems, international researchers, or global insurers.
        - **WHO ICD-11** lacks out-of-the-box alignment with AYUSH terminology in Indian EMRs.
        - **Impact:** Delayed insurance claim settlements, fragmented public health metrics, and clinical documentation barriers.

        ### 💡 Our Proposed Solution
        A **FHIR-Based Dual Coding Microservice** that:
        1. Ingests traditional diagnoses through a clinician portal.
        2. Resolves dual coding across **NAMASTE**, **WHO ICD-11 MMS**, and **WHO ICD-11 Chapter 26 (Traditional Medicine Module 1)**.
        3. Emits validated **HL7® FHIR® R4 Condition & Document Bundle** resources compliant with **EHR Standards of India (2016)** and **ABDM (NRCES)**.
        4. Provides REST APIs for easy plug-and-play into existing EMRs (*Bahmni, e-Hospital, Practo, etc.*).

        ---
        ### 👥 Hackathon Team Credits (Assam Down Town University)
        - **MD Arif Ul Islam**
        - **MD Samiur Rahman Tanim**
        - **Atikur Rahman**
        - **Farhan Masud**
        - **S M Zafor Abbasi**
        - **Soudamoni Pandit**

        *Milestone: Advanced to Round 2 in Smart India Hackathon 2025.*

        ---
        > **Disclaimer:** This software is an open-source research and educational prototype developed for Smart India Hackathon 2025. 
        > Clinical mappings are curated for technical demonstration and should be reviewed by certified medical terminologists for live production deployment.
        """
    )
