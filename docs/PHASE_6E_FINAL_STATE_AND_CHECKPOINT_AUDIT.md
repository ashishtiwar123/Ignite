# PS20 Phase 6E Audit: Final State, LangGraph Checkpoint & Reassessment Audit

**Date**: September 17, 2026  
**Component**: LangGraph Checkpointer (`graph.py`), Supabase Evidence Persistence (`supabase_repository.py`), Governance Projection Route (`incidents.py`), UI State Synchronization (`ApprovalExecutionPanel.tsx`)  
**Status**: **VERIFIED & OPERATIONAL** (All 5 Audit Issues Resolved, Zero State Inconsistencies, Production Build Green)

---

## 1. Executive Summary

Phase 6E performed a forensic audit and resolution of five specific runtime/state issues identified during final system testing:
1. **LangGraph Checkpoint Serialization Warning**: Silenced via explicit `JsonPlusSerializer` module allowlist configuration.
2. **React Hydration Warning (`fdprocessedid`)**: Proven to originate exclusively from browser autofill/password extension injection into form buttons prior to React hydration. Zero application code modifications required.
3. **Backend `POST /agents/review/run-demo-1` HTTP 400**: Diagnosed as intentional backend immutability protection. Resubmitting approval for a thread/run with an existing finalized approval record is blocked to prevent conflicting approval decisions.
4. **Duplicate Evidence Constraint Error During Reassessment**: Idempotency established by supplying `on_conflict="incident_id,report_id"` during Supabase upserts, retaining the `UNIQUE(incident_id, report_id)` database constraint.
5. **Approval / Execution State Inconsistency (`APPROVED` vs `NOT_APPROVED`)**: Resolved by introducing a strictly read-only governance projection endpoint `GET /incidents/{incident_id}/governance` that binds the UI directly to authoritative persisted Supabase database state, and correcting frontend error container rendering.

---

## 2. Forensic Audit Findings & Fixes

### Issue 1: LangGraph Checkpoint Warning
* **Classification**: **FIXED**
* **Root Cause**: `MemorySaver()` checkpointer in `ml/src/agents/graph.py` relied on default msgpack serializer options. When deserializing `AgentState` from checkpoint memory during graph interrupts, `JsonPlusSerializer` emitted a warning because `AgentState` was not in `SAFE_MSGPACK_TYPES`.
* **Verified Fix**: Verified against the active `langgraph.checkpoint` package API:
  ```python
  from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
  serde = JsonPlusSerializer(allowed_msgpack_modules=[("ml.src.agents.state", "AgentState")])
  memory = MemorySaver(serde=serde)
  ```
  Warning eliminated; interrupt/resume state integrity verified.

### Issue 2: React Hydration Warning (`fdprocessedid`)
* **Classification**: **BROWSER EXTENSION**
* **Root Cause**: The attribute `fdprocessedid` ("Form Data Processed ID") is injected dynamically into `<button>` and `<input>` elements by third-party browser extensions (e.g., McAfee WebAdvisor, Dashlane, 1Password) before React client hydration completes, causing a server/client DOM mismatch.
* **Verification**: Codebase search across `frontend/src` and `frontend/node_modules` confirmed 0 occurrences of `fdprocessedid`.
* **Action**: Documented per instructions. Zero application code modified.

### Issue 3: Review Endpoint 400 (`POST /agents/review/{thread_id}`)
* **Classification**: **ROOT CAUSE DIAGNOSED & VERIFIED**
* **Root Cause**:
  1. `AgentService.submit_review()` delegates to `ApprovalService.record_approval()`, which invokes `SupabaseApprovalRepository.upsert()`.
  2. Immutability rules in `SupabaseApprovalRepository` prohibit creating multiple conflicting approval records for the same `optimization_run_id`.
  3. When `POST /agents/review/run-demo-1` was called on a thread whose run ID already had a finalized decision in Supabase, the repository lawfully raised `ValueError("Cannot create a conflicting approval record for this optimization run.")`, which FastAPI returned as `HTTP 400 Bad Request`.
  4. Additionally, if the in-memory graph was not paused at `human_review` (or completed), `submit_review` raised `ValueError("Graph is not pending human review")` (HTTP 400).

### Issue 4: Duplicate Evidence Error During Reassessment
* **Classification**: **FIXED & IDEMPOTENT**
* **Root Cause**: In `SupabaseIncidentRepository.save()`, `incident_evidence` rows were persisted using `.upsert(evidence_data)` without specifying `on_conflict`. PostgREST defaulted to matching on the `evidence_id` primary key and generating a new UUID, triggering `duplicate key value violates unique constraint incident_evidence_incident_id_report_id_key` whenever reassessment re-processed existing reports.
* **Verified Fix**: Updated `supabase_repository.py`:
  ```python
  self.client.table("incident_evidence").upsert(evidence_data, on_conflict="incident_id,report_id").execute()
  ```
  Existing relationships perform an idempotent no-op without error; genuinely new evidence is appended. Database `UNIQUE(incident_id, report_id)` constraint remains strictly intact.

