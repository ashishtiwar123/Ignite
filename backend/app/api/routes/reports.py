from fastapi import APIRouter, HTTPException, Depends
from app.api.schemas.requests import ReportCreate
from app.api.schemas.responses import ReportResponse
from app.services.incident_service import IncidentService
from app.db.dependencies import get_incident_repository
from app.db.base_repository import BaseIncidentRepository

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("", response_model=ReportResponse, status_code=201)
def create_report(
    report_data: ReportCreate,
    incident_repo: BaseIncidentRepository = Depends(get_incident_repository)
):
    incident_service = IncidentService(incident_repo)
    try:
        # Pass the dump of the validated Pydantic model to the service
        report, incident = incident_service.process_report(report_data.model_dump())
        return ReportResponse(
            report_id=report.report_id,
            status="processing",
            message=f"Report ingested. Correlated to candidate incident {incident.incident_id}."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
