# Phase 5 Implementation Plan — Frontend ↔ Real Backend Integration

## A. Current Frontend Architecture
- **Framework**: Vite + React 19 + TanStack Router (`@tanstack/react-router`) + TypeScript + TailwindCSS v4.
- **Routing**:
  - `/`: Home / Launch scenario page (`frontend/src/routes/index.tsx`).
  - `/dashboard`: Main Command Centre Dashboard (`frontend/src/routes/dashboard.tsx`).
- **State Management**:
  - `localStorage` for scenario initialization (`resqai.scenario`).
  - Local component state across `IncidentsView`, `ReportsView`, `ResourcesView`, `AgenciesView`, `SettingsView`, and `DisasterMap`.
- **Visualization**: Mapbox GL JS (`mapbox-gl`) inside `DisasterMap.tsx` with dynamic layer toggles for zones, routes, resources, facilities, and incidents.

---

## B. Current Mock-Data Dependencies
1. `frontend/src/lib/scenario.ts`: Contains hardcoded `DEFAULT_SCENARIO`, `ZONES`, `DISASTER_TYPES`, `SEVERITIES`, `RESOURCE_OPTIONS`, mock `incidentsFor()`, mock `facilitiesFor()`, mock `deploymentsFor()`, mock `aiRecommendation()`, and local storage helpers.
2. `frontend/src/lib/disaster/scenario.ts` & `locations.ts`: Contains static coordinate zones for Mumbai (Kurla West, Lower Parel, Bandra East, Sion, BKC, Dadar).
3. `frontend/src/components/dr/views/IncidentsView.tsx`: Static `INITIAL_INCIDENTS` array.
4. `frontend/src/components/dr/views/ReportsView.tsx`: Static `INITIAL_REPORTS` array.
5. `frontend/src/components/dr/views/ResourcesView.tsx`: Static `RESOURCES_DATA` array.
6. `frontend/src/components/dr/views/AgenciesView.tsx`: Static agency personnel data.

---

## C. Backend Endpoints Available
- `POST /reports`: Raw report ingestion (`ReportCreate` -> `ReportResponse`).
- `GET /incidents`: Fetch verified incident candidates (`List[IncidentSummaryResponse]`).
- `GET /incidents/{incident_id}/assessment`: Fetch incident assessment record (`AssessmentResponse`).
- `POST /incidents/{incident_id}/reassess`: Reassessment endpoint (501 fallback, delegates to `/agents/reassess/{thread_id}`).
- `GET /resources`: Operational inventory list (`List[ResourceRecord]`).
- `POST /resources`: Upsert inventory item (`ResourceRecord`).
- `POST /allocations/optimize`: Run OR-Tools GLOP solver (`OptimizationRequest` -> `OptimizationResponse`).
- `GET /allocations/incident/{incident_id}`: Fetch allocations for an incident (`List[AllocationRecord]`).
- `POST /agents/run`: Launch LangGraph pipeline (`AgentRunRequest` -> `AgentRunResponse`).
- `POST /agents/review/{thread_id}`: Inject human approval decision (`AgentResumeRequest` -> `AgentRunResponse`).
- `POST /agents/execute/{thread_id}`: Controlled execution boundary (`ExecutionRequest` -> `ExecutionResponse`).
- `POST /agents/reassess/{thread_id}`: Multi-step reassessment (`ReassessmentRequest` -> `ReassessmentResponse`).

---

## D. Frontend API Layer Design
Create `frontend/src/lib/api/` module structure:
- `client.ts`: Base HTTP client wrapper with `fetch`, configurable `VITE_API_BASE_URL` (default `http://localhost:8001`), JSON parsing, unified error handling (`ApiError`).
- `types.ts`: Type-safe contracts matching FastAPI backend schemas (`internal.py`, `responses.py`, `requests.py`).
- `agents.ts`: Agent pipeline functions (`runAgent`, `submitReview`, `executeProposal`, `reassessIncident`).
- `incidents.ts`: Incident retrieval (`getIncidents`, `getIncidentAssessment`).
- `reports.ts`: Report submission (`createReport`).
- `allocations.ts`: Allocation optimization and query (`optimizeAllocations`, `getIncidentAllocations`).
- `resources.ts`: Resource inventory query (`getResources`, `upsertResource`).

---

## E. Type Mapping
Map FastAPI schemas cleanly to TypeScript interfaces without inventing fields or swallowing nulls:
- `ReportCreate` & `ReportResponse`
- `IncidentSummaryResponse`
- `AssessmentResponse`, `AssessmentRecord`, `UnsupportedHazardResponse`
- `NeedRecord`, `ResourceRecord`, `AllocationRecord`
- `OptimizationRequest`, `OptimizationResponse`
- `AgentRunRequest`, `AgentRunResponse`
- `ApprovalRecord`, `AgentResumeRequest`
- `ActionRecord`, `ExecutionRequest`, `ExecutionResponse`, `DeductedResourceItem`
- `AssessmentDiff`, `AllocationDeltaItem`, `AllocationDiff`
- `ReassessmentRequest`, `ReassessmentResponse`

---

## F. State-Management Changes
- Replace local static arrays with API-backed React state / TanStack Query hooks where appropriate.
- Centralize active thread state (`thread_id`, `run_id`, `incident_id`, `human_approval_state`, `current_assessment`, `allocation_diff`, `assessment_diff`).
- Standardize UI states: `idle`, `loading`, `success`, `error`, `pending_review`, `executing`, `executed`.

---

## G. Pages & Components Requiring Modification
1. `frontend/src/routes/index.tsx`:
   - Connect report submission form to `POST /reports` / `POST /agents/run` to initiate real incident pipeline on backend.
