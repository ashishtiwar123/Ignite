from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ReportResponse(BaseModel):
    report_id: str
    status: str
    message: str

class IncidentSummaryResponse(BaseModel):
    incident_id: str
    hazard_type: str
    status: str
    first_observed_at: Optional[datetime] = None
    centroid_latitude: Optional[float] = None
    centroid_longitude: Optional[float] = None

class UnsupportedHazardResponse(BaseModel):
    status: str = "unsupported_hazard"
    hazard_type: str
    message: str

class AssessmentResponse(BaseModel):
    incident_id: str
    verification_status: str
    severity: Any  # Could be dict or specific schema. If unsupported, we return UnsupportedHazardResponse or specific struct.
    trajectory: Any
    needs: Any
    priority: Any

class AllocationResultResponse(BaseModel):
    allocations: List[Dict[str, Any]]
    unmet_demand: List[Dict[str, Any]]
    status: str
    message: str

class IncidentGovernanceResponse(BaseModel):
    incident_id: str
    optimization_run_id: Optional[str] = None
    thread_id: Optional[str] = None
    approval_status: str = "NONE" # NONE, PENDING, APPROVED, REJECTED, REVISION_REQUESTED
    execution_status: str = "UNEXECUTED" # UNEXECUTED, EXECUTED, ALREADY_EXECUTED, FAILED, NOT_APPROVED
    execution_id: Optional[str] = None
    approval_id: Optional[str] = None
    deducted_resources: List[Dict[str, Any]] = []
    errors: List[str] = []

