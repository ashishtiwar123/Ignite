from typing import List
from app.db.resource_repository import BaseResourceRepository
from app.api.schemas.internal import ResourceRecord

class ResourceService:
    def __init__(self, resource_repo: BaseResourceRepository):
        self.resource_repo = resource_repo

    def upsert_resource(self, resource_data: dict) -> ResourceRecord:
        """
        Validates and upserts inventory records.
        """
        record = ResourceRecord(
            location_id=resource_data["location_id"],
            resource_type=resource_data["resource_type"],
            category=resource_data.get("category"),
            quantity_available=float(resource_data.get("quantity_available", 0.0)),
            unit=resource_data["unit"],
            provenance=resource_data.get("provenance")
        )
        
        if record.quantity_available < 0:
            raise ValueError("Resource quantity cannot be negative")
            
        self.resource_repo.upsert(record)
        return record

    def get_all_resources(self) -> List[ResourceRecord]:
        return self.resource_repo.get_all()

    def get_resources_by_location(self, location_id: str) -> List[ResourceRecord]:
        return self.resource_repo.get_by_location(location_id)
