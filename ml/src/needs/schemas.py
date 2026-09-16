from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class NeedsAssessmentInput(BaseModel):
    """
    Canonical input schema for the Needs Assessment Engine.
    """
    verified_incident_id: str
    hazard_type: str
    
    # Severity context
    severity_score: Optional[float] = None
    
    # Trajectory context
    trajectory: str = "UNKNOWN"
    
    # Population context
    affected_population: Optional[int] = None
    displaced_population: Optional[int] = None
    
    duration_days: Optional[int] = None
    
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Dict[str, Any] = Field(default_factory=dict)

class ResourceRequirement(BaseModel):
    """
    Canonical output schema for a computed resource requirement.
    """
    requirement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verified_incident_id: str
    
    resource_type: str
    category: str # e.g. WATER, FOOD, SHELTER, MEDICAL, RESCUE, SANITATION
    
    quantity: Optional[float] = None
    unit: Optional[str] = None
    
    time_window: str = "per_day"
    status: str # CALCULATED, INSUFFICIENT_DATA
    
    urgency_category: Optional[str] = None # LOW, MODERATE, HIGH, CRITICAL
    
    rule_id: str
    policy_version: str = "needs_policy_v1"
    
    calculation_basis: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    
    explanation: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
