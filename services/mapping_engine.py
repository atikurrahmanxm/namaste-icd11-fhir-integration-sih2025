"""
Dual Coding Mapping Engine
Provides fuzzy search, lookup, and bidirectional translation
between NAMASTE (AYUSH) terminology and WHO ICD-11 classification.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "namaste_data.json"


class MappingEngine:
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or DATA_FILE
        self.records: List[Dict[str, Any]] = []
        self._by_namaste: Dict[str, Dict[str, Any]] = {}
        self._by_icd11: Dict[str, List[Dict[str, Any]]] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load NAMASTE and ICD-11 data from json file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found at {self.data_path}")
        
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.records = json.load(f)

        self._by_namaste = {r["namaste_code"].upper(): r for r in self.records}
        self._by_icd11 = {}
        for r in self.records:
            icd = r["icd11_code"].upper()
            if icd not in self._by_icd11:
                self._by_icd11[icd] = []
            self._by_icd11[icd].append(r)

    def get_by_namaste_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Lookup single record by NAMASTE code."""
        return self._by_namaste.get(code.strip().upper())

    def get_by_icd11_code(self, code: str) -> List[Dict[str, Any]]:
        """Lookup records mapped to an ICD-11 code."""
        return self._by_icd11.get(code.strip().upper(), [])

    def search(
        self,
        query: str = "",
        system: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search entries across traditional term, English clinical description,
        category, NAMASTE code, and ICD-11 title/code.
        """
        query = query.strip()
        filtered = self.records

        if system and system.lower() != "all":
            filtered = [r for r in filtered if r["system"].lower() == system.lower()]

        if not query:
            return filtered[:limit]

        query_lower = query.lower()
        scored_results = []

        for r in filtered:
            # Direct match check
            searchable_text = f"{r['namaste_code']} {r['traditional_term']} {r['english_description']} {r['category']} {r['icd11_code']} {r['icd11_title']}".lower()

            if HAS_RAPIDFUZZ:
                # Fuzzy score computation
                ratio_name = fuzz.partial_ratio(query_lower, r["traditional_term"].lower())
                ratio_desc = fuzz.partial_ratio(query_lower, r["english_description"].lower())
                ratio_code = 100 if query_lower in r["namaste_code"].lower() or query_lower in r["icd11_code"].lower() else 0
                ratio_icd = fuzz.partial_ratio(query_lower, r["icd11_title"].lower())
                score = max(ratio_name, ratio_desc, ratio_code, ratio_icd)
                if score >= 45 or query_lower in searchable_text:
                    scored_results.append((score, r))
            else:
                if query_lower in searchable_text:
                    score = 100 if query_lower in r["traditional_term"].lower() else 70
                    scored_results.append((score, r))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_results[:limit]]

    def translate(self, code: str, source_type: str = "namaste") -> Dict[str, Any]:
        """
        Bidirectional translation service.
        source_type: 'namaste' or 'icd11'
        """
        code = code.strip().upper()
        if source_type.lower() == "namaste":
            entry = self.get_by_namaste_code(code)
            if not entry:
                return {
                    "status": "error",
                    "message": f"NAMASTE code '{code}' not found in database.",
                    "code": code,
                    "source": "namaste",
                }
            return {
                "status": "success",
                "source_system": "NAMASTE",
                "source_code": entry["namaste_code"],
                "source_term": entry["traditional_term"],
                "ayush_system": entry["system"],
                "target_system": "ICD-11",
                "target_code": entry["icd11_code"],
                "target_title": entry["icd11_title"],
                "target_uri": entry["icd11_uri"],
                "equivalence": entry["mapping_equivalence"],
                "confidence": entry["mapping_confidence"],
                "clinical_description": entry["english_description"],
            }
        elif source_type.lower() == "icd11":
            entries = self.get_by_icd11_code(code)
            if not entries:
                return {
                    "status": "error",
                    "message": f"ICD-11 code '{code}' has no mapped NAMASTE entries.",
                    "code": code,
                    "source": "icd11",
                }
            return {
                "status": "success",
                "source_system": "ICD-11",
                "source_code": code,
                "mappings_count": len(entries),
                "mappings": [
                    {
                        "target_system": "NAMASTE",
                        "target_code": e["namaste_code"],
                        "target_term": e["traditional_term"],
                        "ayush_system": e["system"],
                        "equivalence": e["mapping_equivalence"],
                        "confidence": e["mapping_confidence"],
                    }
                    for e in entries
                ],
            }
        else:
            return {
                "status": "error",
                "message": f"Unsupported source_type '{source_type}'. Use 'namaste' or 'icd11'.",
            }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Return dataset distribution and summary statistics."""
        system_counts: Dict[str, int] = {}
        for r in self.records:
            s = r["system"]
            system_counts[s] = system_counts.get(s, 0) + 1

        return {
            "total_records": len(self.records),
            "systems": system_counts,
            "mapping_coverage_percentage": 100.0,
            "standards_supported": ["FHIR R4", "NAMASTE AYUSH", "WHO ICD-11 MMS"],
        }
