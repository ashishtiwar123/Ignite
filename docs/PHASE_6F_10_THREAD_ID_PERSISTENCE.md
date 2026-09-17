# Phase 6F.10 — Persist LangGraph thread_id in Governance

## Executive Summary

Phase 6F.10 fixes governance persistence for the LangGraph `thread_id`. While Phase 6F.9 corrected the identity contract between `thread_id` and `optimization_run_id`, governance lookup (`GET /incidents/{incident_id}/governance`) previously returned `thread_id: null` because `SupabaseApprovalRepository.upsert()` omitted `thread_id` from the PostgREST upsert payload prior to table migration.

This phase establishes full database persistence for `thread_id` in the `approvals` table, updates repository serialization, enforces `thread_id` preservation across human review decision state transitions (`PENDING` -> `APPROVED` / `REJECTED` / `REVISION_REQUESTED`), and documents the technical boundary between persisted governance identities vs process-local LangGraph checkpointers.

---

## Technical Distinction: Governance Identity vs Checkpoint Memory

> [!IMPORTANT]
> - **THREAD_ID PERSISTENCE**: The actual `thread_id` passed to LangGraph during graph invocation is now durably stored in the `approvals` table (`thread_id TEXT NULL`). `GET /incidents/{incident_id}/governance` reliably returns this `thread_id` alongside `optimization_run_id` across server reboots.
> - **THREAD_ID CHECKPOINT PERSISTENCE**: `MemorySaver` checkpointer is **process-local / in-memory**. Restarting the FastAPI process preserves the `thread_id` governance record in Supabase, but clears the in-memory graph state. If a process restart occurs while a proposal is `PENDING`, the governance endpoint returns `thread_id: "thread-..."` (governance thread identity persisted = YES), but graph resume will return `No active graph state found` (LangGraph checkpoint available = NO).
> - **No Fake Sessions**: Uncheckpointed sessions or legacy approval records with `thread_id = NULL` are returned as `null` without fabricating fake IDs or substituting `optimization_run_id`.

---

## Architectural & Code Changes

### 1. Database Schema Migration
- **`supabase/migrations/008_approval_thread_id.sql`**:
  ```sql
  ALTER TABLE public.approvals ADD COLUMN IF NOT EXISTS thread_id TEXT NULL;
  CREATE INDEX IF NOT EXISTS idx_approvals_thread_id ON public.approvals(thread_id);
  ```

### 2. Supabase Approval Repository
- **`backend/app/db/supabase_approval_repository.py`**:
  Updated `upsert()` to include `thread_id` directly in the PostgREST payload. Added a fallback to strip `thread_id` if executed against a legacy remote DB instance missing column `008`.

### 3. Approval Service State Transitions
- **`backend/app/services/approval_service.py`**:
  Updated `record_approval()` to search for an existing `PENDING` `ApprovalRecord` by `optimization_run_id` or `incident_id`. When transitioning from `PENDING` -> `APPROVED` / `REJECTED` / `REVISION_REQUESTED`, `record_approval()` reuses the existing `approval_id` and preserves `thread_id=thread_id or existing.thread_id`.

### 4. Authoritative PENDING Approval Creation
- **`ml/src/agents/graph.py`**:
  In `optimization_node`, `thread_id` is extracted from the invocation `config` (`config.get("configurable", {}).get("thread_id")`) and passed to `ApprovalRecord(..., thread_id=thread_id, status="PENDING")`.

---

## Verification & Test Results

### 1. Focused Unit Test Suite (`backend/tests/test_phase6f9_thread_id_contract.py`)
- `test_agents_run_returns_actual_thread_id_and_separate_optimization_run_id`: **PASSED**
- `test_caller_supplied_run_id_semantics_preserved`: **PASSED**
- `test_wrong_optimization_run_id_cannot_be_used_as_thread_id`: **PASSED**
- `test_langgraph_resume_uses_exact_thread_id`: **PASSED**
- `test_governance_returns_persisted_thread_id`: **PASSED**
- `test_approval_transition_preserves_thread_id`: **PASSED**
- `test_governance_returns_null_thread_id_for_old_records`: **PASSED**
- `test_execution_uses_correct_identity_and_prevents_unapproved_opt_id`: **PASSED**

Result: **8/8 PASSED**

### 2. Full Regression Suites
- Backend Pytest Suite: **82/82 PASSED**
- Frontend Production Build (`npm run build --prefix frontend`): **SUCCESS**

### 3. Real Live Verification Evidence
Live verification script (`scratch/verify_phase6f9_live.py`) executed against running FastAPI server (`http://localhost:8001`):

```json
1. POST /agents/run
   AgentRunResponse: {
     "thread_id": "thread-4037ede2-4b7c-453e-9c19-58062cd74d1a",
     "run_id": null,
     "status": "PENDING_REVIEW",
     "human_approval_state": "PENDING"
   }

2. GET /incidents/56862ef4-18f4-4bfc-bcf6-795850362551/governance
   Governance Response: {
     "incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551",
     "optimization_run_id": "opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd",
     "thread_id": "thread-4037ede2-4b7c-453e-9c19-58062cd74d1a",
     "approval_status": "PENDING",
     "execution_status": "UNEXECUTED",
     "approval_id": "567b6e33-0d79-46f6-b74e-6de8f9d80df0"
   }

3. POST /agents/review/opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd
   Response (400 Bad Request):
   "No active graph state found for thread_id='opt-b48a0315-3b45-4b43-94e1-728d4e8a04cd'"

4. POST /agents/review/thread-4037ede2-4b7c-453e-9c19-58062cd74d1a
   Response (200 OK):
   {
     "thread_id": "thread-4037ede2-4b7c-453e-9c19-58062cd74d1a",
     "status": "APPROVED",
     "human_approval_state": "APPROVED"
   }
```

---

## Final Checklist & Status

- [x] `thread_id` stored in Supabase PostgREST payload.
- [x] Governance endpoint `GET /incidents/{id}/governance` returns persisted `thread_id`.
- [x] Frontend receives and uses `governance.thread_id` for review calls.
- [x] Human approval resumes using exact `thread_id`.
- [x] `optimization_run_id` remains distinct proposal identifier.
- [x] Approval immutability and `thread_id` preservation across status transitions verified.
- [x] Older legacy records with `NULL` `thread_id` handled safely.
- [x] All unit & regression tests pass.
- [x] Frontend production build passes.
- [x] Process-local MemorySaver checkpoint limitation documented.

**FINAL STATUS: CLOSED**
