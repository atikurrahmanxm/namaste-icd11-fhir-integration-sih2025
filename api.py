"""
FastAPI Microservice for FHIR-Based Dual Coding
Endpoints for searching, translating, generating, and validating FHIR R4 resources.
Compliant with EHR Standards of India (2016) and ABDM (NRCES) profiles.
"""

import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder

app = FastAPI(
    title="FHIR Dual-Coding Microservice (NAMASTE & ICD-11)",
    description="""
    ## Smart India Hackathon 2025 Prototype
    An enterprise-grade healthcare microservice bridging **India's NAMASTE (AYUSH)**
    and **WHO ICD-11** via **HL7® FHIR® Release 4**.
    
    ### Core Capabilities:
    * **Intelligent Autocomplete & Search** across Ayurveda, Unani, Siddha, and Homeopathy.
    * **Bidirectional Terminology Translation** (NAMASTE ↔ WHO ICD-11).
    * **Dual-Coded FHIR R4 Condition Generation** aligned with ABDM (NRCES).
    * **ABDM OPConsultRecord Document Bundle Synthesizer**.
    * **FHIR Resource Semantic Validator**.
    * **ISO 22600 Audit & Consent Tracking Simulator**.
    """,
    version="2.0.0",
    contact={
        "name": "Team HealthTech Innovators (Assam Down Town University)",
        "email": "atikurrahmanxm@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = MappingEngine()
START_TIME = time.time()

# Audit logs store (in-memory for demo / simulation)
AUDIT_LOGS: List[Dict[str, Any]] = []


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi.json"):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "127.0.0.1",
            "iso_22600_consent_status": "authorized",
        }
        AUDIT_LOGS.append(log_entry)
        if len(AUDIT_LOGS) > 100:
            AUDIT_LOGS.pop(0)

    return response


# Pydantic Models
class DualCodingRequest(BaseModel):
    namaste_code: str = Field(..., json_schema_extra={"example": "NAM-AYU-001"}, description="NAMASTE Diagnosis Code")
    patient_id: str = Field("ABHA-91-8765-4321-0987", description="Patient 14-digit ABHA ID")
    patient_name: str = Field("Rahul Sharma", description="Patient Name")
    doctor_name: str = Field("Dr. S. K. Roy (BAMS)", description="Attending Practitioner Name")
    clinical_status: str = Field("active", description="active | recurrence | relapse | remission | resolved")
    verification_status: str = Field("confirmed", description="confirmed | provisional | differential | unconfirmed")
    notes: Optional[str] = Field("Patient reports burning sensation in epigastrium after meals.", description="Clinical Consultation Notes")


class DocumentBundleRequest(BaseModel):
    namaste_codes: List[str] = Field(..., json_schema_extra={"example": ["NAM-AYU-001", "NAM-AYU-003"]}, description="List of NAMASTE diagnosis codes")
    patient_id: str = Field("ABHA-91-8765-4321-0987", description="Patient ABHA ID")
    patient_name: str = Field("Rahul Sharma", description="Patient Name")
    doctor_name: str = Field("Dr. S. K. Roy (BAMS)", description="Attending Practitioner")
    hospital_name: str = Field("National AYUSH Integrated Care Center", description="Hospital / Clinic Facility Name")


@app.get("/", tags=["System Information"])
def root():
    return {
        "service": "FHIR Dual Coding Microservice for NAMASTE & ICD-11",
        "version": "2.0.0",
        "hackathon": "Smart India Hackathon 2025",
        "status": "online",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "docs_url": "/docs",
        "fhir_version": "HL7 FHIR Release 4.0.1",
        "profile": "NRCES India (ABDM Compliant)",
    }


@app.get("/health", tags=["System Information"])
def health_check():
    return {
        "status": "healthy",
        "service": "fhir-dual-coding-microservice",
        "records_loaded": len(engine.records),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/stats", tags=["Terminology Services"])
def get_stats():
    """Returns dataset summary, counts per AYUSH system, and mapping coverage."""
    return engine.get_summary_stats()


@app.get("/api/search", tags=["Terminology Services"])
def search_codes(
    q: str = Query("", description="Search term, symptom, or diagnostic code"),
    system: Optional[str] = Query(None, description="Filter by system: Ayurveda, Unani, Siddha, Homeopathy, or All"),
    limit: int = Query(25, ge=1, le=100),
):
    """Fuzzy and symptom-aware search across NAMASTE and WHO ICD-11 registries."""
    results = engine.search(query=q, system=system, limit=limit)
    return {
        "query": q,
        "system": system or "All",
        "count": len(results),
        "results": results,
    }


@app.get("/api/translate", tags=["Terminology Services"])
def translate_code(
    code: str = Query(..., description="Diagnosis code to translate (e.g. NAM-AYU-001 or 5A11)"),
    source: str = Query("namaste", description="Source vocabulary: 'namaste' or 'icd11'"),
):
    """Bidirectional translation between NAMASTE and WHO ICD-11 with confidence metrics."""
    result = engine.translate(code=code, source_type=source)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@app.post("/api/fhir/condition", tags=["FHIR Resource Generation"])
def generate_fhir_condition(req: DualCodingRequest):
    """Generates an ABDM-compliant dual-coded HL7 FHIR R4 Condition resource."""
    record = engine.get_by_namaste_code(req.namaste_code)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"NAMASTE code '{req.namaste_code}' not found in database.",
        )
    
    fhir_resource = FHIRBuilder.create_dual_coded_condition(
        namaste_record=record,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        doctor_name=req.doctor_name,
        clinical_status=req.clinical_status,
        verification_status=req.verification_status,
        notes=req.notes,
    )
    return fhir_resource


@app.post("/api/fhir/document-bundle", tags=["FHIR Resource Generation"])
def generate_document_bundle(req: DocumentBundleRequest):
    """Generates an ABDM OPConsultRecord Document Bundle containing Composition, Patient, Practitioner, and Conditions."""
    conditions = []
    for code in req.namaste_codes:
        rec = engine.get_by_namaste_code(code)
        if rec:
            cond = FHIRBuilder.create_dual_coded_condition(
                namaste_record=rec,
                patient_id=req.patient_id,
                patient_name=req.patient_name,
                doctor_name=req.doctor_name,
            )
            conditions.append(cond)

    if not conditions:
        raise HTTPException(status_code=400, detail="No valid NAMASTE codes provided.")

    return FHIRBuilder.create_abdm_document_bundle(
        conditions=conditions,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        doctor_name=req.doctor_name,
        hospital_name=req.hospital_name,
    )


@app.post("/api/fhir/validate", tags=["Validation & Compliance"])
def validate_fhir_resource(resource: Dict[str, Any] = Body(...)):
    """Validates an uploaded FHIR R4 resource against ABDM profile requirements and dual-coding integrity."""
    is_valid, errors = FHIRBuilder.validate_resource(resource)
    return {
        "is_valid": is_valid,
        "resource_type": resource.get("resourceType"),
        "errors": errors,
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "compliance_profile": "NRCES NDHM India FHIR R4",
    }


@app.get("/api/fhir/conceptmap", tags=["Standards Specifications"])
def get_fhir_concept_map():
    """Exports full HL7 FHIR R4 ConceptMap specification for nationwide distribution."""
    return FHIRBuilder.create_concept_map(engine.records)


@app.get("/api/fhir/codesystem", tags=["Standards Specifications"])
def get_fhir_code_system():
    """Exports full HL7 FHIR R4 CodeSystem specification for NAMASTE."""
    return FHIRBuilder.create_code_system(engine.records)


@app.get("/api/audit-logs", tags=["Validation & Compliance"])
def get_audit_logs():
    """Returns recent API access and ISO 22600 consent audit logs for SIH demonstration."""
    return {
        "total_events": len(AUDIT_LOGS),
        "standard": "ISO 22600 Privilege Management and Access Control",
        "logs": AUDIT_LOGS[-25:],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
