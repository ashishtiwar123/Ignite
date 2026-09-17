import uuid
import logging
from typing import Optional

from ml.src.agents.graph import build_graph, GraphState
from ml.src.agents.state import AgentState
from app.api.schemas.internal import AgentRunRequest, AgentRunResponse, AgentResumeRequest

logger = logging.getLogger(__name__)

_shared_graph_app = None

def get_shared_graph_app():
    global _shared_graph_app
    if _shared_graph_app is None:
        _shared_graph_app = build_graph()
    return _shared_graph_app

class AgentService:
    def __init__(self, app=None):
        # We reuse the graph definition from ML module.
        # Checkpointer (MemorySaver) is already configured in build_graph.
        self.app = app if app is not None else get_shared_graph_app()

    def run_agent(self, request: AgentRunRequest) -> AgentRunResponse:
        try:
            # 1. Determine Thread ID vs Run ID
            # Thread ID is required by MemorySaver. Run ID is the domain execution identity.
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
            # The graph processes the state and might interrupt before human_review node.
            result = self.app.invoke({"state": initial_state}, config=config)

            # 4. Map Result & Checkpoint State
            state_snap = self.app.get_state(config)
            is_interrupted = bool(state_snap and state_snap.next)
            if result and "state" in result:
                final_state: AgentState = result.get("state")
            elif state_snap and state_snap.values:
                final_state: AgentState = state_snap.values.get("state")
            else:
                final_state = None

            if not final_state:
                raise ValueError("Graph did not return a valid state.")

            # 5. Determine Status
            status = "COMPLETED"

            if final_state.verification_status == "REJECTED":
                status = "REJECTED"
            elif is_interrupted or (
                final_state.human_approval_state == "PENDING" and final_state.allocation_result
            ):
                # We reached a human interrupt point (interrupted before human_review node)
                status = "PENDING_REVIEW"

            # Also include thread_id in errors for caller to track (not a secret)
            errors = list(final_state.errors)

            return AgentRunResponse(
                run_id=final_state.run_id,
                status=status,
                human_approval_state=final_state.human_approval_state,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            # Do NOT expose secrets or stack traces
            return AgentRunResponse(
                run_id=request.run_id,
                status="FAILED",
                human_approval_state="PENDING",
                errors=[f"Internal graph execution error: {type(e).__name__}"]
            )

    def submit_review(self, thread_id: str, request: AgentResumeRequest) -> AgentRunResponse:
        """
        Resume a paused graph execution after injecting the human review decision.

        SAFETY:
        - Only resumes if graph state is currently PENDING at human_review.
        - Persists the human decision before resuming (immutable governance record).
        - Never re-runs optimization, severity, or any ML computation.
        - Never mutates ResourceRepository.
        - thread_id NEVER becomes optimization_run_id.
        """
        from app.db.dependencies import get_approval_repository
        from app.services.approval_service import ApprovalService

        if request.decision not in {"APPROVED", "REJECTED", "REVISION_REQUESTED"}:
            raise ValueError(
                f"Invalid decision '{request.decision}'. "
                "Must be one of: APPROVED, REJECTED, REVISION_REQUESTED"
            )

        config = {"configurable": {"thread_id": thread_id}}

        # Verify the graph is actually paused at human_review
        state_snap = self.app.get_state(config)
        if not state_snap or not state_snap.values:
            raise ValueError(f"No active graph state found for thread_id='{thread_id}'")

        current_state: AgentState = state_snap.values.get("state")
        if current_state is None:
            raise ValueError("Invalid graph state structure.")

        if not state_snap.next or "human_review" not in state_snap.next:
            raise ValueError(
                "Graph is not pending human review. "
                f"Current state: human_approval_state='{current_state.human_approval_state}', "
                f"next={state_snap.next}"
            )

        # Persist the human decision (with immutability enforcement in repository)
        approval_svc = ApprovalService(get_approval_repository())

        # Extract incident_id — thread_id must NEVER become optimization_run_id
        incident_id = "UNKNOWN"
        if current_state.incident_candidates:
            cand = current_state.incident_candidates[0]
            incident_id = cand.get("incident_id") if isinstance(cand, dict) else getattr(cand, "incident_id", "UNKNOWN")

        # optimization_run_id comes from state.run_id only — never from thread_id
        approval_svc.record_approval(
            incident_id=incident_id,
            optimization_run_id=current_state.run_id,  # may be None — that's correct
            decision=request.decision,
            reason=request.reason,
            reviewer_id="API_USER"  # Placeholder; real auth deferred per design
        )

        # Inject the decision into the graph state at the SAME checkpoint
        updated_agent_state = current_state.model_copy(update={
            "human_approval_state": request.decision,
            "human_feedback": request.reason
        })
        self.app.update_state(config, {"state": updated_agent_state})

        # Resume the SAME graph execution (invoke with None input)
        result = self.app.invoke(None, config=config)

        if result is None:
            state_snap2 = self.app.get_state(config)
            final_state: AgentState = state_snap2.values.get("state") if state_snap2 else None
        else:
            final_state: AgentState = result.get("state")

        if not final_state:
            raise ValueError("Graph did not return valid state after resume.")

        status = "APPROVED" if request.decision == "APPROVED" else request.decision

        return AgentRunResponse(
            run_id=final_state.run_id,
            status=status,
            human_approval_state=final_state.human_approval_state,
            errors=final_state.errors
        )

    def execute_agent(self, thread_id: str, request: Optional["ExecutionRequest"] = None) -> "ExecutionResponse":
        """
        Trigger execution of an approved proposal for a specific workflow thread_id.

        SAFETY:
        - Resolves workflow thread_id to state.run_id and incident_id.
        - Delegates execution to ExecutionService, which authoritatively checks PERSISTED approval in DB.
        - thread_id is NEVER used as execution_id or optimization_run_id.
        """
        from app.api.schemas.internal import ExecutionRequest, ExecutionResponse
        from app.services.execution_service import ExecutionService
        from app.db.dependencies import (
            get_approval_repository,
            get_allocation_repository,
            get_resource_repository,
            get_action_repository
        )

        config = {"configurable": {"thread_id": thread_id}}
        state_snap = self.app.get_state(config)

        run_id = None
        incident_id = None
        if state_snap and state_snap.values:
            st: AgentState = state_snap.values.get("state")
            if st:
                run_id = st.run_id
                if st.incident_candidates:
                    cand = st.incident_candidates[0]
                    incident_id = cand.get("incident_id") if isinstance(cand, dict) else getattr(cand, "incident_id", None)

        exec_req = ExecutionRequest(
            optimization_run_id=request.optimization_run_id if (request and request.optimization_run_id) else run_id,
            incident_id=request.incident_id if (request and request.incident_id) else incident_id,
            executor_id=request.executor_id if request else None
        )

        exec_svc = ExecutionService(
            approval_repo=get_approval_repository(),
            allocation_repo=get_allocation_repository(),
            resource_repo=get_resource_repository(),
            action_repo=get_action_repository()
        )

        return exec_svc.execute_proposal(exec_req)

    def reassess_agent(self, thread_id: str, request: "ReassessmentRequest") -> "ReassessmentResponse":
        """
        Submits new reports/evidence to reassess an existing incident workflow.

        CORRECTIONS ENFORCED:
        - New reports are appended to existing incident state.
        - Previous assessment is preserved; a new assessment snapshot is created.
        - Assessment comparison & Allocation delta computed deterministically.
        - Zero automatic inventory mutation. Reallocations require human approval.
        """
        from app.api.schemas.internal import ReassessmentRequest, ReassessmentResponse, AssessmentDiff, AllocationDiff

        config = {"configurable": {"thread_id": thread_id}}
        state_snap = self.app.get_state(config)
        if not state_snap or not state_snap.values:
            raise ValueError(f"No active graph state found for thread_id='{thread_id}'")

        current_state: AgentState = state_snap.values.get("state")
        if not current_state:
            raise ValueError("Invalid graph state structure.")

        # Update state with new reports and reassessment flags
        updated_reports = list(current_state.raw_reports)
        if request.new_reports:
            updated_reports.extend(request.new_reports)

        parent_ass_id = current_state.current_assessment_id
        if not parent_ass_id and current_state.incident_candidates:
            cand = current_state.incident_candidates[0]
            inc_id = cand.get("incident_id") if isinstance(cand, dict) else getattr(cand, "incident_id", None)
            if inc_id:
                from app.db.dependencies import get_assessment_repository
                latest = get_assessment_repository().get_latest_for_incident(inc_id)
                if latest:
                    parent_ass_id = latest.assessment_id

        updated_state = current_state.model_copy(update={
            "raw_reports": updated_reports,
            "reassessment_requested": True,
            "parent_assessment_id": parent_ass_id,
            "reassessment_reason": request.reassessment_reason,
            "human_approval_state": "PENDING"
        })

        if request.run_id:
            updated_state.run_id = request.run_id
        else:
            updated_state.run_id = f"realloc-{uuid.uuid4().hex[:8]}"

        self.app.update_state(config, {"state": updated_state})
        result = self.app.invoke({"state": updated_state}, config=config)

        if result is None:
            state_snap2 = self.app.get_state(config)
            final_state: AgentState = state_snap2.values.get("state") if state_snap2 else None
            is_interrupted = state_snap2 and state_snap2.next
        else:
            final_state: AgentState = result.get("state")
            is_interrupted = False

        if not final_state:
            raise ValueError("Graph did not return valid state after reassessment.")

        cand = final_state.incident_candidates[0] if final_state.incident_candidates else None
        inc_id = cand.get("incident_id") if isinstance(cand, dict) else (getattr(cand, "incident_id", None) if cand else None)
        status = "COMPLETED"
        if is_interrupted or final_state.human_approval_state == "PENDING":
            if final_state.reallocation_required:
                status = "PENDING_REVIEW"
            else:
                status = "NO_REALLOCATION_REQUIRED"

        ass_diff = AssessmentDiff(**final_state.assessment_diff) if final_state.assessment_diff else None
        alloc_diff = AllocationDiff(**final_state.allocation_diff) if final_state.allocation_diff else None

        return ReassessmentResponse(
            run_id=final_state.run_id,
            thread_id=thread_id,
            incident_id=inc_id,
            previous_assessment_id=final_state.parent_assessment_id,
            current_assessment_id=final_state.current_assessment_id,
            assessment_diff=ass_diff,
            reallocation_decision_status=final_state.reallocation_decision_status,
            reallocation_required=final_state.reallocation_required,
            new_optimization_run_id=final_state.run_id if final_state.reallocation_required else None,
            allocation_diff=alloc_diff,
            human_approval_state=final_state.human_approval_state,
            status=status,
            errors=final_state.errors
        )


