import logging
from typing import List
from supabase import Client
from app.api.schemas.internal import NeedRecord
from app.db.needs_repository import BaseNeedsRepository

logger = logging.getLogger(__name__)

class SupabaseNeedsRepository(BaseNeedsRepository):
    def __init__(self, client: Client):
        self.client = client

    def save_all(self, needs: List[NeedRecord]) -> None:
        if not needs:
            return
            
        data = [
            {
                "need_id": n.need_id,
                "incident_id": n.incident_id,
                "assessment_id": n.assessment_id,
                "resource_type": n.resource_type,
                "category": n.category,
                "quantity": n.quantity,
                "unit": n.unit,
                "urgency": n.urgency,
                "status": n.status,
                "time_window": n.time_window,
                "rule_id": n.rule_id,
                "policy_version": n.policy_version,
                "calculation_basis": n.calculation_basis,
                "provenance": n.provenance,
                "explanation": n.explanation,
                "created_at": n.created_at.isoformat()
            } for n in needs
        ]
        
        try:
            # We want to prevent duplicate needs for the same assessment
            # We check if they exist already. If so, return idempotently.
            assessment_id = needs[0].assessment_id
            if assessment_id:
                res = self.client.table("needs").select("need_id").eq("assessment_id", assessment_id).limit(1).execute()
                if res.data:
                    logger.info(f"Idempotent duplicate ignored for needs associated with assessment_id={assessment_id}")
                    return
            
            # Insert the bulk list
            self.client.table("needs").insert(data).execute()
        except Exception as e:
            logger.error(f"Supabase save needs error: {e}")
            raise RuntimeError(f"Database error saving needs: {str(e)}")

    def _map_row(self, row: dict) -> NeedRecord:
        return NeedRecord(
            need_id=row["need_id"],
            incident_id=row["incident_id"],
            assessment_id=row.get("assessment_id"),
            resource_type=row["resource_type"],
            category=row.get("category"),
            quantity=row.get("quantity"),
            unit=row.get("unit"),
            urgency=row.get("urgency"),
            status=row.get("status"),
            time_window=row.get("time_window"),
            rule_id=row.get("rule_id"),
            policy_version=row.get("policy_version"),
            calculation_basis=row.get("calculation_basis"),
            provenance=row.get("provenance"),
            explanation=row.get("explanation"),
            created_at=row.get("created_at")
        )

    def get_by_incident(self, incident_id: str) -> List[NeedRecord]:
        try:
            res = self.client.table("needs").select("*").eq("incident_id", incident_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get needs error: {e}")
            raise RuntimeError(f"Database error getting needs: {str(e)}")

    def get_by_assessment(self, assessment_id: str) -> List[NeedRecord]:
        try:
            res = self.client.table("needs").select("*").eq("assessment_id", assessment_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get needs by assessment error: {e}")
            raise RuntimeError(f"Database error getting needs by assessment: {str(e)}")
