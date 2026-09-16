from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.api.schemas.internal import AllocationRecord

logger = logging.getLogger(__name__)

class BaseAllocationRepository(ABC):
    @abstractmethod
    def save_allocations(self, allocations: List[AllocationRecord]) -> None:
        """Persist a list of allocations."""
        pass
        
    @abstractmethod
    def get_by_incident(self, incident_id: str) -> List[AllocationRecord]:
        """Fetch all allocations related to a specific incident."""
        pass

class InMemoryAllocationRepository(BaseAllocationRepository):
    def __init__(self):
        self._data: List[AllocationRecord] = []
        
    def save_allocations(self, allocations: List[AllocationRecord]) -> None:
        if not allocations:
            return
            
        run_id = allocations[0].optimization_run_id
        
        # Idempotency check: if any allocation exists for this run_id, ignore insertion
        if run_id is not None:
            existing = [a for a in self._data if a.optimization_run_id == run_id]
            if existing:
                logger.info(f"Allocations for run_id {run_id} already exist. Skipping save.")
                return
            
        self._data.extend(allocations)
        
    def get_by_incident(self, incident_id: str) -> List[AllocationRecord]:
        return [a for a in self._data if a.incident_id == incident_id]
