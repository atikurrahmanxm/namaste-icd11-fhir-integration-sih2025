"""
Comprehensive Test Suite for FHIR Dual Coding Microservice
Validates mapping engine, symptom search, FHIR R4 schema generation,
ABDM Document Bundle synthesizer, FHIR validator, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder
from api import app


def test_mapping_engine_load():
    engine = MappingEngine()
    assert len(engine.records) >= 15, "Engine should load enriched records"
    stats = engine.get_summary_stats()
    assert stats["total_records"] >= 15
    assert "Ayurveda" in stats["systems"]
    assert "Unani" in stats["systems"]
    assert "Siddha" in stats["systems"]
    assert "Homeopathy" in stats["systems"]
    assert stats["average_confidence_score"] > 80.0


def test_mapping_engine_symptom_search():
    engine = MappingEngine()
    # Search by symptom 'heartburn' or 'acid'
    res_symptom = engine.search(query="heartburn")
    assert len(res_symptom) > 0
    assert any("Amlapitta" in r["traditional_term"] for r in res_symptom)

    # Search by joint symptom
    res_joint = engine.search(query="Joint pain")
    assert len(res_joint) > 0


def test_bidirectional_translation_with_tm1():
    engine = MappingEngine()
    # NAMASTE -> ICD-11
    tr_nam = engine.translate("NAM-AYU-001", source_type="namaste")
    assert tr_nam["status"] == "success"
    assert tr_nam["target_code"] == "DA42"
    assert "target_tm1_code" in tr_nam

    # ICD-11 -> NAMASTE
    tr_icd = engine.translate("5A11", source_type="icd11")
    assert tr_icd["status"] == "success"
    assert tr_icd["mappings_count"] >= 1


def test_fhir_builder_condition_and_validation():
    engine = MappingEngine()
    rec = engine.get_by_namaste_code("NAM-AYU-001")
    cond = FHIRBuilder.create_dual_coded_condition(rec)

    assert cond["resourceType"] == "Condition"
    assert "coding" in cond["code"]
    assert len(cond["code"]["coding"]) >= 2

    # Check validator
    is_valid, errors = FHIRBuilder.validate_resource(cond)
    assert is_valid is True
    assert len(errors) == 0


def test_fhir_builder_abdm_bundle():
    engine = MappingEngine()
    rec1 = engine.get_by_namaste_code("NAM-AYU-001")
    rec2 = engine.get_by_namaste_code("NAM-AYU-003")
    cond1 = FHIRBuilder.create_dual_coded_condition(rec1)
    cond2 = FHIRBuilder.create_dual_coded_condition(rec2)

    bundle = FHIRBuilder.create_abdm_document_bundle([cond1, cond2])
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert bundle["total"] == 5  # Composition + Patient + Practitioner + 2 Conditions

    is_valid, errors = FHIRBuilder.validate_resource(bundle)
    assert is_valid is True


def test_fastapi_endpoints_complete():
    client = TestClient(app)

    # Root & Health
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "online"

    r_health = client.get("/health")
    assert r_health.status_code == 200

    # Search & Stats
    r_search = client.get("/api/search?q=Asthma")
    assert r_search.status_code == 200
    assert r_search.json()["count"] >= 1

    r_stats = client.get("/api/stats")
    assert r_stats.status_code == 200

    # Translate
    r_trans = client.get("/api/translate?code=NAM-AYU-001&source=namaste")
    assert r_trans.status_code == 200

    # POST Condition
    payload = {
        "namaste_code": "NAM-AYU-001",
        "patient_id": "ABHA-91-8765-4321-0987",
        "patient_name": "Test Patient",
        "doctor_name": "Dr. Test",
        "clinical_status": "active",
        "verification_status": "confirmed",
        "notes": "Test notes",
    }
    r_cond = client.post("/api/fhir/condition", json=payload)
    assert r_cond.status_code == 200
    cond_json = r_cond.json()
    assert cond_json["resourceType"] == "Condition"

    # POST Document Bundle
    doc_payload = {
        "namaste_codes": ["NAM-AYU-001", "NAM-AYU-003"],
        "patient_id": "ABHA-91-8765-4321-0987",
        "patient_name": "Test Patient",
        "doctor_name": "Dr. Test",
        "hospital_name": "Test Hospital",
    }
    r_bundle = client.post("/api/fhir/document-bundle", json=doc_payload)
    assert r_bundle.status_code == 200
    assert r_bundle.json()["resourceType"] == "Bundle"

    # POST Validate
    r_val = client.post("/api/fhir/validate", json=cond_json)
    assert r_val.status_code == 200
    assert r_val.json()["is_valid"] is True

    # Audit logs
    r_audit = client.get("/api/audit-logs")
    assert r_audit.status_code == 200
    assert "total_events" in r_audit.json()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
