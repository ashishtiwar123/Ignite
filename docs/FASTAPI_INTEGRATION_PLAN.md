# PS20 FastAPI Integration Plan

## 1. Current Architecture
The current architecture consists of an independent, highly tested ML intelligence pipeline (Phase 2J baseline) and a visually complete but fully mocked React frontend. The backend, database, and API layers are completely missing. The intelligence modules currently execute synchronously in tests and scripts but lack an HTTP serving interface.

## 2. Existing Components
- **Incident Engine**: `ml/src/incident/` (Contains matching, deduplication, validation, and verification)
- **Severity Predictor**: `ml/src/models/severity_v2/predictor_v2.py` (Class: `SeverityPredictorV2`)
- **Trajectory Engine**: `ml/src/risk/trajectory.py` (Outputs `TrajectoryAssessment`)
- **Needs Engine**: `ml/src/needs/engine.py` (Outputs resource requirements)
- **Priority Engine**: `ml/src/priority/engine.py` (Outputs `PriorityAssessment`)
- **Optimization Solver**: `ml/src/optimization/engine.py` (OR-Tools GLOP solver, outputs `AllocationResult`)
- **Agentic Coordinator**: `ml/src/agents/graph.py` (LangGraph integration with Gemini)

## 3. Existing Internal APIs
Currently, the internal ML components communicate via Pydantic schemas (defined in `ml/src/**/schemas.py`) and standard Python dictionaries.
- `Report` and `IncidentCandidate` (Incident Schema)
- `PriorityEngineInput` -> `PriorityAssessment` (Priority Schema)
- `AllocationContext` -> `AllocationResult` (Optimization Schema)
- `SeverityPredictorV2.predict_severity()` expects a dictionary with `predictor_features_x`.

## 4. Frontend API Requirements
The frontend (`frontend/src/lib/scenario.ts`) currently mocks the following data structures:
- `Scenario` (disaster type, severity, affected population, active resources)
- `Zone` / `Facility` (geospatial data and capacity)
- `Deployment` (resource units, ETA, paths, and statuses)
- `Incident` (markers on the map)
- `aiRecommendation` (LangGraph/Gemini output regarding recommended actions, confidence, ETA, and rationale)

## 5. Proposed FastAPI Structure
```
backend/
    app/
        main.py                # FastAPI app initialization, CORS, routing
        api/
            routes/
                reports.py
                incidents.py
                allocations.py
                actions.py
        schemas/
            # API-specific wrappers around ml.src.*.schemas
            requests.py
            responses.py
        services/
            # Orchestrates calls to ml.src components
            incident_service.py
            assessment_service.py
            optimization_service.py
            agent_service.py
        db/
            # Supabase integration layer
            client.py
            repositories.py
        config/
            settings.py        # Environment variables validation
    tests/
```
*Note: We will import the existing `ml/src` modules directly into the `services/` layer rather than duplicating logic.*

## 6. Endpoint Specification

### `POST /reports`
- **Purpose**: Ingest a new disaster report (e.g., from USGS or NGO).
- **Request**: `ReportCreate` schema (matches `ml/src/incident/schemas.Report`).
- **Response**: `{ "report_id": "...", "status": "processing" }`
- **Internal Component**: `incident.extraction`, `incident.matching`
- **Database Effect**: Inserts report into `reports` table.
- **Errors**: 400 Invalid schema, 422 Unprocessable Entity.

### `GET /incidents`
- **Purpose**: Power the frontend map and incident list.
- **Request**: Query params for filtering (status, severity).
- **Response**: List of `IncidentResponse` (mapped to frontend `Incident`).
- **Internal Component**: Database query.
- **Database Effect**: None (Read-only).
- **Errors**: 500 DB Error.

### `GET /incidents/{incident_id}/assessment`
- **Purpose**: Fetch the comprehensive situational assessment (Severity, Trajectory, Needs, Priority) for the dashboard.
- **Request**: None.
- **Response**: `AssessmentResponse` (aggregates ML outputs).
- **Internal Component**: DB query of persisted assessment records.
- **Database Effect**: None.

### `POST /incidents/{incident_id}/reassess`
- **Purpose**: Trigger a manual or systemic reassessment based on new evidence.
- **Request**: Optional evidence payload.
- **Response**: Trigger acknowledgment.
- **Internal Component**: `SeverityPredictorV2`, `Trajectory`, `Needs`, `Priority` pipeline.
- **Database Effect**: Creates new assessment version in DB.
- **Errors**: 404 Incident not found, 400 Insufficient data for ML.

