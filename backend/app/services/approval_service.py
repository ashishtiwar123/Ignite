import logging
from typing import Optional
from datetime import datetime, timezone

from app.api.schemas.internal import ApprovalRecord
from app.db.approval_repository import BaseApprovalRepository
from app.db.client import get_supabase_client

logger = logging.getLogger(__name__)

VALID_DECISIONS = {"APPROVED", "REJECTED", "REVISION_REQUESTED"}


class ApprovalService:
    def __init__(self, approval_repo: BaseApprovalRepository):
        self.approval_repo = approval_repo

    def record_approval(
        self,
        incident_id: str,
        optimization_run_id: Optional[str],
        decision: str,
        reason: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> ApprovalRecord:

        if decision not in VALID_DECISIONS:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of: {VALID_DECISIONS}")

        existing = None
        if optimization_run_id:
            for a in self.approval_repo.get_by_optimization_run(optimization_run_id):
                if a.status == "PENDING":
                    existing = a
                    break
        if not existing and incident_id:
            for a in self.approval_repo.get_by_incident(incident_id):
                if a.status == "PENDING":
                    existing = a
                    break

        if existing:
            record = existing.model_copy(update={
                "status": decision,
                "reason": reason,
                "reviewer_id": reviewer_id,
                "decided_at": datetime.utcnow(),
                "thread_id": thread_id or existing.thread_id
            })
        else:
            record = ApprovalRecord(
                incident_id=incident_id,
                optimization_run_id=optimization_run_id,
                thread_id=thread_id,
                status=decision,
                reason=reason,
                reviewer_id=reviewer_id,
                decided_at=datetime.utcnow()
            )

        persisted = self.approval_repo.upsert(record)
        self._record_audit_event(persisted)
        return persisted

    def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        return self.approval_repo.get(approval_id)

    def _record_audit_event(self, record: ApprovalRecord):
        """Create an immutable audit trail event. Never logs secrets or credentials."""
        try:
            client = get_supabase_client()
            if client:
                event_type = f"APPROVAL_{record.status}"
                payload = {
                    "approval_id": record.approval_id,
                    "incident_id": record.incident_id,
                    "optimization_run_id": record.optimization_run_id,
                    "status": record.status,
                    "reviewer_id": record.reviewer_id,
                    "reason": record.reason,
                    "decided_at": record.decided_at.isoformat() if record.decided_at else None,
                }
                client.table("audit_events").insert({
                    "event_type": event_type,
                    "incident_id": record.incident_id,
                    "actor_type": "HUMAN_REVIEWER",
                    "actor_reference": record.reviewer_id or "UNKNOWN",
                    "payload": payload,
                    "correlation_id": record.optimization_run_id
                }).execute()
        except Exception as e:
            # Never fail the approval operation due to audit logging issues
            logger.error(f"Failed to record audit event for approval {record.approval_id}: {e}")
