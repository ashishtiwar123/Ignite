from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class VerificationEvidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_candidate_id: str
    source: str
    source_record_id: str
    source_type: str = "UNKNOWN"
    source_reliability_score: float = 0.0
    evidence_type: str = "OBSERVATION"
    observed_at: Optional[datetime] = None
    evidence_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hazard_type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    consistency_status: str = "PENDING"
    provenance: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

class VerificationAssessment(BaseModel):
    incident_candidate_id: str
    verification_status: str = "CANDIDATE" # CANDIDATE, NEEDS_VERIFICATION, VERIFIED, REJECTED
    verification_score: float = 0.0
    confidence: float = 0.0
    
    evidence_count: int = 0
    independent_source_count: int = 0
    
    corroboration_score: float = 0.0
    spatial_consistency_score: float = 0.0
    temporal_consistency_score: float = 0.0
    hazard_consistency_score: float = 0.0
    attribute_consistency_score: float = 0.0
    source_reliability_score: float = 0.0
    
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    
    explanation: List[str] = Field(default_factory=list)
    policy_version: str = "Operational Verification Policy v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
