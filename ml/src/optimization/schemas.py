from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ml.src.needs.schemas import ResourceRequirement
from ml.src.priority.schemas import PriorityAssessment

class ResourceInventory(BaseModel):
    """
    Represents finite available resource supply at a specific location.
    """
    inventory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    resource_type: str
    category: str # WATER, FOOD, SHELTER, etc.
    quantity_available: float
    unit: str
    
    provenance: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AllocationContext(BaseModel):
    """
    The full state passed to the optimizer.
    """
    optimization_run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incidents: List[PriorityAssessment]
    requirements: List[ResourceRequirement]
    inventory: List[ResourceInventory]
    
    policy_version: str = "optimization_policy_v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceAllocation(BaseModel):
    """
    A single allocation edge from a source to an incident.
    """
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    optimization_run_id: str
    
    verified_incident_id: str
    requirement_id: str
    source_location_id: str
    
    resource_type: str
    category: str
    unit: str
    
    quantity_allocated: float
    quantity_requested: float
    quantity_unmet: float
    
    priority_score: float
    
    explanation: str
    provenance: Dict[str, Any] = Field(default_factory=dict)

class AllocationResult(BaseModel):
    """
    The complete result of an optimization run.
    """
    optimization_run_id: str
    solver_status: str # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN
    
    allocations: List[ResourceAllocation]
    
    total_requested: float = 0.0
    total_allocated: float = 0.0
    total_unmet: float = 0.0
    
    objective_value: float = 0.0
    
    constraints_summary: Dict[str, Any] = Field(default_factory=dict)
    policy_version: str = "optimization_policy_v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
