from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.api.schemas.internal import AssessmentRecord

class BaseAssessmentRepository(ABC):
    """
    Abstract interface for assessment persistence.
    """
    @abstractmethod
    def save(self, assessment: AssessmentRecord) -> None:
        pass

    @abstractmethod
    def get(self, assessment_id: str) -> Optional[AssessmentRecord]:
        pass

    @abstractmethod
    def get_latest_for_incident(self, incident_id: str) -> Optional[AssessmentRecord]:
        pass

    @abstractmethod
    def get_all_for_incident(self, incident_id: str) -> List[AssessmentRecord]:
        pass

class InMemoryAssessmentRepository(BaseAssessmentRepository):
    """
    TEMPORARY In-Memory State for Phase 3 Integration Testing.
    """
    def __init__(self):
        self._assessments: dict[str, AssessmentRecord] = {}

    def save(self, assessment: AssessmentRecord) -> None:
        # Check idempotency: incident_id + idempotency_key
        for existing in self._assessments.values():
            if (existing.incident_id == assessment.incident_id and 
                existing.idempotency_key == assessment.idempotency_key and
                assessment.idempotency_key is not None):
                # Optionally return or throw exception. The requirement says:
                # "The second operation should either return the existing assessment
                # or produce a controlled duplicate/idempotency response."
                # We will silently ignore and act as if it succeeded (idempotent),
                # but update the passed reference or just return without inserting a duplicate.
                return
                
        self._assessments[assessment.assessment_id] = assessment

    def get(self, assessment_id: str) -> Optional[AssessmentRecord]:
        return self._assessments.get(assessment_id)

    def get_latest_for_incident(self, incident_id: str) -> Optional[AssessmentRecord]:
        relevant = [a for a in self._assessments.values() if a.incident_id == incident_id]
        if not relevant:
            return None
        # Sort by assessed_at descending
        relevant.sort(key=lambda a: a.assessed_at, reverse=True)
        return relevant[0]

    def get_all_for_incident(self, incident_id: str) -> List[AssessmentRecord]:
        relevant = [a for a in self._assessments.values() if a.incident_id == incident_id]
        relevant.sort(key=lambda a: a.assessed_at, reverse=True)
        return relevant