2. `frontend/src/routes/dashboard.tsx`:
   - Replace static scenario loop with real backend calls (`GET /incidents`, `getIncidentAssessment`).
   - Wire live active incident, agent status, and approval controls.
3. `frontend/src/components/dr/views/IncidentsView.tsx`:
   - Fetch real backend incidents via `GET /incidents` and detailed assessment via `GET /incidents/{incident_id}/assessment`.
   - Render real severity, trajectory, priority, and needs.
4. `frontend/src/components/dr/views/ReportsView.tsx`:
   - Connect report submission form to `POST /reports`.
   - Display real ingested report data.
5. `frontend/src/components/dr/views/ResourcesView.tsx`:
   - Fetch real operational inventory from `GET /resources`.
6. `frontend/src/components/dr/DisasterMap.tsx`:
   - Plot real incident centroid coordinates from backend `IncidentSummaryResponse` on Mapbox map.
7. **NEW Component** (`frontend/src/components/dr/ReassessmentModal.tsx` / Panel):
   - Reassessment UI for submitting new evidence on an existing incident (`POST /agents/reassess/{thread_id}`).
   - Displays `AssessmentDiff` (severity change, priority delta, need changes) and `AllocationDiff` (added/increased/decreased allocations).
8. **NEW Component** (`frontend/src/components/dr/ApprovalExecutionPanel.tsx`):
   - Human Review UI displaying proposed allocations, unmet demand, and solver explanations.
   - Triggers `POST /agents/review/{thread_id}` (APPROVED / REJECTED / REVISION_REQUESTED) and `POST /agents/execute/{thread_id}`.

---

## H. Reassessment Workflow
1. User views an existing incident on `IncidentsView` / `Dashboard`.
2. Clicks **"Reassess Incident"** to open Reassessment form.
3. Inputs new evidence (e.g. `"Hospital flooded, 3000 victims stranded, emergency evacuation required"`).
4. Submits `POST /agents/reassess/{thread_id}`.
5. Displays real `ReassessmentResponse`:
   - Assessment Diff (severity, trajectory, priority, needs changes).
   - Reallocation Policy Decision (`REALLOCATION_REQUIRED` vs `NO_REALLOCATION_REQUIRED`).
   - Allocation Diff (quantities `ADDED`, `INCREASED`, `DECREASED`, `REMOVED`, `UNMET`).
6. If `REALLOCATION_REQUIRED`, prompts human review for the new proposal.

---

## I. Approval Workflow
1. When agent state is `PENDING_REVIEW` or `human_approval_state == "PENDING"`, display **Human Review Panel**.
2. Shows proposed allocations, solver status (`OPTIMAL`), priority score, and unmet demand.
3. User selects `APPROVE`, `REJECT`, or `REVISION REQUIRED` with optional review notes.
4. Calls `POST /agents/review/{thread_id}`.
5. Updates approval state in UI to `APPROVED`.

---

## J. Execution Workflow
1. Enabled ONLY when persisted approval status is `APPROVED`.
2. User clicks **"Execute Allocation Proposal"**.
3. Calls `POST /agents/execute/{thread_id}`.
4. Backend executes inventory deductions via `ExecutionService`.
5. Frontend displays `ExecutionResponse`:
   - Status: `EXECUTED` (or `ALREADY_EXECUTED`, `FAILED`, `NOT_APPROVED`).
   - Itemized deducted resources (`quantity_deducted`, `previous_quantity`, `new_quantity`).
6. Automatically refreshes resource inventory (`GET /resources`) and incident status.

---

## K. Error & Loading States
- Loading indicators for API requests.
- Visually distinct API Error Alerts (`ApiError` with status code and detail string).
- Explicit rendering for `unsupported_hazard` and `INSUFFICIENT_EVIDENCE`.
- Disabled double-submission during active requests.

---

## L. Demo Scenario (Real Backend Execution)
1. **Initial Incident**: Submit USGS Flood report -> `POST /agents/run` -> Backend verifies, assesses, runs OR-Tools optimization -> UI displays initial incident & allocation proposal.
2. **Human Review 1**: User approves initial allocation proposal -> `POST /agents/review/{thread_id}` -> Executes via `ExecutionService` -> Inventory deducted.
3. **Escalation Evidence**: User clicks "Reassess" -> Inputs hospital flooding report -> `POST /agents/reassess/{thread_id}` -> Backend creates new assessment snapshot, computes assessment diff & allocation delta (`+3000 Liters`).
4. **Human Review 2**: User approves reallocation delta proposal -> `POST /agents/review/{thread_id}` -> `POST /agents/execute/{thread_id}` -> ExecutionService deducts delta inventory -> Audit log updated.

---

## M. Test Strategy
1. **Frontend API Client Tests**: Test `api/client.ts` success, HTTP error status handling, base URL resolution.
2. **Component Integration Tests**: Test incident rendering, assessment diff display, allocation delta rendering, approval button state gating, execution result handling.
3. **Full Regression Suite**:
   - `python -m pytest backend/tests -v`
   - `python -m pytest ml/tests -v`
   - `python -m pytest ml/tests backend/tests -v`
4. **Production Build Verification**: `npm run build` in `frontend/` to confirm zero TypeScript compile or Vite build errors.

---

## N. Scope Exclusions
- No WebSockets / realtime subscriptions (polling / manual refresh is used).
- No client-side Gemini or OR-Tools calls.
- No direct Supabase service-role mutations from browser.
- No modifications to existing Phase 4A-4G backend logic or algorithms.
