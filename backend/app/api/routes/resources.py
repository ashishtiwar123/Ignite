from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.db.dependencies import get_resource_repository
from app.db.resource_repository import BaseResourceRepository
from app.services.resource_service import ResourceService
from app.api.schemas.internal import ResourceRecord

router = APIRouter(prefix="/resources", tags=["resources"])

@router.post("", response_model=ResourceRecord)
def upsert_resource(
    resource_data: dict,
    resource_repo: BaseResourceRepository = Depends(get_resource_repository)
):
    """
    Upsert operational resource inventory.
    """
    service = ResourceService(resource_repo)
    try:
        return service.upsert_resource(resource_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[ResourceRecord])
def get_resources(
    location_id: str = None,
    resource_repo: BaseResourceRepository = Depends(get_resource_repository)
):
    """
    Get operational inventory.
    """
    service = ResourceService(resource_repo)
    if location_id:
        return service.get_resources_by_location(location_id)
    return service.get_all_resources()
