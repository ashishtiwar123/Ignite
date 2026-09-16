from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.api.schemas.responses import IncidentSummaryResponse, AssessmentResponse, UnsupportedHazardResponse
from app.api.schemas.requests import AssessmentReassessRequest
from app.db.dependencies import get_incident_repository, get_assessment_repository
from app.db.base_repository import BaseIncidentRepository
from app.db.assessment_repository import BaseAssessmentRepository
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", response_model=List[IncidentSummaryResponse])
def get_incidents(
    incident_repo: BaseIncidentRepository = Depends(get_incident_repository)
):
    incidents = incident_repo.get_all()
    return [
        IncidentSummaryResponse(
            incident_id=i.incident_id,
            hazard_type=i.hazard_type,
            status=i.status,
            first_observed_at=i.first_observed_at,
            centroid_latitude=i.centroid_latitude,
            centroid_longitude=i.centroid_longitude
        ) for i in incidents
    ]

@router.get("/{incident_id}/assessment")
def get_incident_assessment(
    incident_id: str,
    incident_repo: BaseIncidentRepository = Depends(get_incident_repository),
    assessment_repo: BaseAssessmentRepository = Depends(get_assessment_repository)
):
    incident = incident_repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    assessment_service = AssessmentService(assessment_repo)
    
    event_features = {
        "incident_id": incident.incident_id,
        "disaster_type": incident.hazard_type,
        "predictor_features_x": {}
    }
    
    try:
        record = assessment_service.get_or_calculate_assessment(incident, event_features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if record.severity_status == "unsupported_hazard":
        severity = UnsupportedHazardResponse(
            hazard_type=incident.hazard_type,
            message="Hazard type not supported by severity model"
        )
    else:
        severity = record.severity
        
    return AssessmentResponse(
        incident_id=record.incident_id,
        verification_status=record.verification_status,
        severity=severity,
        trajectory=record.trajectory or {"status": "not_calculated"},
        needs={"status": "not_calculated"},
        priority={"status": "not_calculated"}
    )

@router.post("/{incident_id}/reassess")
def reassess_incident(
    incident_id: str, 
    request: AssessmentReassessRequest,
    incident_repo: BaseIncidentRepository = Depends(get_incident_repository)
):
    incident = incident_repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # The full reassessment pipeline is deferred
    raise HTTPException(
        status_code=501, 
        detail="Full reassessment lifecycle via LangGraph is not yet supported in this phase."
    )
