from typing import List, Optional
from datetime import datetime, timezone
import logging

from app.api.schemas.internal import ApprovalRecord
from app.db.approval_repository import BaseApprovalRepository
from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseApprovalRepository(BaseApprovalRepository):
    def __init__(self, client: Client):
        self.client = client

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        response = self.client.table("approvals").select("*").eq("approval_id", approval_id).execute()
        if response.data:
            return ApprovalRecord(**response.data[0])
        return None

    def get_all(self) -> List[ApprovalRecord]:
        response = self.client.table("approvals").select("*").execute()
        return [ApprovalRecord(**r) for r in response.data]

    def get_by_optimization_run(self, optimization_run_id: str) -> List[ApprovalRecord]:
        response = (
            self.client.table("approvals")
            .select("*")
            .eq("optimization_run_id", optimization_run_id)
            .execute()
        )
        return [ApprovalRecord(**r) for r in response.data]

    def upsert(self, record: ApprovalRecord) -> ApprovalRecord:
        # Enforce immutability
        existing = self.get(record.approval_id)
        if existing and existing.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
            if record.status != existing.status:
                raise ValueError(
                    f"Cannot mutate an already finalized approval decision "
                    f"('{existing.status}' -> '{record.status}')."
                )

        # Enforce no conflicting decisions for same run
        if record.optimization_run_id and record.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
            for ex in self.get_by_optimization_run(record.optimization_run_id):
                if ex.approval_id != record.approval_id and ex.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
                    raise ValueError(
                        "Cannot create a conflicting approval record for this optimization run."
                    )

        data = record.model_dump()
        # Serialize datetimes
        data["created_at"] = data["created_at"].isoformat() if data.get("created_at") else None
        data["decided_at"] = data["decided_at"].isoformat() if data.get("decided_at") else None

        response = self.client.table("approvals").upsert(data).execute()
        return ApprovalRecord(**response.data[0])

    def delete(self, approval_id: str) -> bool:
        response = self.client.table("approvals").delete().eq("approval_id", approval_id).execute()
        return len(response.data) > 0
