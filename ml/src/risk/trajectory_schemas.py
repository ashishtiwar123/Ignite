from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class RiskObservation(BaseModel):
    """
    A canonical temporal observation schema representing a point-in-time verified footprint.
    """
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_candidate_id: str
    observed_at: datetime
    hazard_type: str
    
    # Feature vectors extracted from Reports or VerificationAssessments
    intensity_features: Dict[str, float] = Field(default_factory=dict)
    exposure_features: Dict[str, float] = Field(default_factory=dict)
    impact_features: Dict[str, float] = Field(default_factory=dict)
    
    source: str
    source_record_id: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    observation_quality: str = "UNKNOWN"

class TrajectoryAssessment(BaseModel):
    """
    Output schema for deterministic trajectory classification.
    """
    incident_candidate_id: str
    trajectory: str = "INSUFFICIENT_EVIDENCE" # IMPROVING, STABLE, WORSENING, RAPIDLY_WORSENING, INSUFFICIENT_EVIDENCE
    
    confidence_level: float = 0.0
    evidence_strength: float = 0.0
    trend_strength: float = 0.0
    
    observations_used: int = 0
    observation_window_hours: float = 0.0
    relevant_changes: Dict[str, float] = Field(default_factory=dict)
    
    evidence: List[str] = Field(default_factory=list) # observation IDs
    explanation: str = ""
    
    policy_version: str = "risk_policy_v1"
    feature_version: str = "v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
