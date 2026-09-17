# Phase 4G — Reassessment & Dynamic Reallocation Specification

## Overview

Phase 4G implements the closed-loop reassessment and dynamic reallocation capability for PS20 — Agentic Disaster Relief & Emergency Resource Coordinator.

Crucially:
- **Reassessment does NOT itself move resources.**
- **Optimization produces a proposal.**
- **Only approved proposals can enter execution.**
- **ExecutionService is the only inventory mutation boundary.**

---

## Architecture & Reassessment Lifecycle

```
NEW EVIDENCE
    ↓
EXISTING INCIDENT (Correction 10)
    ↓
VERIFICATION GATING (Correction 11)
    ↓
SITUATION ASSESSMENT & NEW SNAPSHOT (Correction 1)
    ↓
ASSESSMENT COMPARISON (Correction 7 & 8)
    ↓
REALLOCATION POLICY DECISION (Correction 6)
    ↓
NEW OR-TOOLS PROPOSAL (Correction 3 & 9)
    ↓
ALLOCATION DELTA (Correction 4 & 5)
    ↓
HUMAN APPROVAL (Correction 13)
    ↓
CONTROLLED EXECUTION (Correction 14 & 15)
    ↓
INVENTORY MUTATION
    ↓
AUDIT PERSISTENCE
```

---

## Key Design Principles & Corrections

### 1. Immutable Assessment Snapshots (Correction 1)
- Every reassessment creates a **NEW** assessment record.
- Historical assessments remain strictly immutable.
- `parent_assessment_id` links the new assessment snapshot to its immediate predecessor for lineage tracking within the same incident.

### 2. Operational Allocation Baseline (Correction 2)
- Reallocations are calculated relative to the **CURRENT OPERATIONAL ALLOCATION** — defined as the latest successfully `EXECUTED` allocation.
- Unexecuted, pending, rejected, or failed proposals are NEVER treated as current resource state.

### 3. Allocation Deltas & Inventory Safety (Corrections 4, 5, 15)
- An allocation delta (`AllocationDiff`) represents `NEW PROPOSAL - CURRENT OPERATIONAL ALLOCATION`.
- Deltas are strictly categorized into `ADDED`, `INCREASED`, `DECREASED`, `REMOVED`, and `UNMET`.
- Physical resource mutation occurs exclusively via `ExecutionService` upon explicit human approval.

### 4. Deterministic Reallocation Decision Policy (Correction 6)
- `is_reallocation_required` evaluates operational changes (quantitative demand shift, priority change, unmet demand becoming actionable).
- Returns explicit status: `NO_REALLOCATION_REQUIRED`, `REALLOCATION_REQUIRED`, `OPTIMIZATION_INFEASIBLE`, `INSUFFICIENT_DATA`, `NEEDS_HUMAN_REVIEW`.

### 5. Existing Pipeline Reuse (Correction 9)
- Reassessment reuses existing engines: SeverityPredictorV2, Trajectory Engine, Needs Engine, Priority Engine, OR-Tools Optimizer, and ExecutionService. No duplicate engines exist.

### 6. Human Approval Boundary (Correction 13)
- Every new optimization proposal requires explicit human approval via Phase 4E `submit_review`.
- No proposal can mutate inventory without prior human approval.

---

## API Contract

`POST /agents/reassess/{thread_id}`

### Request Payload (`ReassessmentRequest`)
- `new_reports`: List of raw report JSON strings
- `reassessment_reason`: Human or system trigger explanation
- `run_id`: Optional explicit domain run identifier

### Response Payload (`ReassessmentResponse`)
- `run_id`, `thread_id`, `incident_id`
- `previous_assessment_id`, `current_assessment_id`
- `assessment_diff`, `reallocation_required`, `reallocation_decision_status`
- `new_optimization_run_id`, `allocation_diff`
- `human_approval_state`, `status`, `errors`