### Issue 5: Approval vs Execution UI State Inconsistency
* **Classification**: **FIXED**
* **Root Cause**:
  1. `ApprovalExecutionPanel.tsx` held local React state `approvalStatus = "APPROVED"` and rendered "Proposal Approved" / "Execution Gate Enabled".
  2. When the user clicked "Execute Allocation Proposal", `ExecutionService.execute_proposal` returned `status="NOT_APPROVED"` because either persisted approval was missing or `incident_id` sent from frontend (`backendIncidents[0]?.incident_id`) mismatched the approval's `incident_id` in Supabase.
  3. `ApprovalExecutionPanel` set `executionResult = res` and rendered `Execution Status: NOT_APPROVED` inside a green success box with `<CheckCircle2>`, creating the UI contradiction.
  4. Neither frontend nor backend had a read endpoint to fetch authoritative persisted approval/execution status.
* **Verified Fix**:
  1. **Read-Only Governance Endpoint**: Added `GET /incidents/{incident_id}/governance` in `backend/app/api/routes/incidents.py`. Performs pure `select` queries on `approvals` and `actions` tables with **zero** side-effects or mutations.
  2. **Authoritative Hydration**: `ApprovalExecutionPanel.tsx` fetches governance state from `GET /incidents/{incident_id}/governance` whenever `incidentId` changes.
  3. **Rejection Alert Rendering**: If `executionResult.status` is `NOT_APPROVED` or `FAILED`, the UI renders a prominent red alert box detailing the rejection reason instead of a green checkmark box.
  4. **Dynamic Selection Binding**: `dashboard.tsx` passes the active selected incident ID (`selected?.id || backendIncidents[0]?.incident_id`) to `ApprovalExecutionPanel`.

---

## 3. Files Changed

| File | Modification Description |
|---|---|
| `ml/src/agents/graph.py` | Configured `MemorySaver` checkpointer with `JsonPlusSerializer` allowlist for `AgentState`. |
| `backend/app/db/supabase_repository.py` | Added `on_conflict="incident_id,report_id"` to `incident_evidence` upsert in `SupabaseIncidentRepository.save()`. |
| `backend/app/db/approval_repository.py` | Added `get_by_incident` abstract/in-memory methods to `BaseApprovalRepository`. |
| `backend/app/db/supabase_approval_repository.py` | Added `get_by_incident` implementation to `SupabaseApprovalRepository`. |
| `backend/app/db/action_repository.py` | Added `get_by_incident` abstract/in-memory methods to `BaseActionRepository`. |
| `backend/app/db/supabase_action_repository.py` | Added `get_by_incident` implementation to `SupabaseActionRepository`. |
| `backend/app/api/schemas/responses.py` | Added `IncidentGovernanceResponse` Pydantic response schema. |
| `backend/app/api/routes/incidents.py` | Added strictly read-only `GET /incidents/{incident_id}/governance` endpoint. |
| `frontend/src/lib/api/types.ts` | Added `IncidentGovernanceResponse` frontend TypeScript interface. |
| `frontend/src/lib/api/agents.ts` | Added `getIncidentGovernance` API client function. |
| `frontend/src/components/dr/ApprovalExecutionPanel.tsx` | Hydrated state from backend governance API; updated execution rejection error box styling. |
| `frontend/src/routes/dashboard.tsx` | Bound `ApprovalExecutionPanel` to dynamically selected incident ID. |

---

## 4. Test & Verification Results

### Backend Test Suite
```bash
$env:PYTHONPATH="backend;."; pytest backend/tests
# 61 passed, 155 warnings in 26.36s (100% green)
```

### ML Test Suite
```bash
pytest ml/tests
# 186 passed in 185.61s (100% green)
```

### Frontend Production Build
```bash
npm run build --prefix frontend
# Built client in 6.15s
# Built SSR in 1.27s
# Generated Cloudflare worker Nitro bundle in 1.41s
# Build exit code: 0
```

---

## 5. Final Checklist & Sign-Off

1. **LangGraph Warning**: **FIXED** (Configured `JsonPlusSerializer(allowed_msgpack_modules=[("ml.src.agents.state", "AgentState")])`).
2. **Hydration Warning**: **BROWSER EXTENSION** (Verified attribute `fdprocessedid` is injected by browser extensions; 0 occurrences in application code; documented per instructions).
3. **Review 400**: **ROOT CAUSE DIAGNOSED** (Immutability guard blocks duplicate conflicting approval creation for finalized run IDs).
4. **Duplicate Evidence**: **FIXED & IDEMPOTENT** (Added `on_conflict="incident_id,report_id"`; constraint preserved; 0 duplicate key errors during reassessment).
5. **Approval/Execution Inconsistency**: **FIXED** (Added read-only `GET /incidents/{id}/governance` endpoint; frontend hydrates from Supabase; rejection errors render in alert box).
6. **Fresh End-to-End Approval/Execution Test**: **VERIFIED** (Persisted approval -> Execution gate enabled -> Controlled resource deduction in Supabase -> Action logged).
7. **Reassessment Test**: **VERIFIED** (Child assessment created with `parent_assessment_id`, new evidence linked idempotently, reallocation delta generated).
8. **Full Regression**: **PASSED** (247 total tests passed across backend and ML suites).
9. **Frontend Build**: **PASSED** (Exit code 0).
10. **Remaining Blockers**: **NONE**.
