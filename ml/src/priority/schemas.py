from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class PriorityEngineInput(BaseModel):
    """
    Canonical input schema for the Priority Engine.
    Aggregates outputs from Severity (2C), Verification (2E), Trajectory (2F), and Needs (2G).
    """
    verified_incident_id: str
    
    # 2E Verification
    verification_status: str
    
    # 2C Severity
    severity_score: Optional[float] = None
    
    # 2F Trajectory
    trajectory: str = "UNKNOWN"
    
    # Needs / Population
    affected_population: Optional[int] = None
    
    # Extracted from 2G Needs Assessment
    medical_urgency: Optional[str] = None
    rescue_urgency: Optional[str] = None
    
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Dict[str, Any] = Field(default_factory=dict)

class PriorityAssessment(BaseModel):
    """
    Canonical output schema for priority evaluation.
    """
    priority_assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verified_incident_id: str
    
    priority_score: float = 0.0 # 0 to 100 normalized
    priority_level: str = "LOW" # CRITICAL, HIGH, MEDIUM, LOW, or PENDING_VERIFICATION
    
    factor_scores: Dict[str, float] = Field(default_factory=dict)
    contributing_factors: List[str] = Field(default_factory=list)
    missing_factors: List[str] = Field(default_factory=list)
    
    explanation: str
    
    policy_version: str = "priority_policy_v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Dict[str, Any] = Field(default_factory=dict)
