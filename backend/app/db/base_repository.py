from abc import ABC, abstractmethod
from typing import List, Optional, Any
from ml.src.incident.schemas import IncidentCandidate

class BaseIncidentRepository(ABC):
    """
    Abstract interface for incident persistence.
    Allows swapping between InMemory and Supabase implementations without changing services.
    """
    @abstractmethod
    def save(self, incident: IncidentCandidate) -> None:
        pass
        
    @abstractmethod
    def save_report(self, report: Any) -> None:
        pass

    @abstractmethod
    def get(self, incident_id: str) -> Optional[IncidentCandidate]:
        pass

    @abstractmethod
    def get_all(self) -> List[IncidentCandidate]:
        pass
