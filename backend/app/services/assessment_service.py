from ml.src.models.severity_v2.predictor_v2 import SeverityPredictorV2
from app.db.assessment_repository import BaseAssessmentRepository
from app.api.schemas.internal import AssessmentRecord

class AssessmentService:
    def __init__(self, assessment_repo: BaseAssessmentRepository):
        self.assessment_repo = assessment_repo
        self.severity_predictor = SeverityPredictorV2()

    def get_or_calculate_assessment(self, incident, event_features: dict) -> AssessmentRecord:
        """
        Retrieves the latest assessment from DB, or computes and persists a new one if none exists.
        """
        existing = self.assessment_repo.get_latest_for_incident(incident.incident_id)
        if existing:
            return existing
            
        # Calculate Severity V2
        severity_res = self.severity_predictor.predict_severity(event_features)
        
        is_unsupported = severity_res.get("status") == "unsupported_hazard"
        severity_status = "unsupported_hazard" if is_unsupported else "supported"
        severity_data = None if is_unsupported else severity_res
        
        # Determine caller provided idempotency
        # Must be a stable logical identity (run_id or idempotency_key). 
        # No fallback to timestamp.
        idempotency_key = event_features.get("idempotency_key") or event_features.get("run_id")
        
        # Capture precise provenance for the executed components
        severity_model_version = severity_res.get("model_version")
        
        # Verification, Trajectory, Needs, Priority are NOT currently executed by this service flow.
        # Their provenance is explicitly set to None.
        
        # Create AssessmentRecord
        record = AssessmentRecord(
            incident_id=incident.incident_id,
            idempotency_key=idempotency_key,
            verification_status=incident.status,
            severity_status=severity_status,
            severity=severity_data,
            trajectory_status="not_calculated",
            trajectory={"status": "not_calculated"},
            priority_level=None,
            priority_score=None,
            severity_model_version=severity_model_version,
            verification_policy_version=None,
            trajectory_policy_version=None,
            needs_policy_version=None,
            priority_policy_version=None
        )
        
        # Persist
        self.assessment_repo.save(record)
        return record

    def save_complete_assessment(self, record: AssessmentRecord) -> AssessmentRecord:
        """
        Saves a fully orchestrated assessment record.
        """
        self.assessment_repo.save(record)
        return record
