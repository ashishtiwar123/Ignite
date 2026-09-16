from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    """
    The canonical shared graph state.
    """
    run_id: str
    
    # Input
    raw_reports: List[str] = Field(default_factory=list)
    
    # Processed Data
    structured_reports: List[Dict[str, Any]] = Field(default_factory=list)
    incident_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Determinstic Engine Outputs
    verification_status: str = "PENDING"
    severity_score: Optional[float] = None
    trajectory: Optional[str] = None
    needs: List[Dict[str, Any]] = Field(default_factory=list)
    priority: Optional[Dict[str, Any]] = None
    
    # Optimization & Coordination
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    allocation_result: Optional[Dict[str, Any]] = None
    coordination_plan: Optional[str] = None
    
    # Human-in-the-loop
    human_approval_state: str = "PENDING" # APPROVE, MODIFY, REJECT, PENDING
    human_feedback: Optional[str] = None
    
    # Workflow
    workflow_status: str = "RUNNING"
    errors: List[str] = Field(default_factory=list)
