# Phase 4A LangGraph ↔ FastAPI Orchestration Foundation

## 1. Existing LangGraph Contract
The LangGraph orchestrator (`ml/src/agents/graph.py`) processes an `AgentState`. 
- **Nodes**: `report_intelligence`, `incident_detection`, `verification`, `situation_assessment`, `optimization`, `coordination`, `human_review`
- **Edges**: Deterministic paths with conditionals post-verification and post-optimization to handle rejections or infeasible allocations via `human_review`.
- **Checkpointer**: Uses `MemorySaver` which requires a `thread_id` for state persistence and replayability.

## 2. AgentState Contract
- Contains input `raw_reports` and execution identifier `run_id`.
- The `run_id` field is `Optional[str] = None`. It is explicitly passed through to ML subcomponents like `AllocationContext` without internal modification.

## 3. FastAPI Boundary
- The new `AgentService` (`backend/app/services/agent_service.py`) acts as a thin adapter between FastAPI endpoints and LangGraph invocation.
- It instantiates the graph (`build_graph()`) and configures thread state.
- **AgentRunRequest**: Defines `run_id: Optional[str] = None` and `raw_reports: list[str]`.
- **AgentRunResponse**: Returns `run_id`, `status`, `human_approval_state`, and `errors`.

## 4. Run ID and Thread ID Semantics
### Critical Distinction
- **run_id**: Represents the logical execution identity provided by the caller. It remains `None` if the caller did not supply one (non-idempotent execution).
- **thread_id**: A technical session/checkpoint identifier required by LangGraph `MemorySaver`.

### Isolation
- When no caller-provided `run_id` exists, a temporary UUID is generated solely as LangGraph MemorySaver `thread_id`. 
- This value is not an execution identity and must never propagate to `optimization_run_id` or other idempotency fields. `AgentState.run_id` remains `None`.

## 5. Checkpointing (MemorySaver Behavior)
- The existing `MemorySaver` is process-local and suitable for development/demo. 
- It is not durable across process restart. Persistent database checkpointing is reserved for a future phase.

## 6. Interrupt and Rejection Behavior
- **Interrupts**: If the graph routes to `human_review` (e.g., due to `NEEDS_VERIFICATION` or `INFEASIBLE` solver status), the state `human_approval_state` becomes `PENDING`. The service catches this and surfaces a response `status` of `INTERRUPTED`.
- **Rejections**: If the `verification_node` marks the `verification_status` as `REJECTED` (e.g., prompt injection detected), the service translates this to a `status` of `REJECTED`.

## 7. Error Handling
- Exceptions raised during graph execution are caught by `AgentService`.
- Stack traces or sensitive details are obfuscated. The response returns a generic `FAILED` status with the error class name.

## 8. Gemini Security
- Uses existing `GeminiAdapter`. The API key is securely loaded from `os.environ` and defaults to mock if missing. 
- The key is strictly confined to the adapter, never serialized into `AgentState`, and never leaked in API responses or logs.

## 9. API Endpoint
- **POST /agents/run** 
  - Defined in `backend/app/api/routes/agents.py`.
  - Maps to `AgentService.run_agent`.

## 10. Tests & Regression
- Tests explicitly cover `run_id` vs `thread_id` isolation to prevent regressions on idempotency rules.
- Run `pytest backend/tests -v` and `pytest ml/tests -v` to confirm regression integrity.

## 11. Limitations & Scope of Phase 4B
- **What is NOT Implemented in Phase 4A**:
  - Full report-to-incident database integration.
  - Dynamic reassessment persistence.
  - Persistent LangGraph checkpointing (SupabaseSaver).
  - Complete Human-in-the-loop (HITL) approval API workflows.
  - Real-time notifications and dynamic resource reallocation.
- Phase 4B will continue expanding upon this orchestration foundation to cover full end-to-end integration mapping.
