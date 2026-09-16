from typing import Dict, List, Optional
from ml.src.incident.schemas import IncidentCandidate
from app.db.base_repository import BaseIncidentRepository

class InMemoryIncidentRepository(BaseIncidentRepository):
    """
    TEMPORARY In-Memory State for Phase 2 Integration Testing.
    This is NOT a database and state will be lost on restart.
    Will be replaced by Supabase in Phase 3.
    """
    def __init__(self):
        self._incidents: Dict[str, IncidentCandidate] = {}
        self._reports: Dict[str, Any] = {}

    def save(self, incident: IncidentCandidate) -> None:
        self._incidents[incident.incident_id] = incident
        
    def save_report(self, report: Any) -> None:
        self._reports[report.report_id] = report

    def get(self, incident_id: str) -> Optional[IncidentCandidate]:
        return self._incidents.get(incident_id)

    def get_all(self) -> List[IncidentCandidate]:
        return list(self._incidents.values())

incident_repo = InMemoryIncidentRepository()
