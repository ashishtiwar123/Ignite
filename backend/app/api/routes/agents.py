from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas.internal import AgentRunRequest, AgentRunResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])

def get_agent_service() -> AgentService:
    return AgentService()

@router.post("/run", response_model=AgentRunResponse)
def run_agent(
    request: AgentRunRequest,
    service: AgentService = Depends(get_agent_service)
):
    try:
        if not request.raw_reports:
            raise ValueError("Agent run requires at least one raw report.")
        
        response = service.run_agent(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
