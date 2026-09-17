# Phase 4E — Human Review / Approval Integration

## 1. Objective

Implement a strict Human-in-the-Loop (HITL) governance boundary into the disaster-relief
LangGraph pipeline. After optimization, the system pauses and awaits explicit human authorization
before any execution occurs.

The Phase 4E output is:

```
AUTHORIZED_FOR_EXECUTION
```

NOT:

```
EXECUTED
```

Phase 4F owns actual execution.

---

## 2. Human-in-the-Loop Architecture

```
ALLOCATION PROPOSAL (Phase 4D)
          ↓
PENDING HUMAN REVIEW
          ↓
 ┌────────┼──────────────────────┐
 ↓        ↓                     ↓
APPROVED REJECTED   REVISION_REQUESTED
 ↓        ↓                     ↓
STOP     STOP                  STOP
```

Where `APPROVED` = `AUTHORIZED_FOR_EXECUTION`, **NOT** `EXECUTED`.

All three terminal states are persisted as immutable governance records in the `approvals` table.

---

## 3. State Machine

| State | Meaning |
|---|---|
| `PENDING` | Graph paused before `human_review_node` |
| `APPROVED` | Reviewer authorized the allocation proposal |
| `REJECTED` | Reviewer rejected the allocation proposal |
| `REVISION_REQUESTED` | Reviewer requested changes to the proposal |

Transitions:

```
(Start) → OPTIMIZATION → [INTERRUPT] → PENDING_REVIEW
PENDING → (human decision injected) → APPROVED / REJECTED / REVISION_REQUESTED
APPROVED / REJECTED / REVISION_REQUESTED → END
```

---

## 4. LangGraph Interruption Mechanism

The graph is compiled with:

```python
app = workflow.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"]
)
```

When optimization completes:
1. The graph pauses **before** executing `human_review_node`.
2. The checkpoint is stored in `MemorySaver` keyed by `thread_id`.
3. The API caller receives status `PENDING_REVIEW`.

---

## 5. Same-Checkpoint Resume Protocol

1. Caller receives `PENDING_REVIEW` from `POST /agents/run`.
2. Caller obtains `thread_id` (returned in context or stored from initial run).
3. Caller submits decision to `POST /agents/review/{thread_id}`.
4. `AgentService.submit_review()` verifies the graph is actually `PENDING`.
5. `ApprovalService.record_approval()` persists the governance record.
6. `app.update_state(config, {"state": updated_state})` injects the decision.
7. `app.invoke(None, config=config)` resumes the **same** checkpoint execution.
8. `human_review_node` routes to `END` based on the injected decision.

The same `thread_id` is used throughout. A new graph invocation is **never** created.

---

## 6. Approval Schema (`ApprovalRecord`)

```python
class ApprovalRecord(BaseModel):
    approval_id: str                    # UUID entity ID
    incident_id: str                    # References the incident
    optimization_run_id: Optional[str]  # Domain run_id (may be None)
    action_id: Optional[str]            # Optional action reference
    status: str                         # APPROVED / REJECTED / REVISION_REQUESTED
    reviewer_id: Optional[str]          # Reviewer identity (future: from auth)
    reason: Optional[str]              # Required for REJECTED/REVISION_REQUESTED
    decided_at: Optional[datetime]
    created_at: datetime
```

---

## 7. Approval Persistence

```
human_review_node
        ↓
AgentService.submit_review()
        ↓
ApprovalService.record_approval()
        ↓
InMemoryApprovalRepository / SupabaseApprovalRepository
        ↓
public.approvals (Supabase)
```

No SQL exists in `graph.py`. All persistence goes through the service → repository boundary.

---

## 8. Audit Events

Every approval decision creates an immutable `audit_events` row:

| Event Type | When |
|---|---|
| `APPROVAL_APPROVED` | Reviewer submits `APPROVED` |
| `APPROVAL_REJECTED` | Reviewer submits `REJECTED` |
| `APPROVAL_REVISION_REQUESTED` | Reviewer submits `REVISION_REQUESTED` |

Audit payload includes: `approval_id`, `incident_id`, `optimization_run_id`, `status`,
`reviewer_id`, `reason`, `decided_at`.

