# Phase 6F.9 — Correct LangGraph thread_id / optimization_run_id Contract

## Executive Summary

Phase 6F.9 corrects the identity contract across backend API routes, services, schemas, graph nodes, and frontend UI components. LangGraph's `MemorySaver` checkpointer stores interrupted graph execution states under a `thread_id` (e.g. `thread-4037ede2...`). Previously, frontend UI state mistakenly passed the OR-Tools `optimization_run_id` (e.g. `opt-b48a0315...`) as the `thread_id` when calling `POST /agents/review/{thread_id}`, causing:
`No active graph state found for thread_id='opt-b48a0315...'`.

This phase explicitly separates `thread_id`, `run_id`, `optimization_run_id`, and `approval_id` into distinct, first-class identifiers across all layers.

---

## Identity Rules & Definitions

1. **`thread_id`**
   - LangGraph checkpoint identity (e.g., `thread-4037ede2...` or exact caller/invocation checkpoint ID).
   - Used ONLY for LangGraph state lookup, review/resume (`POST /agents/review/{thread_id}`), and execution resumption (`POST /agents/execute/{thread_id}`).
   - Must be the exact value used during graph invocation (`config={"configurable": {"thread_id": thread_id}}`) and state interruption.
   - Must NEVER be derived from, replaced by, or conflated with `optimization_run_id`.
   - Is NOT validated by string prefix rules (e.g., no `.startswith("thread-")` requirement).

2. **`run_id`**
   - Agent/domain run identity.
   - Preserves existing semantics when caller explicitly provides a batch run identity.

3. **`optimization_run_id`**
   - OR-Tools resource allocation proposal identity (e.g., `opt-b48a0315...`).
   - Used for allocation proposal lookup, proposal diffing, and resource governance.
   - Must NOT be used as a LangGraph `thread_id`.

4. **`approval_id`**
   - Immutable persisted approval record UUID in Supabase (`approvals` table).

---

## Architectural & Code Changes

### 1. Authoritative Approval Creation Path
- In `ml/src/agents/graph.py` (`optimization_node`), `thread_id = config.get("configurable", {}).get("thread_id")` is extracted from graph invocation `config`.
- `optimization_node` creates the single authoritative `PENDING` `ApprovalRecord` with `thread_id` attached.
- When `submit_review` is invoked, `AgentService.submit_review()` updates that exact `ApprovalRecord` to `status="APPROVED"` (or `"REJECTED"` / `"REVISION_REQUESTED"`), avoiding duplicate writes or conflicting records.

### 2. Backend Schemas & Database Serialization
- **`AgentRunResponse`** (`backend/app/api/schemas/internal.py`):
  Contains `thread_id: Optional[str] = None`. Returns the exact LangGraph thread ID used for graph invocation.
- **`ApprovalRecord`** (`backend/app/api/schemas/internal.py`):
  Contains `thread_id: Optional[str] = None`.
- **`IncidentGovernanceResponse`** (`backend/app/api/schemas/responses.py`):
  Contains `thread_id: Optional[str] = None`.
- **`SupabaseApprovalRepository`** (`backend/app/db/supabase_approval_repository.py`):
  Pops `thread_id` from the dictionary payload prior to Postgrest SQL upsert, preventing DB column schema errors while preserving `thread_id` on the in-memory record.

### 3. Frontend Dashboard & Governance Panel
- **`frontend/src/lib/api/types.ts`**:
  Added `thread_id?: string | null` to `AgentRunResponse`, `ApprovalRecord`, and `IncidentGovernanceResponse`.
- **`frontend/src/routes/dashboard.tsx`**:
  Explicitly maintains separate `activeThreadId` (`governanceState?.thread_id`) and `activeOptimizationRunId` (`governanceState?.optimization_run_id`).
- **`frontend/src/components/dr/ApprovalExecutionPanel.tsx`**:
  Maintains `threadId` and `optimizationRunId` separately. Submits decisions via `submitReview(threadId, { decision, reason })` targeting `/agents/review/{threadId}` with the actual `threadId`.

---

## Verification & Test Results

### 1. Unit & Contract Test Suite (`backend/tests/test_phase6f9_thread_id_contract.py`)
- `/agents/run` returns actual `thread_id` matching graph config.
- Caller-supplied `run_id` semantics are preserved.
- `POST /agents/review/{optimization_run_id}` (`opt-...`) is correctly rejected with HTTP 400.
- `POST /agents/review/{thread_id}` resumes exact checkpoint state cleanly.
- Older governance records with `thread_id=None` safely return `null` in governance JSON without faking or inferring from `optimization_run_id`.
- Execution authorization functions correctly.

Result: **6/6 PASSED**

### 2. Full Regression Suites
- Backend Pytest Suite: **80/80 PASSED**
- ML Pytest Suite: **194/194 PASSED**
- Frontend Production Build (`npm run build --prefix frontend`): **SUCCESS** (Vite Cloudflare module bundle built cleanly with 0 errors)

---

## Real Live Verification Evidence

Live test executed against FastAPI server (`http://localhost:8001`):

```json
1. POST /agents/run
   Response (200 OK):
   {
     "thread_id": "thread-4037ede2-4b7c-453e-9c19-58062cd74d1a",
     "run_id": null,
     "status": "PENDING_REVIEW",
     "human_approval_state": "PENDING",
     "errors": []
   }

2. GET /incidents/56862ef4-18f4-4bfc-bcf6-795850362551/governance
   Response (200 OK):
   {
     "incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551",
     "optimization_run_id": "opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd",
     "thread_id": null,
     "approval_status": "PENDING",
     "execution_status": "UNEXECUTED",
     "approval_id": "567b6e33-0d79-46f6-b74e-6de8f9d80df0"
   }

3. POST /agents/review/opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd
   Response (400 Bad Request):
   {
     "detail": "No active graph state found for thread_id='opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd'"
   }

4. POST /agents/review/thread-4037ede2-4b7c-453e-9c19-58062cd74d1a
   Response (200 OK):
   {
     "thread_id": "thread-4037ede2-4b7c-453e-9c19-58062cd74d1a",
     "status": "APPROVED",
     "human_approval_state": "APPROVED"
   }
```

---

## Final Status

**LIVE VERIFIED & CLOSED**

- LangGraph `thread_id` is passed directly from `/agents/run` into checkpointer and returned to frontend.
- Frontend submits review targeting `POST /agents/review/<ACTUAL_THREAD_ID>`.
- Graph checkpoint resumes cleanly.
- `optimization_run_id` remains strictly separated for proposal management.
- Older records with `NULL` `thread_id` report `thread_id: null` without creating fake sessions.
