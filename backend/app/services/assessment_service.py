from ml.src.severity.engine import UnifiedSeverityEngine
from app.db.assessment_repository import BaseAssessmentRepository
from app.api.schemas.internal import AssessmentRecord

class AssessmentService:
    def __init__(self, assessment_repo: BaseAssessmentRepository):
        self.assessment_repo = assessment_repo
        self.severity_engine = UnifiedSeverityEngine()

    def get_or_calculate_assessment(self, incident, event_features: dict) -> AssessmentRecord:
        """
        Retrieves the latest assessment from DB, or computes and persists a new one if none exists.
        If existing assessment record has severity_status == 'unsupported_hazard' but the hazard
        is now supported by UnifiedSeverityEngine (e.g. Flood, Wildfire, Heavy Rainfall), a new assessment
        record is computed and returned.
        """
        existing = self.assessment_repo.get_latest_for_incident(incident.incident_id)
        if existing and existing.severity_status != "unsupported_hazard":
            sev_dict = existing.severity if isinstance(existing.severity, dict) else {}
            ev_cov = sev_dict.get("evidence_coverage", {}) if isinstance(sev_dict, dict) else {}
            avail_cnt = ev_cov.get("available_factors_count", 0) if isinstance(ev_cov, dict) else 0
            has_new_features = bool(event_features.get("predictor_features_x"))
            # If previous assessment was evaluated with 0 evidence factors due to empty features bug, re-evaluate
            if avail_cnt > 0 or not has_new_features:
                return existing
            
        # Compute Unified Severity (ML V2 or Policy V1)
        severity_res = self.severity_engine.predict_severity(event_features)
        
        is_unsupported = severity_res.get("status") == "unsupported_hazard"
        severity_status = "unsupported_hazard" if is_unsupported else "supported"
        severity_data = None if is_unsupported else severity_res
        
        idempotency_key = event_features.get("idempotency_key") or event_features.get("run_id")
        severity_model_version = severity_res.get("model_version") or severity_res.get("policy_version")
        
        record = AssessmentRecord(
            incident_id=incident.incident_id,
            idempotency_key=idempotency_key,
            verification_status=getattr(incident, "status", "VERIFIED"),
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
        
        self.assessment_repo.save(record)
        return record

    def save_complete_assessment(self, record: AssessmentRecord) -> AssessmentRecord:
        """
        Saves a fully orchestrated assessment record.
        """
        self.assessment_repo.save(record)
        return record