**Secrets are never logged.** API keys, Gemini credentials, and auth tokens are excluded.

---

## 9. Decision Semantics

### APPROVED
- Allocation proposal is authorized for execution.
- No execution occurs in Phase 4E.
- Approval record persisted as immutable.
- Audit event created.
- Status: `AUTHORIZED_FOR_EXECUTION` (not `EXECUTED`).

### REJECTED
- Proposal denied.
- No execution, no retry, no re-optimization.
- Rejection record persisted as immutable.
- Reason preserved.
- Audit event created.

### REVISION_REQUESTED
- Current approval cycle ends.
- No automatic re-optimization or inventory changes.
- Revision record persisted as immutable.
- Reason preserved.
- Audit event created.
- Future reassessment behavior belongs to Phase 4G.

---

## 10. Run ID vs Thread ID

| Concept | Value |
|---|---|
| `state.run_id` | Domain execution identity (may be `None`) |
| LangGraph `thread_id` | Checkpoint identity (required by MemorySaver) |
| `optimization_run_id` | Always equals `state.run_id` (never `thread_id`) |
| `approval_id` | New UUID per approval record |

Rules:
- If caller provides `run_id` → `thread_id = run_id`, `state.run_id = run_id`
- If caller provides no `run_id` → `thread_id = new UUID`, `state.run_id = None`
- `thread_id` **NEVER** becomes `optimization_run_id`, `incident_id`, `approval_id`, or any domain identity.

---

## 11. Approval Immutability

Once a decision is finalized (`APPROVED`, `REJECTED`, or `REVISION_REQUESTED`):
- The same record **cannot** be mutated to a different decision.
- A new conflicting finalized record for the same `optimization_run_id` is rejected.
- Identical re-submission of the exact same record is idempotent (no-op).

---

## 12. Reviewer Identity

Authentication is not yet implemented. Current default:

```
reviewer_id = "API_USER"
```

This is a known limitation documented below. Future implementation should populate `reviewer_id`
from the authenticated session.

---

## 13. Verification Gate

Only a `VERIFIED` incident with a valid allocation proposal reaches human approval:
- `NEEDS_VERIFICATION` → routed away before optimization; no allocation → no review
- `REJECTED` verification → routed to `END`; no allocation → no review

The API layer (`POST /agents/review/{thread_id}`) additionally validates that the graph
is actually paused before the `human_review` node before accepting a decision.

---

## 14. No-Execution Invariant

Human approval **NEVER** triggers:
- Inventory deduction
- Warehouse stock mutation
- Resource dispatch
- Transport routing
- Agency notification
- Field execution

This is enforced architecturally: `human_review_node` is a pure routing node. No write
operations against `ResourceRepository` occur in the Phase 4E execution path.

---

## 15. Security Boundary

| Layer | Authority |
|---|---|
| Human | Decision authority (APPROVE / REJECT / REVISION_REQUESTED) |
| Backend | Validates decision value, workflow identity, pending state |
| Graph | Injects decision into checkpoint state; resumes execution |
| LangGraph | Orchestrates the interrupt-resume lifecycle |
| Gemini | **Not involved in approval decisions** |
| ML engines | **Not involved in approval decisions** |

A Gemini-generated or LLM-generated approval is **impossible by architecture**: the
`human_review_node` is a pure pass-through that only reads the already-injected `human_approval_state`.

---

## 16. API Contract

### Run Agent
```
POST /agents/run
Body: { "run_id": "optional-domain-id", "raw_reports": ["..."] }
Response: { "run_id": "...", "status": "PENDING_REVIEW", "human_approval_state": "PENDING", "errors": [] }
```

### Submit Review Decision
```
POST /agents/review/{thread_id}
Body: { "decision": "APPROVED" | "REJECTED" | "REVISION_REQUESTED", "reason": "optional" }
Response: { "run_id": "...", "status": "APPROVED" | "REJECTED" | "REVISION_REQUESTED", "human_approval_state": "...", "errors": [] }
```

Error codes:
- `400` — Invalid decision value / workflow not in PENDING state / invalid workflow identity
- `500` — Internal error (no details exposed)

---

## 17. Repository Architecture

