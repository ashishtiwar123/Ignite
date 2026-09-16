from typing import List, Dict, Any
from app.db.needs_repository import BaseNeedsRepository
from app.api.schemas.internal import NeedRecord

class NeedsService:
    def __init__(self, needs_repo: BaseNeedsRepository):
        self.needs_repo = needs_repo

    def save_needs_from_assessment(
        self, 
        incident_id: str, 
        assessment_id: str, 
        raw_needs: List[Dict[str, Any]]
    ) -> List[NeedRecord]:
        """
        Maps the raw output from the ML Needs Engine to structured database records and saves them.
        """
        records = []
        for raw in raw_needs:
            record = NeedRecord(
                incident_id=incident_id,
                assessment_id=assessment_id,
                resource_type=raw.get("resource_type", "UNKNOWN"),
                category=raw.get("category"),
                quantity=raw.get("quantity"),
                unit=raw.get("unit"),
                urgency=raw.get("urgency_category"),
                status=raw.get("status"),
                time_window=raw.get("time_window"),
                rule_id=raw.get("rule_id"),
                policy_version=raw.get("policy_version"),
                calculation_basis=raw.get("calculation_basis"),
                provenance=raw.get("provenance"),
                explanation=raw.get("explanation")
            )
            records.append(record)
            
        self.needs_repo.save_all(records)
        return records

    def get_needs_for_incident(self, incident_id: str) -> List[NeedRecord]:
        return self.needs_repo.get_by_incident(incident_id)
