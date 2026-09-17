import uuid
import logging
from typing import Optional

from ml.src.agents.graph import build_graph, GraphState
from ml.src.agents.state import AgentState
from app.api.schemas.internal import (
    AgentRunRequest,
    AgentRunResponse,
    AgentResumeRequest,
)

logger = logging.getLogger(__name__)

_shared_graph_app = None


def get_shared_graph_app():
    global _shared_graph_app

    if _shared_graph_app is None:
        _shared_graph_app = build_graph()

    return _shared_graph_app


class AgentService:

    def __init__(self, app=None):
        """
        Reuse the shared LangGraph application.

        The graph itself owns the MemorySaver checkpointer.
        """
        self.app = (
            app
            if app is not None
            else get_shared_graph_app()
        )

    # =========================================================
    # RUN AGENT
    # =========================================================

    def run_agent(
        self,
        request: AgentRunRequest,
    ) -> AgentRunResponse:

        try:

            incident = None

            # -------------------------------------------------
            # 1. Resolve requested incident
            # -------------------------------------------------

            if request.incident_id:

                from app.db.dependencies import (
                    get_incident_repository,
                )

                inc_repo = (
                    get_incident_repository()
                )

                incident = inc_repo.get(
                    request.incident_id
                )

                if not incident:
                    raise ValueError(
                        f"Incident with ID "
                        f"{request.incident_id} not found"
                    )

                # -------------------------------------------------
                # If no new reports were supplied, hydrate the
                # graph with the persisted incident's reports.
                # -------------------------------------------------

                if not request.raw_reports:

                    report_ids = (
                        incident.report_ids
                    )

                    hydrated_raw = []

                    if report_ids:

                        from app.db.client import (
                            get_supabase_client,
                        )

                        import json

                        client = (
                            get_supabase_client()
                        )

                        try:

                            rep_res = (
                                client
                                .table("reports")
                                .select("*")
                                .in_(
                                    "report_id",
                                    report_ids,
                                )
                                .execute()
                            )

                            for r in rep_res.data:

                                raw_t = r.get(
                                    "raw_text"
                                )

                                # ---------------------------------
                                # Preserve original structured JSON
                                # when available.
                                # ---------------------------------

                                if (
                                    raw_t
                                    and isinstance(
                                        raw_t,
                                        str,
                                    )
                                    and raw_t.startswith(
                                        "{"
                                    )
                                ):

                                    hydrated_raw.append(
                                        raw_t
                                    )

                                else:

                                    payload = {

                                        "source":
                                            r.get(
                                                "source",
                                                "PERSISTED_REPORT",
                                            ),

                                        "source_record_id":
                                            r.get(
                                                "source_record_id",
                                                r.get(
                                                    "report_id"
                                                ),
                                            ),

                                        "hazard_type":
                                            r.get(
                                                "hazard_type",
                                                incident.hazard_type,
                                            ),

                                        "location":
                                            r.get(
                                                "location_name"
                                            ),

                                        "latitude":
                                            r.get(
                                                "latitude"
                                            ),

                                        "longitude":
                                            r.get(
                                                "longitude"
                                            ),

                                        "affected_population":
                                            r.get(
                                                "affected_population"
                                            ),

                                        "magnitude":
                                            r.get(
                                                "magnitude"
                                            ),

                                        "wind_speed":
                                            r.get(
                                                "wind_speed"
                                            ),

                                        "pressure":
                                            r.get(
                                                "pressure"
                                            ),

                                        "depth":
                                            r.get(
                                                "depth"
                                            ),
                                    }

                                    hydrated_raw.append(
                                        json.dumps(
                                            payload
                                        )
                                    )

                        except Exception as ex:

                            logger.warning(
                                "Failed to fetch reports "
                                "for incident %s: %s",
                                request.incident_id,
                                ex,
                            )

                    # -------------------------------------------------
                    # If no persisted reports were available, create
                    # a minimal report from the canonical incident.
                    # -------------------------------------------------

                    if not hydrated_raw:

                        import json

                        payload = {

                            "source":
                                "PERSISTED_INCIDENT",

                            "source_record_id":
                                incident.incident_id,

                            "hazard_type":
                                incident.hazard_type,

                            "latitude":
                                incident.centroid_latitude,

                            "longitude":
                                incident.centroid_longitude,
                        }

                        hydrated_raw.append(
                            json.dumps(
                                payload
                            )
                        )

                    request.raw_reports = (
                        hydrated_raw
                    )

            # -------------------------------------------------
            # 2. Determine thread ID and run ID
            # -------------------------------------------------

            if request.run_id is not None:

                thread_id = request.run_id
                run_id = request.run_id

            else:

                run_id = None
                thread_id = (
                    f"thread-{uuid.uuid4()}"
                )

            # -------------------------------------------------
            # 3. Setup initial graph state
            #
            # target_incident_id is the AUTHORITATIVE identity.
            #
            # incident_candidates remains the mutable candidate
            # representation used by the detection pipeline.
            # -------------------------------------------------

            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }

            initial_state = AgentState(

                run_id=run_id,

                target_incident_id=(
                    incident.incident_id
                    if incident
                    else None
                ),

                raw_reports=
                    request.raw_reports,

                incident_candidates=(
                    [incident.model_dump()]
                    if incident
                    else []
                ),
            )

            # -------------------------------------------------
            # 4. Invoke LangGraph
            # -------------------------------------------------

            result = self.app.invoke(
                {
                    "state": initial_state
                },
                config=config,
            )

            # -------------------------------------------------
            # 5. Read checkpoint state
            # -------------------------------------------------

            state_snap = (
                self.app.get_state(
                    config
                )
            )

            is_interrupted = bool(
                state_snap
                and state_snap.next
            )

            if (
                result
                and "state" in result
            ):

                final_state: AgentState = (
                    result.get("state")
                )

            elif (
                state_snap
                and state_snap.values
            ):

                final_state: AgentState = (
                    state_snap.values.get(
                        "state"
                    )
                )

            else:

                final_state = None

            if not final_state:

                raise ValueError(
                    "Graph did not return "
                    "a valid state."
                )

            # -------------------------------------------------
            # 6. Determine workflow status
            # -------------------------------------------------

            status = "COMPLETED"

            if (
                final_state.verification_status
                == "REJECTED"
            ):

                status = "REJECTED"

            elif (
                is_interrupted
                or (
                    final_state.human_approval_state
                    == "PENDING"
                    and final_state.allocation_result
                )
            ):

                status = "PENDING_REVIEW"

            # -------------------------------------------------
            # 7. Return safe response
            # -------------------------------------------------

            errors = list(
                final_state.errors
            )

            return AgentRunResponse(

                thread_id=thread_id,

                run_id=final_state.run_id,

                status=status,

                human_approval_state=
                    final_state.human_approval_state,

                errors=errors,
            )

        except Exception as e:

            logger.error(
                "Agent execution failed: %s",
                e,
            )

            # Never expose secrets or stack traces.

            return AgentRunResponse(

                thread_id=request.run_id,

                run_id=request.run_id,

                status="FAILED",

                human_approval_state=
                    "PENDING",

                errors=[
                    "Internal graph execution error: "
                    f"{type(e).__name__}"
                ],
            )

    # =========================================================
    # SUBMIT HUMAN REVIEW
    # =========================================================

    def submit_review(
        self,
        thread_id: str,
        request: AgentResumeRequest,
    ) -> AgentRunResponse:

        """
        Resume a paused graph execution after human review.

        Safety guarantees:
        - Only resumes an active human-review checkpoint.
        - Persists the human decision before resuming.
        - Never re-runs optimization, severity, or ML manually.
        - Never mutates ResourceRepository directly.
        - thread_id never becomes optimization_run_id.
        """

        from app.db.dependencies import (
            get_approval_repository,
        )

        from app.services.approval_service import (
            ApprovalService,
        )

        # -------------------------------------------------
        # 1. Validate decision
        # -------------------------------------------------

        if request.decision not in {
            "APPROVED",
            "REJECTED",
            "REVISION_REQUESTED",
        }:

            raise ValueError(
                f"Invalid decision "
                f"'{request.decision}'. "
                "Must be one of: "
                "APPROVED, REJECTED, "
                "REVISION_REQUESTED"
            )

        # -------------------------------------------------
        # 2. Resolve checkpoint
        # -------------------------------------------------

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state_snap = (
            self.app.get_state(
                config
            )
        )

        if (
            not state_snap
            or not state_snap.values
        ):

            raise ValueError(
                "No active graph state found "
                f"for thread_id='{thread_id}'"
            )

        current_state: AgentState = (
            state_snap.values.get(
                "state"
            )
        )

        if current_state is None:

            raise ValueError(
                "Invalid graph state structure."
            )

        # -------------------------------------------------
        # 3. Verify graph is actually paused
        # -------------------------------------------------

        if (
            not state_snap.next
            or "human_review"
            not in state_snap.next
        ):

            raise ValueError(
                "Graph is not pending human review. "
                f"Current state: "
                f"human_approval_state="
                f"'{current_state.human_approval_state}', "
                f"next={state_snap.next}"
            )

        # -------------------------------------------------
        # 4. Resolve canonical incident identity
        #
        # target_incident_id is authoritative.
        # Fallback to candidate only for legacy checkpoints
        # created before target_incident_id existed.
        # -------------------------------------------------

        incident_id = (
            current_state.target_incident_id
        )

        if not incident_id:

            if current_state.incident_candidates:

                cand = (
                    current_state
                    .incident_candidates[0]
                )

                incident_id = (
                    cand.get(
                        "incident_id"
                    )
                    if isinstance(
                        cand,
                        dict,
                    )
                    else getattr(
                        cand,
                        "incident_id",
                        None,
                    )
                )

        if not incident_id:

            raise ValueError(
                "Unable to resolve canonical "
                "incident identity for review."
            )

        # -------------------------------------------------
        # 5. Persist human decision
        # -------------------------------------------------

        approval_svc = (
            ApprovalService(
                get_approval_repository()
            )
        )

        approval_svc.record_approval(

            incident_id=
                incident_id,

            optimization_run_id=
                current_state.run_id,

            thread_id=
                thread_id,

            decision=
                request.decision,

            reason=
                request.reason,

            reviewer_id=
                "API_USER",
        )

        # -------------------------------------------------
        # 6. Inject human decision into SAME graph state
        # -------------------------------------------------

        updated_agent_state = (
            current_state.model_copy(
                update={
                    "human_approval_state":
                        request.decision,

                    "human_feedback":
                        request.reason,
                }
            )
        )

        self.app.update_state(
            config,
            {
                "state":
                    updated_agent_state
            },
        )

        # -------------------------------------------------
        # 7. Resume SAME checkpoint
        # -------------------------------------------------

        result = self.app.invoke(
            None,
            config=config,
        )

        if result is None:

            state_snap2 = (
                self.app.get_state(
                    config
                )
            )

            final_state: AgentState = (
                state_snap2.values.get(
                    "state"
                )
                if state_snap2
                else None
            )

        else:

            final_state: AgentState = (
                result.get("state")
            )

        if not final_state:

            raise ValueError(
                "Graph did not return valid "
                "state after resume."
            )

        # -------------------------------------------------
        # 8. Response
        # -------------------------------------------------

        status = (
            "APPROVED"
            if request.decision
            == "APPROVED"
            else request.decision
        )

        return AgentRunResponse(

            thread_id=
                thread_id,

            run_id=
                final_state.run_id,

            status=
                status,

            human_approval_state=
                final_state.human_approval_state,

            errors=
                final_state.errors,
        )

    # =========================================================
    # EXECUTE APPROVED AGENT PROPOSAL
    # =========================================================

    def execute_agent(
        self,
        thread_id: str,
        request: Optional["ExecutionRequest"] = None,
    ) -> "ExecutionResponse":

        """
        Execute an approved proposal for a specific graph thread.

        Safety:
        - Resolves thread_id to graph state.
        - Resolves optimization_run_id from graph state.
        - Resolves incident_id from target_incident_id.
        - ExecutionService independently validates persisted
          approval before changing inventory.
        - thread_id is never used as optimization_run_id.
        """

        from app.api.schemas.internal import (
            ExecutionRequest,
            ExecutionResponse,
        )

        from app.services.execution_service import (
            ExecutionService,
        )

        from app.db.dependencies import (
            get_approval_repository,
            get_allocation_repository,
            get_resource_repository,
            get_action_repository,
        )

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        state_snap = (
            self.app.get_state(
                config
            )
        )

        run_id = None
        incident_id = None

        if (
            state_snap
            and state_snap.values
        ):

            st: AgentState = (
                state_snap.values.get(
                    "state"
                )
            )

            if st:

                run_id = st.run_id

                # ---------------------------------------------
                # Canonical incident identity first.
                # ---------------------------------------------

                incident_id = (
                    st.target_incident_id
                )

                # ---------------------------------------------
                # Legacy fallback.
                # ---------------------------------------------

                if not incident_id:

                    if st.incident_candidates:

                        cand = (
                            st.incident_candidates[0]
                        )

                        incident_id = (
                            cand.get(
                                "incident_id"
                            )
                            if isinstance(
                                cand,
                                dict,
                            )
                            else getattr(
                                cand,
                                "incident_id",
                                None,
                            )
                        )

        exec_req = ExecutionRequest(

            optimization_run_id=(
                request.optimization_run_id
                if (
                    request
                    and request.optimization_run_id
                )
                else run_id
            ),

            incident_id=(
                request.incident_id
                if (
                    request
                    and request.incident_id
                )
                else incident_id
            ),

            executor_id=(
                request.executor_id
                if request
                else None
            ),
        )

        exec_svc = ExecutionService(

            approval_repo=
                get_approval_repository(),

            allocation_repo=
                get_allocation_repository(),

            resource_repo=
                get_resource_repository(),

            action_repo=
                get_action_repository(),
        )

        return (
            exec_svc.execute_proposal(
                exec_req
            )
        )

    # =========================================================
    # REASSESS EXISTING INCIDENT
    # =========================================================

    def reassess_agent(
        self,
        thread_id: str,
        request: "ReassessmentRequest",
    ) -> "ReassessmentResponse":

        """
        Submit new evidence for reassessment of an existing
        incident workflow.

        Guarantees:
        - Existing incident identity is preserved.
        - New reports are appended.
        - Previous assessment remains immutable.
        - New assessment snapshot is created.
        - Assessment comparison is deterministic.
        - Allocation delta is deterministic.
        - No automatic inventory mutation.
        - Reallocation requires human approval.
        """

        from app.api.schemas.internal import (
            ReassessmentRequest,
            ReassessmentResponse,
            AssessmentDiff,
            AllocationDiff,
        )

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # -------------------------------------------------
        # 1. Resolve existing graph state
        # -------------------------------------------------

        state_snap = (
            self.app.get_state(
                config
            )
        )

        if (
            not state_snap
            or not state_snap.values
        ):

            raise ValueError(
                "No active graph state found "
                f"for thread_id='{thread_id}'"
            )

        current_state: AgentState = (
            state_snap.values.get(
                "state"
            )
        )

        if not current_state:

            raise ValueError(
                "Invalid graph state structure."
            )

        # -------------------------------------------------
        # 2. Preserve canonical incident ID
        # -------------------------------------------------

        incident_id = (
            current_state.target_incident_id
        )

        # Legacy fallback for older checkpoints.

        if not incident_id:

            if current_state.incident_candidates:

                cand = (
                    current_state
                    .incident_candidates[0]
                )

                incident_id = (
                    cand.get(
                        "incident_id"
                    )
                    if isinstance(
                        cand,
                        dict,
                    )
                    else getattr(
                        cand,
                        "incident_id",
                        None,
                    )
                )

        if not incident_id:

            raise ValueError(
                "Unable to resolve canonical "
                "incident identity for reassessment."
            )

        # -------------------------------------------------
        # 3. Append new reports
        # -------------------------------------------------

        updated_reports = list(
            current_state.raw_reports
        )

        if request.new_reports:

            updated_reports.extend(
                request.new_reports
            )

        # -------------------------------------------------
        # 4. Resolve parent assessment
        # -------------------------------------------------

        parent_ass_id = (
            current_state.current_assessment_id
        )

        if not parent_ass_id:

            from app.db.dependencies import (
                get_assessment_repository,
            )

            latest = (
                get_assessment_repository()
                .get_latest_for_incident(
                    incident_id
                )
            )

            if latest:

                parent_ass_id = (
                    latest.assessment_id
                )

        # -------------------------------------------------
        # 5. Create reassessment state
        # -------------------------------------------------

        updated_state = (
            current_state.model_copy(
                update={

                    "target_incident_id":
                        incident_id,

                    "raw_reports":
                        updated_reports,

                    "reassessment_requested":
                        True,

                    "parent_assessment_id":
                        parent_ass_id,

                    "reassessment_reason":
                        request.reassessment_reason,

                    "human_approval_state":
                        "PENDING",
                }
            )
        )

        # -------------------------------------------------
        # 6. Generate reassessment run ID
        # -------------------------------------------------

        if request.run_id:

            updated_state.run_id = (
                request.run_id
            )

        else:

            updated_state.run_id = (
                f"realloc-{uuid.uuid4().hex[:8]}"
            )

        # -------------------------------------------------
        # 7. Update checkpoint
        # -------------------------------------------------

        self.app.update_state(
            config,
            {
                "state":
                    updated_state
            },
        )

        # -------------------------------------------------
        # 8. Resume graph
        # -------------------------------------------------

        result = self.app.invoke(
            {
                "state":
                    updated_state
            },
            config=config,
        )

        if result is None:

            state_snap2 = (
                self.app.get_state(
                    config
                )
            )

            final_state: AgentState = (
                state_snap2.values.get(
                    "state"
                )
                if state_snap2
                else None
            )

            is_interrupted = (
                state_snap2
                and state_snap2.next
            )

        else:

            final_state: AgentState = (
                result.get("state")
            )

            is_interrupted = False

        if not final_state:

            raise ValueError(
                "Graph did not return valid "
                "state after reassessment."
            )

        # -------------------------------------------------
        # 9. Resolve canonical incident ID from final state
        # -------------------------------------------------

        inc_id = (
            final_state.target_incident_id
        )

        if not inc_id:

            cand = (
                final_state.incident_candidates[0]
                if final_state.incident_candidates
                else None
            )

            inc_id = (
                cand.get("incident_id")
                if isinstance(
                    cand,
                    dict,
                )
                else (
                    getattr(
                        cand,
                        "incident_id",
                        None,
                    )
                    if cand
                    else None
                )
            )

        # -------------------------------------------------
        # 10. Determine status
        # -------------------------------------------------

        status = "COMPLETED"

        if (
            is_interrupted
            or final_state.human_approval_state
            == "PENDING"
        ):

            if final_state.reallocation_required:

                status = (
                    "PENDING_REVIEW"
                )

            else:

                status = (
                    "NO_REALLOCATION_REQUIRED"
                )

        # -------------------------------------------------
        # 11. Serialize diffs
        # -------------------------------------------------

        ass_diff = (
            AssessmentDiff(
                **final_state.assessment_diff
            )
            if final_state.assessment_diff
            else None
        )

        alloc_diff = (
            AllocationDiff(
                **final_state.allocation_diff
            )
            if final_state.allocation_diff
            else None
        )

        # -------------------------------------------------
        # 12. Return reassessment response
        # -------------------------------------------------

        return ReassessmentResponse(

            run_id=
                final_state.run_id,

            thread_id=
                thread_id,

            incident_id=
                inc_id,

            previous_assessment_id=
                final_state.parent_assessment_id,

            current_assessment_id=
                final_state.current_assessment_id,

            assessment_diff=
                ass_diff,

            reallocation_decision_status=
                final_state.reallocation_decision_status,

            reallocation_required=
                final_state.reallocation_required,

            new_optimization_run_id=(
                final_state.run_id
                if final_state.reallocation_required
                else None
            ),

            allocation_diff=
                alloc_diff,

            human_approval_state=
                final_state.human_approval_state,

            status=
                status,

            errors=
                final_state.errors,
        )