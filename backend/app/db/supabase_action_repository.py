from typing import List, Optional
import logging
from app.api.schemas.internal import ActionRecord
from app.db.action_repository import BaseActionRepository
from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseActionRepository(BaseActionRepository):
    def __init__(self, client: Client):
        self.client = client

    def _map_row(self, row: dict) -> ActionRecord:
        return ActionRecord(
            action_id=row["action_id"],
            execution_id=row.get("execution_id"),
            incident_id=row["incident_id"],
            optimization_run_id=row.get("optimization_run_id"),
            approval_id=row.get("approval_id"),
            action_type=row.get("action_type", "RESOURCE_ALLOCATION_EXECUTION"),
            status=row.get("status", "PROPOSED"),
            description=row.get("description"),
            payload=row.get("payload"),
            executed_by=row.get("executed_by"),
            executed_at=row.get("executed_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    def save(self, action: ActionRecord) -> ActionRecord:
        data = action.model_dump(mode="json")
        try:
            res = self.client.table("actions").upsert(data).execute()
            if res.data:
                return self._map_row(res.data[0])
            return action
        except Exception as e:
            logger.error(f"Supabase save action error: {e}")
            raise RuntimeError(f"Database error saving action: {str(e)}")

    def get(self, action_id: str) -> Optional[ActionRecord]:
        try:
            res = self.client.table("actions").select("*").eq("action_id", action_id).execute()
            if res.data:
                return self._map_row(res.data[0])
            return None
        except Exception as e:
            logger.error(f"Supabase get action error: {e}")
            raise RuntimeError(f"Database error fetching action: {str(e)}")

    def get_by_execution_id(self, execution_id: str) -> Optional[ActionRecord]:
        try:
            res = self.client.table("actions").select("*").eq("execution_id", execution_id).execute()
            if res.data:
                return self._map_row(res.data[0])
            return None
        except Exception as e:
            logger.error(f"Supabase get action by execution_id error: {e}")
            raise RuntimeError(f"Database error fetching action by execution_id: {str(e)}")

    def get_by_optimization_run(self, optimization_run_id: str) -> List[ActionRecord]:
        try:
            res = self.client.table("actions").select("*").eq("optimization_run_id", optimization_run_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get actions by optimization_run_id error: {e}")
            raise RuntimeError(f"Database error fetching actions by optimization_run_id: {str(e)}")

    def get_by_approval_id(self, approval_id: str) -> List[ActionRecord]:
        try:
            res = self.client.table("actions").select("*").eq("approval_id", approval_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get actions by approval_id error: {e}")
            raise RuntimeError(f"Database error fetching actions by approval_id: {str(e)}")
