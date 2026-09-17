from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class SeverityAssessmentResult(BaseModel):
    """
    Canonical unified result schema for all severity evaluations (ML and Policy).
    """
    status: str  # "success", "unsupported_hazard", "insufficient_evidence", "failed"
    hazard_type: str
    severity_class: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    severity_score: float  # Bounded 0.0 to 10.0
    assessment_method: str  # "ML" or "POLICY"
    model_version: Optional[str] = None  # e.g., "severity_v2"
    policy_version: Optional[str] = None  # e.g., "FLOOD_POLICY_V1"
    evidence_coverage: Dict[str, Any] = Field(default_factory=dict)
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    confidence: Optional[float] = None  # None for POLICY assessments
    probabilities: Optional[Dict[str, float]] = None  # None for POLICY assessments
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
