from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class AssessmentRecord(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    parent_assessment_id: Optional[str] = None
    reassessment_reason: Optional[str] = None
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
    previous_optimization_run_id: Optional[str] = None
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

class ApprovalRecord(BaseModel):
    approval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    optimization_run_id: Optional[str] = None
    action_id: Optional[str] = None
    status: str = "PENDING"
    reviewer_id: Optional[str] = None
    reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentResumeRequest(BaseModel):
    decision: str  # APPROVED, REJECTED, REVISION_REQUESTED
    reason: Optional[str] = None

class ActionRecord(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: Optional[str] = None
    incident_id: str
    optimization_run_id: Optional[str] = None
    approval_id: Optional[str] = None
    action_type: str = "RESOURCE_ALLOCATION_EXECUTION"
    status: str = "PROPOSED" # PROPOSED, EXECUTING, EXECUTED, FAILED, ALREADY_EXECUTED
    description: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    executed_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionRequest(BaseModel):
    optimization_run_id: Optional[str] = None
    incident_id: Optional[str] = None
    executor_id: Optional[str] = None
    approved: Optional[bool] = None  # Client flags like "approved=true" MUST NEVER be trusted as authorization


class DeductedResourceItem(BaseModel):
    resource_id: str
    location_id: str
    resource_type: str
    category: Optional[str] = None
    quantity_deducted: float
    unit: str
    previous_quantity: float
    new_quantity: float

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str  # EXECUTED, ALREADY_EXECUTED, FAILED, NOT_APPROVED, INVALID_PROPOSAL
    optimization_run_id: Optional[str] = None
    approval_id: Optional[str] = None
    incident_id: Optional[str] = None
    deducted_resources: list[DeductedResourceItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

class AssessmentDiff(BaseModel):
    parent_assessment_id: Optional[str] = None
    current_assessment_id: str
    severity_changed: bool = False
    previous_severity: Optional[str] = None
    current_severity: Optional[str] = None
    previous_severity_score: Optional[float] = None
    current_severity_score: Optional[float] = None
    trajectory_changed: bool = False
    previous_trajectory: Optional[str] = None
    current_trajectory: Optional[str] = None
    priority_changed: bool = False
    previous_priority_level: Optional[str] = None
    current_priority_level: Optional[str] = None
    previous_priority_score: Optional[float] = None
    current_priority_score: Optional[float] = None
    priority_score_delta: float = 0.0
    needs_changed: bool = False
    added_needs: list[Dict[str, Any]] = Field(default_factory=list)
    increased_needs: list[Dict[str, Any]] = Field(default_factory=list)
    decreased_needs: list[Dict[str, Any]] = Field(default_factory=list)
    resolved_needs: list[Dict[str, Any]] = Field(default_factory=list)

class AllocationDeltaItem(BaseModel):
    resource_type: str
    category: Optional[str] = None
    source_location_id: str
    unit: str
    change_type: str  # ADDED, INCREASED, DECREASED, REMOVED, UNCHANGED
    previous_quantity: float = 0.0
    new_quantity: float = 0.0
    delta_quantity: float = 0.0
    explanation: Optional[str] = None

class AllocationDiff(BaseModel):
    baseline_optimization_run_id: Optional[str] = None
    new_optimization_run_id: Optional[str] = None
    deltas: list[AllocationDeltaItem] = Field(default_factory=list)
    total_previous_allocated: float = 0.0
    total_new_allocated: float = 0.0
    net_allocated_delta: float = 0.0
    has_meaningful_change: bool = False

class ReassessmentRequest(BaseModel):
    new_reports: list[str] = Field(default_factory=list)
    run_id: Optional[str] = None
    reassessment_reason: Optional[str] = None

class ReassessmentResponse(BaseModel):
    run_id: Optional[str] = None
    thread_id: str
    incident_id: Optional[str] = None
    previous_assessment_id: Optional[str] = None
    current_assessment_id: Optional[str] = None
    assessment_diff: Optional[AssessmentDiff] = None
    reallocation_decision_status: str  # NO_REALLOCATION_REQUIRED, REALLOCATION_REQUIRED, OPTIMIZATION_INFEASIBLE, INSUFFICIENT_DATA, NEEDS_HUMAN_REVIEW
    reallocation_required: bool = False
    new_optimization_run_id: Optional[str] = None
    allocation_diff: Optional[AllocationDiff] = None
    human_approval_state: str = "PENDING"
    status: str = "COMPLETED"  # COMPLETED, PENDING_REVIEW, NO_REALLOCATION_REQUIRED, FAILED
    errors: list[str] = Field(default_factory=list)


