import logging
from typing import List, Optional
from supabase import Client
from app.api.schemas.internal import AssessmentRecord
from app.db.assessment_repository import BaseAssessmentRepository

logger = logging.getLogger(__name__)

class SupabaseAssessmentRepository(BaseAssessmentRepository):
    def __init__(self, client: Client):
        self.client = client

    def save(self, assessment: AssessmentRecord) -> None:
        data = {
            "assessment_id": assessment.assessment_id,
            "incident_id": assessment.incident_id,
            "parent_assessment_id": assessment.parent_assessment_id,
            "reassessment_reason": assessment.reassessment_reason,
            "idempotency_key": assessment.idempotency_key,
            "verification_status": assessment.verification_status,
            "severity_status": assessment.severity_status,
            "severity": assessment.severity,
            "trajectory_status": assessment.trajectory_status,
            "trajectory": assessment.trajectory,
            "priority_level": assessment.priority_level,
            "priority_score": assessment.priority_score,
            "severity_model_version": assessment.severity_model_version,
            "verification_policy_version": assessment.verification_policy_version,
            "trajectory_policy_version": assessment.trajectory_policy_version,
            "needs_policy_version": assessment.needs_policy_version,
            "priority_policy_version": assessment.priority_policy_version,
            "assessed_at": assessment.assessed_at.isoformat(),
            "created_at": assessment.created_at.isoformat()
        }
        
        # Ensure any nested datetime in JSONB fields (severity, trajectory) is cleanly serialized
        import json
        data = json.loads(json.dumps(data, default=lambda o: o.isoformat() if hasattr(o, 'isoformat') else str(o)))

        try:
            # First try to insert to catch uniqueness constraint
            self.client.table("assessments").insert(data).execute()
        except Exception as e:
            error_str = str(e)
            if "23505" in error_str and "idx_assessments_idempotency" in error_str:
                logger.info(f"Idempotent duplicate ignored for incident_id={assessment.incident_id}, key={assessment.idempotency_key}")
                return
            elif "duplicate key value violates unique constraint" in error_str and "idx_assessments_idempotency" in error_str:
                logger.info(f"Idempotent duplicate ignored for incident_id={assessment.incident_id}, key={assessment.idempotency_key}")
                return
                
            logger.error(f"Supabase save assessment error: {e}")
            raise RuntimeError(f"Database error saving assessment: {str(e)}")

    def _map_row(self, row: dict) -> AssessmentRecord:
        return AssessmentRecord(
            assessment_id=row["assessment_id"],
            incident_id=row["incident_id"],
            parent_assessment_id=row.get("parent_assessment_id"),
            reassessment_reason=row.get("reassessment_reason"),
            idempotency_key=row.get("idempotency_key", ""),
            verification_status=row.get("verification_status"),
            severity_status=row.get("severity_status"),
            severity=row.get("severity"),
            trajectory_status=row.get("trajectory_status"),
            trajectory=row.get("trajectory"),
            priority_level=row.get("priority_level"),
            priority_score=row.get("priority_score"),
            severity_model_version=row.get("severity_model_version"),
            verification_policy_version=row.get("verification_policy_version"),
            trajectory_policy_version=row.get("trajectory_policy_version"),
            needs_policy_version=row.get("needs_policy_version"),
            priority_policy_version=row.get("priority_policy_version"),
            assessed_at=row.get("assessed_at"),
            created_at=row.get("created_at")
        )

    def get(self, assessment_id: str) -> Optional[AssessmentRecord]:
        try:
            res = self.client.table("assessments").select("*").eq("assessment_id", assessment_id).execute()
            if not res.data:
                return None
            return self._map_row(res.data[0])
        except Exception as e:
            logger.error(f"Supabase get assessment error: {e}")
            raise RuntimeError(f"Database error getting assessment: {str(e)}")

    def get_latest_for_incident(self, incident_id: str) -> Optional[AssessmentRecord]:
        try:
            res = (
                self.client.table("assessments")
                .select("*")
                .eq("incident_id", incident_id)
                .order("assessed_at", desc=True)
                .limit(1)
                .execute()
            )
            if not res.data:
                return None
            return self._map_row(res.data[0])
        except Exception as e:
            logger.error(f"Supabase get_latest assessment error: {e}")
            raise RuntimeError(f"Database error getting latest assessment: {str(e)}")

    def get_all_for_incident(self, incident_id: str) -> List[AssessmentRecord]:
        try:
            res = (
                self.client.table("assessments")
                .select("*")
                .eq("incident_id", incident_id)
                .order("assessed_at", desc=True)
                .execute()
            )
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get_all assessments error: {e}")
            raise RuntimeError(f"Database error getting assessments: {str(e)}")
