"""
FastAPI Microservice for FHIR-Based Dual Coding
Endpoints for searching, translating, and generating FHIR R4 resources.
"""

from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder

app = FastAPI(
    title="FHIR Dual-Coding Microservice (NAMASTE & ICD-11)",
    description="A microservice bridging AYUSH (NAMASTE) and WHO ICD-11 medical coding via HL7 FHIR R4.",
    version="1.0.0",
)

# Enable CORS for EMR integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = MappingEngine()


class DualCodingRequest(BaseModel):
    namaste_code: str = Field(..., json_schema_extra={"example": "NAM-AYU-001"}, description="NAMASTE Diagnosis Code")
    patient_id: str = Field("ABHA-91-8765-4321-0987", description="Patient ABHA ID")
    patient_name: str = Field("Rahul Sharma", description="Patient Name")
    doctor_name: str = Field("Dr. S. K. Roy (BAMS)", description="Attending Practitioner")
    clinical_status: str = Field("active", description="active | recurrence | relapse | remission | resolved")
    verification_status: str = Field("confirmed", description="unconfirmed | provisional | differential | confirmed")
    notes: Optional[str] = Field("Patient reports burning sensation after meals for 2 weeks.", description="Clinical Notes")


@app.get("/")
def root():
    return {
        "service": "FHIR Dual Coding Microservice for NAMASTE & ICD-11",
        "version": "1.0.0",
        "hackathon": "Smart India Hackathon 2025",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "fhir-dual-coding-microservice"}


@app.get("/api/stats")
def get_stats():
    return engine.get_summary_stats()


@app.get("/api/search")
def search_codes(
    q: str = Query("", description="Search term or code"),
    system: Optional[str] = Query(None, description="Ayurveda, Unani, Siddha, Homeopathy, or All"),
    limit: int = Query(20, ge=1, le=100),
):
    results = engine.search(query=q, system=system, limit=limit)
    return {
        "query": q,
        "system": system or "All",
        "count": len(results),
        "results": results,
    }


@app.get("/api/translate")
def translate_code(
    code: str = Query(..., description="Diagnosis code to translate"),
    source: str = Query("namaste", description="Source vocabulary: 'namaste' or 'icd11'"),
):
    result = engine.translate(code=code, source_type=source)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@app.post("/api/fhir/condition")
def generate_fhir_condition(req: DualCodingRequest):
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


@app.get("/api/fhir/conceptmap")
def get_fhir_concept_map():
    return FHIRBuilder.create_concept_map(engine.records)


@app.get("/api/fhir/codesystem")
def get_fhir_code_system():
    return FHIRBuilder.create_code_system(engine.records)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
