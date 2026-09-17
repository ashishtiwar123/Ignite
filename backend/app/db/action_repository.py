from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from app.api.schemas.internal import ActionRecord

logger = logging.getLogger(__name__)

class BaseActionRepository(ABC):
    @abstractmethod
    def save(self, action: ActionRecord) -> ActionRecord:
        """Persist or update an action record."""
        pass

    @abstractmethod
    def get(self, action_id: str) -> Optional[ActionRecord]:
        """Fetch an action record by action_id."""
        pass

    @abstractmethod
    def get_by_execution_id(self, execution_id: str) -> Optional[ActionRecord]:
        """Fetch an action record by execution_id."""
        pass

    @abstractmethod
    def get_by_optimization_run(self, optimization_run_id: str) -> List[ActionRecord]:
        """Fetch all action records for an optimization_run_id."""
        pass

    @abstractmethod
    def get_by_approval_id(self, approval_id: str) -> List[ActionRecord]:
        """Fetch action records matching approval_id."""
        pass

    @abstractmethod
    def get_by_incident(self, incident_id: str) -> List[ActionRecord]:
        """Fetch action records matching incident_id."""
        pass


class InMemoryActionRepository(BaseActionRepository):
    def __init__(self):
        self._storage: dict[str, ActionRecord] = {}

    def save(self, action: ActionRecord) -> ActionRecord:
        self._storage[action.action_id] = action
        return action

    def get(self, action_id: str) -> Optional[ActionRecord]:
        return self._storage.get(action_id)

    def get_by_execution_id(self, execution_id: str) -> Optional[ActionRecord]:
        for a in self._storage.values():
            if a.execution_id == execution_id:
                return a
        return None

    def get_by_optimization_run(self, optimization_run_id: str) -> List[ActionRecord]:
        return [a for a in self._storage.values() if a.optimization_run_id == optimization_run_id]

    def get_by_approval_id(self, approval_id: str) -> List[ActionRecord]:
        return [a for a in self._storage.values() if a.approval_id == approval_id]

    def get_by_incident(self, incident_id: str) -> List[ActionRecord]:
        return [a for a in self._storage.values() if a.incident_id == incident_id]
