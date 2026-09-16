# Phase 4B — Report to Incident Orchestration

## Overview
Phase 4B integrates the real machine learning and deterministic pipelines into the LangGraph orchestration (`ml/src/agents/graph.py`), replacing the previous mock implementations. The pipeline now natively transforms unstructured user reports or structured external data feeds into verifiable Incident Candidates.

## Implementation Details

### Report Intelligence
The `report_intelligence_node` receives incoming raw reports and uses the `GeminiAdapter` to extract structured representations. 
- **Provenance Rules**: If the report is an external JSON payload, its genuine `source` and `source_record_id` are preserved. If the report is unstructured manual text, the `source` is set to `"USER_REPORT"` and an internal UUID is generated for the `source_record_id` to satisfy schema constraints without fabricating external provenance.
- **Data Forwarding**: Coordinates (`latitude`, `longitude`) and `magnitude` extracted by Gemini are forwarded into the pipeline.
- **Prompt Injection Defense**: If Gemini extracts `"PROMPT_INJECTION_DETECTED"`, the node explicitly propagates this hazard type.

### Incident Detection Pipeline
The `incident_detection_node` fully utilizes the existing deterministic pipeline:
1. **Validation**: `validate_report_fields()` checks deterministically for boundaries.
2. **Normalization**: `normalize_timestamp()` and `normalize_hazard_type()` enforce canonical formats.
3. **Deduplication**: `deduplicate_reports()` ensures identical provenance signatures are not duplicated.
4. **Matching & Clustering**: `cluster_reports()` inherently performs semantic and geospatial matching to aggregate corroborating reports into a single `IncidentCandidate`.

### Verification Engine
The `verification_node` invokes the authoritative Phase 2E `assess_incident()` engine.
- No logic was reimplemented. The engine dynamically evaluates source corroboration, spatial, temporal, hazard, and attribute consistency.
- Single-report candidates generally map to `NEEDS_VERIFICATION` unless sourced from highly authoritative feeds.
- **Security Check**: Candidates flagged with `"PROMPT_INJECTION_DETECTED"` are immediately intercepted in the graph node and assigned a status of `REJECTED`, safely stopping execution.

## Run ID and Thread ID Semantics
- LangGraph `AgentState.run_id` respects the explicitly provided caller ID (e.g., from FastAPI), or defaults to `None`. 
- The temporary memory `thread_id` used by LangGraph's `MemorySaver` does not leak into the state object, database, or optimization run.

## Known Limitations & Multi-Candidate Handling
- **Single-Candidate Flow**: The `cluster_reports()` function may produce multiple discrete `IncidentCandidate` objects from a batch of reports. However, the current orchestration explicitly selects `incident_candidates[0]` to pass downstream to the Situation Assessment and Optimization nodes. Full multi-incident routing and orchestration is deferred to a future phase.
- **Mock Fallback**: In test environments or when `GEMINI_API_KEY` is missing, the `GeminiAdapter` will use its internal mock deterministic outputs to prevent execution crashes.

## Testing Results
- **ML Regression**: 104/104 PASSED
- **Backend Regression**: 46/46 PASSED (including 7 Agent Service integration tests)
- **Targeted Integration Tests**: 10/10 PASSED (`ml/tests/test_phase4b_graph.py`)

## Phase 4C Boundary
Phase 4C is expected to continue downstream toward situation assessment and integration of priority scaling, ultimately preparing the pipeline for dispatching verified incidents into the OR-Tools optimizer.
