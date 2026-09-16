from abc import ABC, abstractmethod
from typing import List, Optional
from app.api.schemas.internal import ResourceRecord
from datetime import datetime, timezone

class BaseResourceRepository(ABC):
    @abstractmethod
    def upsert(self, resource: ResourceRecord) -> None:
        """
        Upserts inventory. Uniqueness is based on (location_id, resource_type, category).
        """
        pass

    @abstractmethod
    def get_all(self) -> List[ResourceRecord]:
        """
        Retrieves all available resources.
        """
        pass

    @abstractmethod
    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        """
        Retrieves resources for a specific location.
        """
        pass

class InMemoryResourceRepository(BaseResourceRepository):
    def __init__(self):
        self._resources: dict[str, ResourceRecord] = {}

    def upsert(self, resource: ResourceRecord) -> None:
        # Check for existing inventory by (location, type, category)
        category = resource.category or ""
        existing_key = f"{resource.location_id}:{resource.resource_type}:{category}"
        
        # We store internally by this unique key to simulate the UPSERT index
        if existing_key in self._resources:
            existing = self._resources[existing_key]
            # Upsert logic: keep existing ID, update quantity/timestamp
            existing.quantity_available = resource.quantity_available
            existing.unit = resource.unit
            existing.provenance = resource.provenance
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self._resources[existing_key] = resource

    def get_all(self) -> List[ResourceRecord]:
        return list(self._resources.values())

    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        return [r for r in self._resources.values() if r.location_id == location_id]
