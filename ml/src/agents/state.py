from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Canonical shared state for the disaster-response agent graph.

    Identity model:
    - target_incident_id is the authoritative incident selected by
      the API/user when operating on an existing incident.
    - incident_candidates contains the currently detected/enriched
      incident candidates produced by the report-intelligence and
      clustering pipeline.

    target_incident_id must never be replaced by a newly generated
    clustering candidate ID.
    """

    run_id: Optional[str] = None

    # ---------------------------------------------------------
    # Canonical incident identity
    # ---------------------------------------------------------

    target_incident_id: Optional[str] = None

    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    raw_reports: List[str] = Field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # Processed Data
    # ---------------------------------------------------------

    structured_reports: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    incident_candidates: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # Deterministic Engine Outputs
    # ---------------------------------------------------------

    verification_status: str = "PENDING"

    severity_score: Optional[float] = None

    severity: Optional[Dict[str, Any]] = None

    trajectory: Optional[str] = None

    trajectory_status: str = "PENDING"

    needs: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    needs_status: str = "PENDING"

    priority: Optional[Dict[str, Any]] = None

    priority_status: str = "PENDING"

    # ---------------------------------------------------------
    # Unified Assessment
    # ---------------------------------------------------------

    assessment_record: Optional[Dict[str, Any]] = None

    assessment_status: str = "PENDING"

    # ---------------------------------------------------------
    # Optimization & Coordination
    # ---------------------------------------------------------

    inventory: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    allocation_result: Optional[Dict[str, Any]] = None

    coordination_plan: Optional[str] = None

    # ---------------------------------------------------------
    # Reassessment & Dynamic Reallocation
    # ---------------------------------------------------------

    reassessment_requested: bool = False

    parent_assessment_id: Optional[str] = None

    current_assessment_id: Optional[str] = None

    previous_optimization_run_id: Optional[str] = None

    operational_allocation_baseline_id: Optional[str] = None

    assessment_diff: Optional[Dict[str, Any]] = None

    allocation_diff: Optional[Dict[str, Any]] = None

    reallocation_required: bool = False

    reallocation_decision_status: str = "PENDING"

    reassessment_reason: Optional[str] = None

    # ---------------------------------------------------------
    # Human-in-the-loop
    # ---------------------------------------------------------

    human_approval_state: str = "PENDING"

    human_feedback: Optional[str] = None

    # ---------------------------------------------------------
    # Workflow
    # ---------------------------------------------------------

    workflow_status: str = "RUNNING"

    errors: List[str] = Field(
        default_factory=list
    )