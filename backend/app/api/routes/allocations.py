from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.api.schemas.internal import OptimizationRequest, OptimizationResponse, AllocationRecord
from app.db.allocation_repository import BaseAllocationRepository
from app.db.needs_repository import BaseNeedsRepository
from app.db.resource_repository import BaseResourceRepository
from app.db.assessment_repository import BaseAssessmentRepository

from app.db.dependencies import (
    get_allocation_repository,
    get_needs_repository,
    get_resource_repository,
    get_assessment_repository
)
from app.services.allocation_service import AllocationService

router = APIRouter(prefix="/allocations", tags=["allocations"])

def get_allocation_service(
    allocation_repo: BaseAllocationRepository = Depends(get_allocation_repository),
    needs_repo: BaseNeedsRepository = Depends(get_needs_repository),
    resource_repo: BaseResourceRepository = Depends(get_resource_repository),
    assessment_repo: BaseAssessmentRepository = Depends(get_assessment_repository),
) -> AllocationService:
    return AllocationService(
        allocation_repo=allocation_repo,
        needs_repo=needs_repo,
        resource_repo=resource_repo,
        assessment_repo=assessment_repo
    )

@router.post("/optimize", response_model=OptimizationResponse)
def optimize_allocations(
    request: OptimizationRequest,
    service: AllocationService = Depends(get_allocation_service)
):
    try:
        if not request.incident_ids:
            raise ValueError("Optimization requires at least one incident ID.")
        response = service.optimize(request)
        
        # If infeasible, we still return the response but can set a specific status code if we wanted.
        # But 200 OK with solver_status="INFEASIBLE" matches optimization API conventions better.
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/incident/{incident_id}", response_model=List[AllocationRecord])
def get_allocations_for_incident(
    incident_id: str,
    allocation_repo: BaseAllocationRepository = Depends(get_allocation_repository)
):
    try:
        return allocation_repo.get_by_incident(incident_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
