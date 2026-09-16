from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.db.dependencies import get_needs_repository
from app.db.needs_repository import BaseNeedsRepository
from app.services.needs_service import NeedsService
from app.api.schemas.internal import NeedRecord

router = APIRouter(prefix="/incidents", tags=["needs"])

@router.post("/{incident_id}/needs", response_model=List[NeedRecord])
def create_needs(
    incident_id: str,
    assessment_id: str,
    raw_needs: List[Dict[str, Any]],
    needs_repo: BaseNeedsRepository = Depends(get_needs_repository)
):
    """
    Persist raw ML needs output.
    """
    service = NeedsService(needs_repo)
    try:
        return service.save_needs_from_assessment(incident_id, assessment_id, raw_needs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{incident_id}/needs", response_model=List[NeedRecord])
def get_needs(
    incident_id: str,
    needs_repo: BaseNeedsRepository = Depends(get_needs_repository)
):
    """
    Get all needs for an incident.
    """
    service = NeedsService(needs_repo)
    return service.get_needs_for_incident(incident_id)
