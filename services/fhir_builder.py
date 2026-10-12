"""
FHIR R4 Resource Builder
Generates valid HL7 FHIR Release 4 resources for:
1. CodeSystem (NAMASTE AYUSH Terminology)
2. ConceptMap (NAMASTE -> WHO ICD-11 mapping)
3. Condition (Dual-coded clinical diagnostic entry conforming to ABDM / EHR Standards of India)
4. Bundle (ProblemList representation)
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


NAMASTE_SYSTEM_URI = "https://namaste.ayush.gov.in/fhir/CodeSystem/namaste"
ICD11_SYSTEM_URI = "http://id.who.int/icd/release/11/mms"
ABDM_CONDITION_PROFILE = "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Condition"


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
        Creates a valid HL7 FHIR R4 Condition resource featuring dual coding
        (NAMASTE AYUSH + WHO ICD-11).
        """
        condition_id = f"cond-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        fhir_condition = {
            "resourceType": "Condition",
            "id": condition_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": now_iso,
                "profile": [ABDM_CONDITION_PROFILE],
            },
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
            "code": {
                "coding": [
                    {
                        "system": NAMASTE_SYSTEM_URI,
                        "code": namaste_record["namaste_code"],
                        "display": f"{namaste_record['traditional_term']} ({namaste_record['system']})",
                        "userSelected": True,
                    },
                    {
                        "system": ICD11_SYSTEM_URI,
                        "code": namaste_record["icd11_code"],
                        "display": namaste_record["icd11_title"],
                        "userSelected": False,
                    },
                ],
                "text": f"Dual Coded: {namaste_record['traditional_term']} [{namaste_record['namaste_code']}] mapped to WHO ICD-11 {namaste_record['icd11_title']} [{namaste_record['icd11_code']}] ({namaste_record['mapping_equivalence']})",
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
                "display": patient_name,
            },
            "recordedDate": now_iso,
            "recorder": {
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
            # Map equivalence terms to FHIR R4 ConceptMapEquivalence enum
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
                        "comment": f"Confidence: {r.get('mapping_confidence', 0.90) * 100:.1f}%. Subsystem: {r.get('system')}",
                    }
                ],
            })

        return {
            "resourceType": "ConceptMap",
            "id": "namaste-to-icd11-map",
            "url": "https://nrces.in/ndhm/fhir/r4/ConceptMap/namaste-to-icd11",
            "version": "1.0.0",
            "name": "NamasteToICD11ConceptMap",
            "title": "FHIR ConceptMap: National AYUSH Morbidity (NAMASTE) to WHO ICD-11",
            "status": "active",
            "experimental": True,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "publisher": "Smart India Hackathon 2025 - Team HealthTech Innovators",
            "description": "FHIR-based ConceptMap facilitating semantic interoperability between India's traditional medicine terminologies and WHO ICD-11 classification.",
            "sourceUri": NAMASTE_SYSTEM_URI,
            "targetUri": ICD11_SYSTEM_URI,
            "group": [
                {
                    "source": NAMASTE_SYSTEM_URI,
                    "target": ICD11_SYSTEM_URI,
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
            "version": "2025.1",
            "name": "NAMASTETerminology",
            "title": "National AYUSH Morbidity and Standardized Terminologies Electronic Portal (NAMASTE)",
            "status": "active",
            "content": "complete",
            "count": len(concepts),
            "concept": concepts,
        }

    @staticmethod
    def create_problem_list_bundle(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Packs multiple Condition resources into an HL7 FHIR R4 Bundle.
        """
        entries = []
        for c in conditions:
            entries.append({
                "fullUrl": f"urn:uuid:{c.get('id', uuid.uuid4())}",
                "resource": c,
            })

        return {
            "resourceType": "Bundle",
            "id": f"bundle-{uuid.uuid4().hex[:8]}",
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(entries),
            "entry": entries,
        }
