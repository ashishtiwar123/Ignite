from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas.internal import (
    AgentRunRequest,
    AgentRunResponse,
    AgentResumeRequest,
    ExecutionRequest,
    ExecutionResponse,
    ReassessmentRequest,
    ReassessmentResponse
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])

_agent_service_instance = None

def get_agent_service() -> AgentService:
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

@router.post("/run", response_model=AgentRunResponse)
def run_agent(
    request: AgentRunRequest,
    service: AgentService = Depends(get_agent_service)
):
    try:
        if not request.raw_reports and not request.incident_id:
            raise ValueError("Agent run requires at least one raw report or an existing incident_id.")
        
        response = service.run_agent(request)
        return response
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/review/{thread_id}", response_model=AgentRunResponse)
def submit_review(
    thread_id: str,
    request: AgentResumeRequest,
    service: AgentService = Depends(get_agent_service)
):
    try:
        if request.decision not in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
            raise ValueError(f"Invalid decision: {request.decision}")
            
        response = service.submit_review(thread_id, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/execute/{thread_id}", response_model=ExecutionResponse)
def execute_proposal(
    thread_id: str,
    request: ExecutionRequest = ExecutionRequest(),
    service: AgentService = Depends(get_agent_service)
):
    try:
        response = service.execute_agent(thread_id, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reassess/{thread_id}", response_model=ReassessmentResponse)
def reassess_incident(
    thread_id: str,
    request: ReassessmentRequest,
    service: AgentService = Depends(get_agent_service)
):
    try:
        response = service.reassess_agent(thread_id, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


