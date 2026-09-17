# Phase 5 — Frontend ↔ Real Backend Integration Specification

## Overview

Phase 5 completes the full integration between the React/TanStack Start frontend and the real FastAPI / LangGraph backend for **PS20 — Agentic Disaster Relief & Emergency Resource Coordinator**.

---

## Architectural Principles & Security Invariants

1. **Backend as Sole Source of Truth**:
   All ML predictions, severity scoring, trajectory computation, Sphere needs calculations, priority ranking, OR-Tools GLOP solver optimizations, assessment snapshots, and inventory mutations are executed **EXCLUSIVELY** on the backend.

2. **Zero Browser ML / Optimization Logic**:
   The frontend does NOT duplicate severity, priority, trajectory, or needs formulas, nor does it call Gemini or OR-Tools directly.

3. **No Service-Role Secrets in Browser**:
   The browser communicates strictly with the FastAPI server via `http://localhost:8001` (configurable via `VITE_API_BASE_URL`). No `SUPABASE_SERVICE_ROLE_KEY` or `GEMINI_API_KEY` credentials exist in the client.

4. **Human Governance & Controlled Execution**:
   - Proposals produced by OR-Tools require explicit human approval via `POST /agents/review/{thread_id}` (`APPROVED`, `REJECTED`, `REVISION_REQUESTED`).
   - Resource inventory deduction is triggered strictly by `POST /agents/execute/{thread_id}`, which invokes Phase 4F `ExecutionService`.

---

## Data Flow Pipeline

```
REAL DISASTER REPORT
        ↓
FASTAPI (`POST /reports` / `POST /agents/run`)
        ↓
LANGGRAPH ORCHESTRATOR
        ↓
ML / RULES / OR-TOOLS
        ↓
SUPABASE PERSISTENCE
        ↓
REAL DASHBOARD STATE
        ↓
HUMAN APPROVAL (`POST /agents/review/{thread_id}`)
        ↓
CONTROLLED EXECUTION (`POST /agents/execute/{thread_id}`)
        ↓
PHASE 4G REASSESSMENT (`POST /agents/reassess/{thread_id}`)
        ↓
DYNAMIC REALLOCATION PROPOSAL & DELTA (`AllocationDiff`)
```

---

## Centralized Frontend API Architecture (`frontend/src/lib/api/`)

- `client.ts`: Base HTTP client wrapper handling `VITE_API_BASE_URL`, JSON body formatting, and unified `ApiError` class.
- `types.ts`: Type-safe TypeScript contracts mirroring backend Pydantic models.
- `reports.ts`: `createReport(data)` -> `POST /reports`.
- `incidents.ts`: `getIncidents()` -> `GET /incidents`, `getIncidentAssessment(id)` -> `GET /incidents/{incident_id}/assessment`.
- `resources.ts`: `getResources(locationId)` -> `GET /resources`.
- `allocations.ts`: `optimizeAllocations(req)` -> `POST /allocations/optimize`, `getIncidentAllocations(id)` -> `GET /allocations/incident/{incident_id}`.
- `agents.ts`:
  - `runAgent(req)` -> `POST /agents/run`
  - `submitReview(threadId, req)` -> `POST /agents/review/{thread_id}`
  - `executeProposal(threadId, req)` -> `POST /agents/execute/{thread_id}`
  - `reassessIncident(threadId, req)` -> `POST /agents/reassess/{thread_id}`

---

## Component Integration Highlights

- **`IncidentsView.tsx`**: Renders real incidents from `GET /incidents` and detailed assessment metrics (`verification_status`, `severity`, `trajectory`, `priority`, `needs`) from `GET /incidents/{incident_id}/assessment`.
- **`ReportsView.tsx`**: Field report submission form connected to `POST /reports` & `POST /agents/run`.
- **`ResourcesView.tsx`**: Renders real operational inventory levels from `GET /resources`.
- **`DisasterMap.tsx`**: Places map markers using real backend incident centroid coordinates (`centroid_latitude`, `centroid_longitude`).
- **`ApprovalExecutionPanel.tsx`**: Governance panel displaying proposed allocations, human review decision submit controls (`APPROVED`, `REJECTED`, `REVISION_REQUESTED`), and controlled execution button invoking `ExecutionService`.
- **`ReassessmentModal.tsx`**: Form to submit new disaster evidence for an existing incident (`POST /agents/reassess/{thread_id}`), displaying itemized `AssessmentDiff` and `AllocationDiff` (`ADDED`, `INCREASED`, `DECREASED`, `REMOVED`, `UNMET`).
