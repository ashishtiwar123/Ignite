import uuid
import logging
from typing import Optional

from ml.src.agents.graph import build_graph, GraphState
from ml.src.agents.state import AgentState
from app.api.schemas.internal import AgentRunRequest, AgentRunResponse

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        # We reuse the graph definition from ML module.
        # Checkpointer (MemorySaver) is already configured in build_graph.
        self.app = build_graph()
        
    def run_agent(self, request: AgentRunRequest) -> AgentRunResponse:
        try:
            # 1. Determine Thread ID vs Run ID
            # Thread ID is required by MemorySaver. Run ID is the execution identity.
            if request.run_id is not None:
                thread_id = request.run_id
                run_id = request.run_id
            else:
                thread_id = str(uuid.uuid4())
                run_id = None
                
            # 2. Setup initial state and config
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = AgentState(
                run_id=run_id,
                raw_reports=request.raw_reports
            )
            
            # 3. Invoke Graph
            # The graph processes the state and might interrupt if human review is needed.
            result = self.app.invoke({"state": initial_state}, config=config)
            
            # 4. Map Result
            # The result is a GraphState dict which contains our AgentState
            final_state: AgentState = result.get("state")
            if not final_state:
                raise ValueError("Graph did not return a valid state.")
                
            # 5. Determine Status
            status = "COMPLETED"
            
            # Check for Rejection from Verification node or similar
            if final_state.verification_status == "REJECTED":
                status = "REJECTED"
            elif final_state.human_approval_state == "PENDING" and (
                final_state.verification_status == "NEEDS_VERIFICATION" or
                (final_state.allocation_result and final_state.allocation_result.get("solver_status") == "INFEASIBLE") or
                final_state.coordination_plan
            ):
                # We reached a human interrupt point (e.g. human_review node)
                status = "INTERRUPTED"
                    
            return AgentRunResponse(
                run_id=final_state.run_id,
                status=status,
                human_approval_state=final_state.human_approval_state,
                errors=final_state.errors
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            # Do NOT expose secrets or stack traces, just return FAILED with minimal message
            return AgentRunResponse(
                run_id=request.run_id,
                status="FAILED",
                human_approval_state="PENDING",
                errors=[f"Internal graph execution error: {type(e).__name__}"]
            )
