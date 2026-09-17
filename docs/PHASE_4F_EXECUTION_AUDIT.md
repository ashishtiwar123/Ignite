# Phase 4F — Controlled Execution + Audit Integration

## 1. Objective

Implement a controlled execution boundary for approved disaster-relief resource allocation proposals. Phase 4F is the first phase authorized to mutate resource inventory.

Conceptual flow:

```
ALLOCATION PROPOSAL (Phase 4D)
          ↓
HUMAN REVIEW (Phase 4E)
          ↓
APPROVED (Authorized for Execution)
          ↓
EXECUTION AUTHORIZATION CHECK
          ↓
PROPOSAL VALIDATION
          ↓
CURRENT INVENTORY VALIDATION
          ↓
ATOMIC INVENTORY MUTATION
          ↓
ACTION / EXECUTION RECORD
          ↓
AUDIT EVENT
          ↓
EXECUTED
```

Failure at any validation stage results in **ZERO INVENTORY MUTATION**.

---

## 2. Absolute Execution Gate

Execution is permitted **ONLY** when a persisted approval record with `status == "APPROVED"` exists in the database/repository.

The following are **NEVER** sufficient authorization:
- `state.human_approval_state == "APPROVED"`
- Client-supplied `approved=true`
- Frontend UI state
- Gemini / LLM output

`ExecutionService` independently loads and verifies the persisted `ApprovalRecord` before performing any action.

---

## 3. Proposal Integrity

Execution consumes the exact Phase 4D allocation proposal.
- **NO** OR-Tools solver invocation during execution.
- **NO** Gemini / LLM calls during execution.
- **NO** recalculation of severity, trajectory, needs, or priority.

---

## 4. Identity Separation

| Identity | Purpose |
|---|---|
| `run_id` | Domain execution context |
| `optimization_run_id` | Phase 4D optimization proposal identity |
| `approval_id` | Phase 4E governance decision identity |
| `execution_id` | Phase 4F execution entity identity (UUID) |
| `thread_id` | LangGraph checkpoint identity |

Rules:
- `execution_id` is a distinct entity identifier.
- `thread_id` **NEVER** becomes `execution_id` or `optimization_run_id`.
- `optimization_run_id` is preserved throughout the pipeline.

---

## 5. Inventory Validation & Atomic Mutation

Before any mutation:
1. Verify `quantity_allocated > 0`.
2. Verify `quantity_allocated` is finite and not `NaN`.
3. Verify `quantity_allocated <= current_available_quantity`.
4. Verify resource exists at target location.

**Atomicity**: Multi-resource inventory mutation is all-or-nothing.
- **InMemory**: Validates all items before mutating state; rolls back on error.
- **Supabase**: Performs conditional updates (`quantity_available = quantity_available - requested WHERE quantity_available >= requested`) with batch rollback on race conditions.

---

## 6. Double Execution Protection / Server-Side Idempotency

If an execution request is submitted twice for the same `optimization_run_id` or `approval_id`:
1. First request: Deducts inventory and logs `ActionRecord` with status `EXECUTED`.
2. Second request: Detects existing `EXECUTED` action record, returns `ALREADY_EXECUTED`, and deducts **ZERO** additional inventory.

---

## 7. Action Records & Audit Events

- **Action Records**: Persisted to `public.actions` table with `execution_id`, `optimization_run_id`, `approval_id`, `status` (`EXECUTED` / `FAILED` / `ALREADY_EXECUTED`), `executed_by`, `executed_at`, and `payload`.
- **Audit Events**: Persisted to `public.audit_events` with `event_type` (`EXECUTION_SUCCEEDED`, `EXECUTION_FAILED`, `EXECUTION_ALREADY_COMPLETED`, `EXECUTION_REJECTED`).
- **Secrets**: API keys, credentials, and tokens are **NEVER** included in audit payloads.

---

## 8. API Contract

`POST /agents/execute/{thread_id}`

Request Body (`ExecutionRequest`):
```json
{
  "optimization_run_id": "optional-run-id",
  "incident_id": "optional-incident-id",
  "executor_id": "optional-user-id"
}
```

Response Body (`ExecutionResponse`):
```json
{
  "execution_id": "uuid",
  "status": "EXECUTED",
  "optimization_run_id": "run-id",
  "approval_id": "approval-id",
  "incident_id": "incident-id",
  "deducted_resources": [
    {
      "resource_id": "uuid",
      "location_id": "warehouse-alpha",
      "resource_type": "Water",
      "category": "WATER",
      "quantity_deducted": 100.0,
      "unit": "Liters",
      "previous_quantity": 1000.0,
      "new_quantity": 900.0
    }
  ],
  "errors": []
}
```

---

## 9. Limitations & Phase 4G Boundary

1. **Supabase Integration Verification**: Supabase transaction contract tests ran against in-memory fallback since live Supabase credentials are not configured in test environment (`Supabase transaction integration: NOT VERIFIED — credentials/environment unavailable`).
2. **Actor Identity**: `executor_id` defaults to `"API_USER"` / `"GRAPH_NODE"` until JWT/OAuth authentication is implemented.
3. **No Field Dispatch / Notification**: Phase 4F mutates internal inventory only. Transport routing, driver dispatch, SMS/email, and external agency notifications belong to Phase 4G+.
