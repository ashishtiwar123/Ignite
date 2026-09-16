# Phase 4C — Situation Assessment Integration

## 1. Objective
Integrate the existing validated deterministic and machine-learning Situation Assessment engines (Severity, Trajectory, Needs, Priority) into the LangGraph orchestrator. LangGraph operates purely as a coordinator; the engines remain strictly authoritative for all numeric and operational decisions.

## 2. Existing Engine Contracts
The integration seamlessly adopts the existing API schemas of the Phase 2 engines:
- `SeverityPredictorV2`: Processes disaster features to return `severity_score`, `severity_class`, and `status`.
- `Trajectory Engine`: Consumes `RiskObservation` models and returns a single `TrajectoryAssessment` indicating trends like `RAPIDLY_WORSENING`.
- `Needs Engine`: Receives `NeedsAssessmentInput` (including `affected_population`) and returns a strict list of quantitative and qualitative `ResourceRequirement` elements.
- `Priority Engine`: Uses `PriorityEngineInput` (assimilating verification, severity, trajectory, and needs outcomes) to output a final `PriorityAssessment` with `priority_score` and `priority_level`.

## 3. LangGraph Orchestration
The new `situation_assessment_node` executes in `ml/src/agents/graph.py`. It sequentially orchestrates Severity, Trajectory, Needs, and Priority without relinquishing control back to the user/LLM, as these engines are fast, deterministic functions designed to operate cohesively on a verified candidate.

## 4. Verification Gate
Situation assessment is strictly gated behind the Phase 4B `VERIFIED` status. Any `incident_candidates` with `NEEDS_VERIFICATION` or `REJECTED` are cleanly bypassed, leaving their assessment status as `PENDING`.

## 5. Severity
Integrated by passing explicit geographic and seismic/cyclonic features to `SeverityPredictorV2`. A `success` response persists the numeric severity score; an `unsupported_hazard` safely returns an unsupported string and `None` for the score, respecting the exact engine capabilities. Model versions are meticulously preserved.

## 6. Trajectory
Integrated by mapping structured reports into temporal `RiskObservation` items. Maintains the explicit `INSUFFICIENT_EVIDENCE` state instead of fabricating arbitrary "stable" baselines when reports are sparse.

## 7. Needs
Populated precisely with `affected_population` from the canonical record or primary report. The distinction between quantitative rules (e.g. WASH) and qualitative urgencies (e.g. MEDICAL, RESCUE) is perfectly maintained through LangGraph arrays.

## 8. Priority
Leverages the exact deterministic priority formulas from the priority engine by injecting severity, trajectory, and needs outputs. Scores and explicit priority classes (e.g. CRITICAL) are seamlessly carried forward.

## 9. Assessment Aggregation
All individual outputs are unified into a single `AssessmentRecord` that maps exactly to the Phase 3C persistence schema. 

## 10. Persistence
Integration preserves architectural boundaries by utilizing `AssessmentService` and `NeedsService` inside the node. Database SQL is kept strictly out of LangGraph. We provided `save_complete_assessment()` to facilitate a full atomic commit of the orchestrated outputs without recreating internal DB queries.

## 11. Idempotency
Phase 3C uniqueness semantics remain perfectly intact. The caller-supplied `state.run_id` acts explicitly as the `idempotency_key`. 

## 12. Run ID vs Thread ID
A clear operational boundary enforces that `run_id` denotes the genuine business execution identity, whereas the LangGraph checkpoint `thread_id` remains an isolated framework state identifier that never leaks into business provenance or idempotency keys.

## 13. Provenance
Provenance is flawlessly propagated:
- Severity: `model_version`
- Trajectory: `policy_version`
- Needs: `rule_id`, `policy_version`, `calculation_basis`
- Priority: `policy_version`

## 14. Unsupported Hazards
Unsupported hazard flows (like WILDFIRE against SeverityPredictorV2) explicitly retain the `unsupported_hazard` label and produce no fabricated numeric fallbacks. Downstream engines handle missing severities safely via their built-in fallback modes.

## 15. Failure Semantics
In the event that an engine throws an unrecoverable error or persistence fails, `state.assessment_status` explicitly reports `FAILED` or `PERSISTENCE_FAILED`, ensuring the workflow cannot incorrectly flag an incomplete assessment as `ASSESSMENT_COMPLETE`.

## 16. Single-Candidate Limitation
Inheriting from Phase 4B, the node explicitly restricts evaluation to `state.incident_candidates[0]`. End-to-end multi-incident routing is cleanly deferred to future phases.

## 17. Tests
A dedicated Phase 4C test suite (`ml/tests/test_phase4c_graph.py`) exhaustively tests 30 distinct criteria ranging from idempotency to provenance leakage, failure states, and engine invocations.

## 18. Regression
ML and Backend regression tests execute the full suite completely green, guaranteeing that Phase 4C enhancements break absolutely no prior functionality.

## 19. Static Audit
Audits confirmed that no LLM dependencies compute numeric severity/priority, no SQL statements live in graph logic, and no secrets leak into the payload.

## 20. Limitations
- Single candidate processing (multi-incident support deferred).
- Wait-and-see integration into final Phase 4D dynamic reallocation logic.

## 21. Phase 4D Boundary
Phase 4C ends exactly at the persistence and aggregation of the situation assessment. It does NOT invent optimization or resource allocations, retaining strict boundaries ahead of the upcoming Phase 4D Allocation workflows.