```
BaseApprovalRepository (ABC)
├── InMemoryApprovalRepository  ← used in tests / inmemory backend
└── SupabaseApprovalRepository  ← used in production (supabase backend)
```

Both implementations enforce:
1. Immutability for finalized decisions.
2. Conflict detection for duplicate decisions on the same `optimization_run_id`.
3. Idempotency for identical re-submission.

---

## 18. Database Migration

File: `supabase/migrations/005_approval_optimization_run_id.sql`

Changes:
- Added `optimization_run_id TEXT` column to `public.approvals`.
- Added index `idx_approvals_optimization_run_id`.

The `allocation_result` JSONB was **not** duplicated into `approvals`.
The stable reference is `optimization_run_id` which can be used to join `allocations`.

---

## 19. Tests

File: `ml/tests/test_phase4e_graph.py`

| # | Test | Scenario |
|---|---|---|
| 1 | `test_graph_interrupts_at_human_review` | Graph pauses before human_review |
| 2 | `test_pending_review_is_distinct_from_failed` | PENDING_REVIEW ≠ FAILED |
| 3 | `test_approval_resumes_same_checkpoint` | Same checkpoint resumed after APPROVED |
| 4 | `test_approval_does_not_mutate_inventory` | ResourceRepository unchanged after APPROVED |
| 5 | `test_approval_allocation_unchanged` | Allocation proposal identical before/after review |
| 6 | `test_rejection_resumes_and_terminates` | REJECTED terminates workflow |
| 7 | `test_rejection_does_not_mutate_inventory` | ResourceRepository unchanged after REJECTED |
| 8 | `test_revision_requested_terminates_without_reoptimization` | No re-optimization on REVISION_REQUESTED |
| 9 | `test_invalid_decision_rejected` | Invalid decision raises ValueError |
| 10 | `test_approval_immutability_same_record` | APPROVED cannot be mutated to REJECTED |
| 11 | `test_conflicting_decision_for_same_run_blocked` | No two conflicting finals for same run |
| 12 | `test_identical_submission_is_idempotent` | Re-submitting same decision is safe |
| 13 | `test_explicit_run_id_preserved` | state.run_id preserved throughout |
| 14 | `test_missing_run_id_stays_none` | run_id=None stays None |
| 15 | `test_thread_id_never_becomes_optimization_run_id` | thread_id isolation |
| 16 | `test_needs_verification_cannot_reach_approval` | Verification gate |
| 17 | `test_rejected_verification_cannot_reach_approval` | Rejected verification gate |
| 18 | `test_no_execution_after_approval` | APPROVED = AUTHORIZED, not EXECUTED |
| 19 | `test_complete_lifecycle_approve` | Full approve lifecycle |
| 20 | `test_complete_lifecycle_reject` | Full reject lifecycle |
| 21 | `test_complete_lifecycle_revision` | Full revision lifecycle |
| 22 | `test_approval_service_persists_correctly` | ApprovalService fields |
| 23 | `test_approval_service_persists_rejection` | Rejection record fields |
| 24 | `test_approval_service_persists_revision` | Revision record fields |
| 25 | `test_approval_none_run_id_preserved` | None run_id in service |

---

## 20. Known Limitations

1. **Authentication not yet implemented**: `reviewer_id` defaults to `"API_USER"`. Real authentication (JWT/OAuth) is deferred.

2. **Single-candidate limitation**: The graph processes one incident candidate (the first). Multi-incident orchestration is deferred.

3. **No approval query endpoint**: `GET /agents/review/{thread_id}` is not yet implemented. Callers must track their own `thread_id`.

4. **Audit events in InMemory mode**: When running with `inmemory` backend (no Supabase), audit events are silently skipped (logged as warnings). In production with Supabase, they are persisted.

5. **MemorySaver is in-memory only**: If the server restarts, `MemorySaver` loses all checkpoints. A persistent checkpointer (e.g., PostgreSQL-backed) is needed for production durability.

---

## 21. Phase 4F Boundary

Phase 4E ends with the allocation proposal in `AUTHORIZED_FOR_EXECUTION` state.

Phase 4F will:
- Read the approved allocation from the repository.
- Deduct inventory.
- Dispatch resources.
- Send agency notifications.
- Record field execution events.

No Phase 4F logic exists in Phase 4E code.
