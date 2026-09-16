from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class AssessmentRecord(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    idempotency_key: Optional[str] = None
    verification_status: Optional[str] = None
    severity_status: Optional[str] = None
    severity: Optional[Dict[str, Any]] = None
    trajectory_status: Optional[str] = None
    trajectory: Optional[Dict[str, Any]] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    
    # Provenance fields
    severity_model_version: Optional[str] = None
    verification_policy_version: Optional[str] = None
    trajectory_policy_version: Optional[str] = None
    needs_policy_version: Optional[str] = None
    priority_policy_version: Optional[str] = None
    
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NeedRecord(BaseModel):
    need_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    assessment_id: Optional[str] = None
    resource_type: str
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    time_window: Optional[str] = None
    rule_id: Optional[str] = None
    policy_version: Optional[str] = None
    calculation_basis: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceRecord(BaseModel):
    resource_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    resource_type: str
    category: Optional[str] = None
    quantity_available: float = 0.0
    unit: str
    provenance: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AllocationRecord(BaseModel):
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    optimization_run_id: Optional[str] = None
    incident_id: str
    requirement_id: Optional[str] = None
    source_location_id: str
    resource_type: str
    category: Optional[str] = None
    unit: str
    quantity_allocated: float
    quantity_requested: float
    quantity_unmet: float
    priority_score: Optional[float] = None
    solver_status: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OptimizationRequest(BaseModel):
    incident_ids: list[str]
    optimization_run_id: Optional[str] = None

class OptimizationResponse(BaseModel):
    optimization_run_id: Optional[str] = None
    solver_status: str
    allocations: list[AllocationRecord]
    total_requested: float
    total_allocated: float
    total_unmet: float
    objective_value: float
    generated_at: datetime

class AgentRunRequest(BaseModel):
    run_id: Optional[str] = None
    raw_reports: list[str]

class AgentRunResponse(BaseModel):
    run_id: Optional[str]
    status: str
    human_approval_state: str
    errors: list[str]
