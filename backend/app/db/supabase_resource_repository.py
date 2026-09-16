import logging
from typing import List
from supabase import Client
from app.api.schemas.internal import ResourceRecord
from app.db.resource_repository import BaseResourceRepository

logger = logging.getLogger(__name__)

class SupabaseResourceRepository(BaseResourceRepository):
    def __init__(self, client: Client):
        self.client = client

    def upsert(self, resource: ResourceRecord) -> None:
        data = {
            "resource_id": resource.resource_id,
            "location_id": resource.location_id,
            "resource_type": resource.resource_type,
            "category": resource.category,
            "quantity_available": resource.quantity_available,
            "unit": resource.unit,
            "provenance": resource.provenance,
            "updated_at": resource.updated_at.isoformat(),
            "created_at": resource.created_at.isoformat()
        }
        
        try:
            # We use upsert with on_conflict constraint matching migration 003
            self.client.table("resources").upsert(
                data, 
                on_conflict="location_id, resource_type, category"
            ).execute()
        except Exception as e:
            logger.error(f"Supabase upsert resource error: {e}")
            raise RuntimeError(f"Database error upserting resource: {str(e)}")

    def _map_row(self, row: dict) -> ResourceRecord:
        return ResourceRecord(
            resource_id=row["resource_id"],
            location_id=row["location_id"],
            resource_type=row["resource_type"],
            category=row.get("category"),
            quantity_available=row.get("quantity_available", 0.0),
            unit=row["unit"],
            provenance=row.get("provenance"),
            updated_at=row.get("updated_at"),
            created_at=row.get("created_at")
        )

    def get_all(self) -> List[ResourceRecord]:
        try:
            res = self.client.table("resources").select("*").execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get all resources error: {e}")
            raise RuntimeError(f"Database error getting resources: {str(e)}")

    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        try:
            res = self.client.table("resources").select("*").eq("location_id", location_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get resources by location error: {e}")
            raise RuntimeError(f"Database error getting resources by location: {str(e)}")
