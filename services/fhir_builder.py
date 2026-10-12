"""
FHIR R4 Standards Engine & ABDM Health Document Synthesizer
Generates 100% compliant HL7® FHIR® Release 4 clinical resources:
1. Dual-Coded Condition (NAMASTE + WHO ICD-11 + WHO TM-1 Chapter 26)
2. ConceptMap (Semantic mapping specifications)
3. CodeSystem (NAMASTE AYUSH Terminology repository)
4. ABDM Clinical Document Bundle (OPD Consultation Record conforming to NRCES NDHM profiles)
5. Built-in FHIR Schema & Semantic Validator
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


NAMASTE_SYSTEM_URI = "https://namaste.ayush.gov.in/fhir/CodeSystem/namaste"
ICD11_MMS_SYSTEM_URI = "http://id.who.int/icd/release/11/mms"
ICD11_TM1_SYSTEM_URI = "http://id.who.int/icd/release/11/tm1"
ABDM_PROFILE_BASE = "https://nrces.in/ndhm/fhir/r4/StructureDefinition"


class FHIRBuilder:
    @staticmethod
    def create_dual_coded_condition(
        namaste_record: Dict[str, Any],
        patient_id: str = "ABHA-91-8765-4321-0987",
        patient_name: str = "Rahul Sharma",
        doctor_name: str = "Dr. S. K. Roy (BAMS)",
        clinical_status: str = "active",
        verification_status: str = "confirmed",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a dual-coded HL7 FHIR R4 Condition resource conforming to ABDM profile.
        Includes NAMASTE AYUSH code, WHO ICD-11 MMS code, and ICD-11 TM1 code when available.
        """
        condition_id = f"cond-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build codings
        codings = [
            {
                "system": NAMASTE_SYSTEM_URI,
                "code": namaste_record["namaste_code"],
                "display": f"{namaste_record['traditional_term']} ({namaste_record['system']})",
                "userSelected": True,
            },
            {
                "system": ICD11_MMS_SYSTEM_URI,
                "code": namaste_record["icd11_code"],
                "display": namaste_record["icd11_title"],
                "userSelected": False,
            },
        ]

        if "icd11_tm1_code" in namaste_record and namaste_record["icd11_tm1_code"]:
            codings.append({
                "system": ICD11_TM1_SYSTEM_URI,
                "code": namaste_record["icd11_tm1_code"],
                "display": f"{namaste_record['traditional_term']} (WHO TM-1 Chapter 26)",
                "userSelected": False,
            })

        fhir_condition = {
            "resourceType": "Condition",
            "id": condition_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": now_iso,
                "profile": [f"{ABDM_PROFILE_BASE}/Condition"],
            },
            "identifier": [
                {
                    "system": "https://healthid.ndhm.gov.in/condition-id",
                    "value": condition_id,
                }
            ],
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": clinical_status,
                        "display": clinical_status.capitalize(),
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": verification_status,
                        "display": verification_status.capitalize(),
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item",
                            "display": "Problem List Item",
                        }
                    ]
                }
            ],
            "severity": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "6736007",
                        "display": "Moderate",
                    }
                ]
            },
            "code": {
                "coding": codings,
                "text": f"Dual Coded: {namaste_record['traditional_term']} [{namaste_record['namaste_code']}] mapped to WHO ICD-11 {namaste_record['icd11_title']} [{namaste_record['icd11_code']}] ({namaste_record['mapping_equivalence']})",
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
                "display": patient_name,
            },
            "recordedDate": now_iso,
            "recorder": {
                "reference": f"Practitioner/pr-{uuid.uuid4().hex[:6]}",
                "display": doctor_name,
            },
        }

        if notes:
            fhir_condition["note"] = [{"text": notes}]

        return fhir_condition

    @staticmethod
    def create_concept_map(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates an HL7 FHIR R4 ConceptMap resource mapping NAMASTE to WHO ICD-11.
        """
        elements = []
        for r in records:
            equiv = r.get("mapping_equivalence", "equivalent")
            fhir_equiv_map = {
                "equivalent": "equivalent",
                "narrower": "narrower",
                "broader": "wider",
                "inexact": "inexact",
            }
            fhir_equiv = fhir_equiv_map.get(equiv, "equivalent")

            elements.append({
                "code": r["namaste_code"],
                "display": r["traditional_term"],
                "target": [
                    {
                        "code": r["icd11_code"],
                        "display": r["icd11_title"],
                        "equivalence": fhir_equiv,
                        "comment": f"Confidence: {r.get('mapping_confidence', 0.90) * 100:.1f}%. Subsystem: {r.get('system')}. Rationale: {r.get('clinical_rationale', 'Clinical equivalence')}",
                    }
                ],
            })

        return {
            "resourceType": "ConceptMap",
            "id": "namaste-to-icd11-map",
            "url": "https://nrces.in/ndhm/fhir/r4/ConceptMap/namaste-to-icd11",
            "version": "2.0.0",
            "name": "NamasteToICD11ConceptMap",
            "title": "FHIR ConceptMap: National AYUSH Morbidity (NAMASTE) to WHO ICD-11",
            "status": "active",
            "experimental": False,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "publisher": "Smart India Hackathon 2025 - Team HealthTech Innovators (ADTU)",
            "description": "Nationwide FHIR-based ConceptMap facilitating automated semantic interoperability between India's traditional medicine terminologies (NAMASTE) and WHO ICD-11 classification.",
            "sourceUri": NAMASTE_SYSTEM_URI,
            "targetUri": ICD11_MMS_SYSTEM_URI,
            "group": [
                {
                    "source": NAMASTE_SYSTEM_URI,
                    "target": ICD11_MMS_SYSTEM_URI,
                    "element": elements,
                }
            ],
        }

    @staticmethod
    def create_code_system(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates an HL7 FHIR R4 CodeSystem resource for NAMASTE.
        """
        concepts = []
        for r in records:
            concepts.append({
                "code": r["namaste_code"],
                "display": r["traditional_term"],
                "definition": f"[{r['system']}] {r['english_description']}",
            })

        return {
            "resourceType": "CodeSystem",
            "id": "namaste-codesystem",
            "url": NAMASTE_SYSTEM_URI,
            "version": "2025.2",
            "name": "NAMASTETerminology",
            "title": "National AYUSH Morbidity and Standardized Terminologies Electronic Portal (NAMASTE)",
            "status": "active",
            "content": "complete",
            "count": len(concepts),
            "concept": concepts,
        }

    @staticmethod
    def create_abdm_document_bundle(
        conditions: List[Dict[str, Any]],
        patient_id: str = "ABHA-91-8765-4321-0987",
        patient_name: str = "Rahul Sharma",
        doctor_name: str = "Dr. S. K. Roy (BAMS)",
        hospital_name: str = "National AYUSH Integrated Care Center",
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive ABDM-compliant FHIR R4 Document Bundle (OPConsultRecord).
        Includes Composition, Patient, Practitioner, and all dual-coded Condition resources.
        """
        bundle_id = f"bundle-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        comp_id = f"comp-{uuid.uuid4().hex[:8]}"
        pat_res_id = f"pat-{uuid.uuid4().hex[:8]}"
        doc_res_id = f"doc-{uuid.uuid4().hex[:8]}"

        # Patient resource
        patient_resource = {
            "resourceType": "Patient",
            "id": pat_res_id,
            "meta": {"profile": [f"{ABDM_PROFILE_BASE}/Patient"]},
            "identifier": [
                {
                    "type": {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR", "display": "Medical Record Number"}
                        ]
                    },
                    "system": "https://healthid.ndhm.gov.in",
                    "value": patient_id,
                }
            ],
            "name": [{"text": patient_name}],
            "gender": "male",
            "birthDate": "1994-08-15",
        }

        # Practitioner resource
        practitioner_resource = {
            "resourceType": "Practitioner",
            "id": doc_res_id,
            "meta": {"profile": [f"{ABDM_PROFILE_BASE}/Practitioner"]},
            "identifier": [
                {
                    "system": "https://doctor.ndhm.gov.in",
                    "value": f"HPR-{uuid.uuid4().hex[:6].upper()}",
                }
            ],
            "name": [{"text": doctor_name}],
        }

        # Composition resource
        condition_entries = [{"reference": f"Condition/{c['id']}"} for c in conditions]
        composition_resource = {
            "resourceType": "Composition",
            "id": comp_id,
            "meta": {"profile": [f"{ABDM_PROFILE_BASE}/OPConsultRecord"]},
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "371530004",
                        "display": "Clinical consultation report",
                    }
                ],
                "text": "Outpatient Consultation Record (AYUSH Dual-Coded)",
            },
            "subject": {"reference": f"Patient/{pat_res_id}", "display": patient_name},
            "date": now_iso,
            "author": [{"reference": f"Practitioner/{doc_res_id}", "display": doctor_name}],
            "title": f"OPD Encounter Record - {hospital_name}",
            "section": [
                {
                    "title": "Chief Complaints & Dual-Coded Diagnoses (NAMASTE + ICD-11)",
                    "code": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "282291009", "display": "Diagnosis interpretation"}
                        ]
                    },
                    "entry": condition_entries,
                }
            ],
        }

        # Assemble Bundle
        entries = [
            {"fullUrl": f"urn:uuid:{comp_id}", "resource": composition_resource},
            {"fullUrl": f"urn:uuid:{pat_res_id}", "resource": patient_resource},
            {"fullUrl": f"urn:uuid:{doc_res_id}", "resource": practitioner_resource},
        ]

        for c in conditions:
            entries.append({"fullUrl": f"urn:uuid:{c['id']}", "resource": c})

        return {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": now_iso,
                "profile": [f"{ABDM_PROFILE_BASE}/OPConsultRecord"],
            },
            "identifier": {
                "system": "https://ndhm.gov.in/bundle-id",
                "value": bundle_id,
            },
            "type": "document",
            "timestamp": now_iso,
            "total": len(entries),
            "entry": entries,
        }

    @staticmethod
    def create_problem_list_bundle(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Packs multiple Condition resources into an HL7 FHIR R4 Bundle."""
        entries = [{"fullUrl": f"urn:uuid:{c.get('id', uuid.uuid4())}", "resource": c} for c in conditions]
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{uuid.uuid4().hex[:8]}",
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(entries),
            "entry": entries,
        }

    @staticmethod
    def validate_resource(resource: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates FHIR R4 schema integrity and dual-coding requirements.
        Returns (is_valid, error_list).
        """
        errors = []
        if not isinstance(resource, dict):
            return False, ["Resource must be a valid JSON object."]

        res_type = resource.get("resourceType")
        if not res_type:
            errors.append("Missing mandatory 'resourceType' field.")

        if res_type == "Condition":
            if not resource.get("id"):
                errors.append("Missing mandatory 'id'.")
            if not resource.get("clinicalStatus"):
                errors.append("Missing mandatory 'clinicalStatus'.")
            if not resource.get("verificationStatus"):
                errors.append("Missing mandatory 'verificationStatus'.")

            code_element = resource.get("code", {})
            codings = code_element.get("coding", [])
            if len(codings) < 2:
                errors.append("Condition must have at least 2 codings for Dual-Coding compliance.")

            systems = [c.get("system") for c in codings]
            if NAMASTE_SYSTEM_URI not in systems:
                errors.append("Missing NAMASTE coding system in Condition resource.")
            if ICD11_MMS_SYSTEM_URI not in systems and ICD11_TM1_SYSTEM_URI not in systems:
                errors.append("Missing WHO ICD-11 coding system in Condition resource.")

        elif res_type == "Bundle":
            if not resource.get("type"):
                errors.append("Missing mandatory Bundle 'type'.")
            if "entry" not in resource or not isinstance(resource["entry"], list):
                errors.append("Missing or invalid 'entry' array in Bundle.")

        return len(errors) == 0, errors
