import logging
from typing import List

from app.api.schemas.internal import AllocationRecord
from app.db.allocation_repository import BaseAllocationRepository

logger = logging.getLogger(__name__)

class SupabaseAllocationRepository(BaseAllocationRepository):
    def __init__(self, client):
        self.client = client
        
    def _map_row(self, row: dict) -> AllocationRecord:
        return AllocationRecord(
            allocation_id=row["allocation_id"],
            optimization_run_id=row["optimization_run_id"],
            incident_id=row["incident_id"],
            requirement_id=row.get("requirement_id"),
            source_location_id=row["source_location_id"],
            resource_type=row["resource_type"],
            category=row.get("category"),
            unit=row["unit"],
            quantity_allocated=row["quantity_allocated"],
            quantity_requested=row["quantity_requested"],
            quantity_unmet=row["quantity_unmet"],
            priority_score=row.get("priority_score"),
            solver_status=row.get("solver_status"),
            explanation=row.get("explanation"),
            created_at=row["created_at"]
        )
        
    def save_allocations(self, allocations: List[AllocationRecord]) -> None:
        if not allocations:
            return
            
        run_id = allocations[0].optimization_run_id
        
        try:
            # Check for existing records for this optimization_run_id for idempotency
            if run_id:
                existing = self.client.table("allocations").select("allocation_id").eq("optimization_run_id", run_id).limit(1).execute()
                if existing.data:
                    logger.info(f"Allocations for run_id {run_id} already exist in Supabase. Skipping.")
                    return
                
            payload = []
            for a in allocations:
                row = a.model_dump(mode="json")
                payload.append(row)
                
            if payload:
                self.client.table("allocations").insert(payload).execute()
                
        except Exception as e:
            logger.error(f"Supabase save allocations error: {e}")
            raise RuntimeError(f"Database error saving allocations: {str(e)}")
            
    def get_by_incident(self, incident_id: str) -> List[AllocationRecord]:
        try:
            res = self.client.table("allocations").select("*").eq("incident_id", incident_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get allocations by incident error: {e}")
            raise RuntimeError(f"Database error getting allocations: {str(e)}")