### `POST /allocations/optimize`
- **Purpose**: Trigger the OR-Tools solver to calculate new resource routes and deployments.
- **Request**: `{ "incident_id": "..." }`
- **Response**: `AllocationResult` (mapped to frontend `Deployment[]`).
- **Internal Component**: `optimization.engine`.
- **Database Effect**: Saves draft allocation to `allocations` table.
- **Errors**: 422 Infeasible constraints (handled gracefully, returns partial allocation).

## 7. Schema Mapping
- **`ml/src/incident/schemas.Report`** -> API: `ReportCreate` -> Frontend: Generates new `Incident` marker.
- **`ml/src/optimization/schemas.AllocationResult`** -> API: `OptimizationResponse` -> Frontend: Mapped to `Deployment[]` (routes and ETAs).
- **`ml/src/priority/schemas.PriorityAssessment` + Severity Predictor output** -> API: `AssessmentResponse` -> Frontend: Mapped to `Scenario` state.

## 8. LangGraph Integration
The LangGraph agent (`ml/src/agents/graph.py`) will be executed asynchronously via a background task when an incident is verified or heavily updated. The resulting natural language rationale will be persisted to the database and fetched by the frontend to populate the `aiRecommendation` panel.

## 9. ML Integration
The `SeverityPredictorV2` will be wrapped in a singleton dependency injected into the FastAPI routes or services to prevent reloading the `.joblib` model on every request. If a hazard is unsupported, the backend will catch the `status: unsupported_hazard` dict output and gracefully fallback to deterministic rules, returning a flag to the frontend.

## 10. OR-Tools Integration
The GLOP linear programming solver will be called synchronously during optimization requests. If unmet demand exceeds inventory, the API must correctly serialize the solver's unmet constraints so the frontend can display resource shortages.

## 11. Reassessment / Dynamic Reallocation
**Workflow**:
1. `POST /reports` triggers `incident_service`.
2. Incident updates trigger a background task for `assessment_service`.
3. Needs and Priority change, flagging the incident as requiring reallocation.
4. The LangGraph agent identifies the need for reallocation and drafts a proposal.
5. The frontend polls or receives a WebSocket update, displaying the new `aiRecommendation`.
6. User clicks "Approve", calling `POST /allocations/optimize` (or an approval endpoint) to commit the new plan.

## 12. Authentication / Security
- **Configuration**: Managed via `pydantic-settings`.
- **Secrets**: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` must be loaded from `.env` and never exposed via API responses.
- **CORS**: Configured strictly to allow requests only from the deployed frontend domains.

## 13. Testing Strategy
- **API Tests**: Use `TestClient` from `fastapi.testclient` to verify HTTP behavior and schema validation.
- **Mocks**: Mock the ML predictors and OR-Tools solvers in API tests to ensure speed.
- **Preservation**: Do NOT modify the existing `ml/tests/`. Run API tests in a separate `backend/tests/` suite to ensure the 98/98 baseline remains intact.

## 14. Frontend Integration Plan
1. Stand up the FastAPI shell and basic CRUD endpoints.
2. Replace `saveScenario` and `loadScenario` in `frontend/src/lib/scenario.ts` with real `fetch` calls to `GET /incidents` and `GET /incidents/{id}/assessment`.
3. Replace `deploymentsFor` with data from `GET /allocations`.
4. Implement a Supabase real-time listener (or polling) for live map updates.

## 15. Risks / Unknowns
- **Latency**: ML inference and LangGraph execution could take several seconds. We must design these as async background tasks to prevent HTTP timeouts.
- **Data Shape**: The mocked frontend relies on `Scenario.affectedPopulation` and static zones. The real backend will generate precise coordinates and highly granular data that the frontend must be adapted to parse.
- **Port Conflict**: The ML contract specifies port `8001`. We will deploy the FastAPI integration layer on `8001` to honor this contract, serving both ML requests and frontend API traffic.

## 16. Implementation Order
- **Phase 1**: Infrastructure (FastAPI setup, Pydantic settings, Supabase client).
- **Phase 2**: Core Services Integration (Import ML, Optimization, and Agent components).
- **Phase 3**: Endpoints & Schemas (Build the API layer).
- **Phase 4**: Frontend Wire-up (Replace mock data with API calls).

---
**FASTAPI READINESS**:
- **Existing backend**: 🔴 None. Needs creation.
- **Existing ML services**: ✅ Fully implemented, tested, and ready for import.
- **Existing LangGraph**: ✅ Fully implemented, ready for async execution.
- **Existing schemas**: ✅ Robust Pydantic schemas exist in `ml/src/`.
- **Frontend API requirements**: 🟡 Understood, but requires rewriting `scenario.ts` to consume external data.
- **Database requirements**: 🔴 None. Supabase tables and RLS must be designed.
- **Major integration gaps**: The lack of a unified execution pipeline; ML runs in isolation. FastAPI must bridge this gap.
