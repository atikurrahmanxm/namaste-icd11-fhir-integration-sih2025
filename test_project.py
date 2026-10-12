"""
Test Suite for FHIR Dual Coding Microservice
Validates mapping engine, FHIR R4 schema generation, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from services.mapping_engine import MappingEngine
from services.fhir_builder import FHIRBuilder
from api import app


def test_mapping_engine_load():
    engine = MappingEngine()
    assert len(engine.records) > 0, "Engine should load sample records"
    stats = engine.get_summary_stats()
    assert stats["total_records"] >= 20
    assert "Ayurveda" in stats["systems"]
    assert "Unani" in stats["systems"]
    assert "Siddha" in stats["systems"]
    assert "Homeopathy" in stats["systems"]


def test_mapping_engine_search():
    engine = MappingEngine()
    # Search for asthma
    results = engine.search(query="Asthma")
    assert len(results) > 0
    # Search specific code
    code_res = engine.get_by_namaste_code("NAM-AYU-001")
    assert code_res is not None
    assert code_res["traditional_term"] == "Amlapitta"
    assert code_res["icd11_code"] == "DA42"


def test_bidirectional_translation():
    engine = MappingEngine()
    # NAMASTE -> ICD-11
    tr_nam = engine.translate("NAM-AYU-003", source_type="namaste")
    assert tr_nam["status"] == "success"
    assert tr_nam["target_code"] == "5A11"

    # ICD-11 -> NAMASTE
    tr_icd = engine.translate("5A11", source_type="icd11")
    assert tr_icd["status"] == "success"
    assert tr_icd["mappings_count"] >= 1


def test_fhir_builder_condition():
    engine = MappingEngine()
    rec = engine.get_by_namaste_code("NAM-AYU-001")
    cond = FHIRBuilder.create_dual_coded_condition(rec)

    assert cond["resourceType"] == "Condition"
    assert "coding" in cond["code"]
    assert len(cond["code"]["coding"]) == 2

    # Check both coding systems are present
    systems = [c["system"] for c in cond["code"]["coding"]]
    assert "https://namaste.ayush.gov.in/fhir/CodeSystem/namaste" in systems
    assert "http://id.who.int/icd/release/11/mms" in systems


def test_fhir_builder_conceptmap():
    engine = MappingEngine()
    cmap = FHIRBuilder.create_concept_map(engine.records)
    assert cmap["resourceType"] == "ConceptMap"
    assert len(cmap["group"]) > 0
    assert len(cmap["group"][0]["element"]) == len(engine.records)


def test_fastapi_endpoints():
    client = TestClient(app)

    # Root
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "online"

    # Search
    r_search = client.get("/api/search?q=Amlapitta")
    assert r_search.status_code == 200
    assert r_search.json()["count"] >= 1

    # Translate
    r_trans = client.get("/api/translate?code=NAM-AYU-001&source=namaste")
    assert r_trans.status_code == 200
    assert r_trans.json()["target_code"] == "DA42"

    # POST FHIR Condition
    payload = {
        "namaste_code": "NAM-AYU-001",
        "patient_id": "ABHA-001",
        "patient_name": "Test Patient",
        "doctor_name": "Dr. Test",
        "clinical_status": "active",
        "verification_status": "confirmed",
        "notes": "Test notes",
    }
    r_cond = client.post("/api/fhir/condition", json=payload)
    assert r_cond.status_code == 200
    assert r_cond.json()["resourceType"] == "Condition"

    # ConceptMap
    r_cmap = client.get("/api/fhir/conceptmap")
    assert r_cmap.status_code == 200
    assert r_cmap.json()["resourceType"] == "ConceptMap"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
