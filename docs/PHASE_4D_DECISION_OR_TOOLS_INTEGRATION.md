# Phase 4D — Decision Intelligence & OR-Tools Integration

## 1. Objective
Integrate the existing OR-Tools `AllocationService` into the LangGraph orchestrator (`optimization_node`). Ensure LangGraph acts purely as an orchestrator, bridging Phase 4C outputs (Needs, Priority) into the deterministic Phase 2I optimizer.

## 2. Dependency Architecture
The integration adheres to the established architectural boundary:
```text
FastAPI
   ↓
LangGraph (optimization_node)
   ↓
AllocationService (backend/app/services/allocation_service.py)
   ↓
OR-Tools Engine (ml/src/optimization/engine.py)
   ↓
AllocationRepository
```
No reverse dependencies were introduced. `graph.py` instantiates `AllocationService` dynamically to delegate optimization execution and persistence.

## 3. AllocationService Integration
The `optimization_node` dynamically binds backend singleton dependencies (allocation, needs, resource, and assessment repositories) into `AllocationService` and calls `.optimize(OptimizationRequest(incident_ids=[...]))`.

## 4. Assessment Mapping
The service retrieves priority assessments via `assessment_repo.get_latest_for_incident()`, pulling the exact priority score calculated during Phase 4C.

## 5. Needs Mapping
The service retrieves needs via `needs_repo.get_by_incident()`. Only quantitative resource requirements are processed by OR-Tools; qualitative needs gracefully skip allocation mathematics.

## 6. Resource Mapping
The service uses `resource_repo.get_all()` to discover inventory. No fake inventory structures exist in `graph.py`. If the repositories are empty (or in testing), no allocations are made.

## 7. Priority Mapping
`AllocationService` explicitly maps the persistent assessment priority level and score into the `PriorityAssessment` schema required by the optimizer.

## 8. OR-Tools Integration
OR-Tools GLOP solver remains authoritative. `graph.py` contains zero optimization mathematics.

## 9. Partial Fulfillment
Partial fulfillment is handled natively by the GLOP solver.

## 10. Unmet Demand
If inventory is insufficient to cover the demand of an incident, the `quantity_unmet` field records the remaining deficit. No resources are fabricated.

## 11. Infeasible Behavior
If the problem is unsolveable, `overall_status` returns `INFEASIBLE` which translates into a state error that flags the node for human review or intervention.

## 12. Allocation Persistence
`AllocationService` automatically commits proposed allocations using `allocation_repo.save_allocations()`.

## 13. Run ID Semantics
The existing `state.run_id` idempotency key is forwarded exactly to `optimization_run_id`.

## 14. Idempotency
Because `state.run_id` propagates into `OptimizationRequest`, the persistence layer seamlessly respects the idempotency contract across retries.

## 15. Inventory Mutation Boundary
Phase 4D creates an ALLOCATION PROPOSAL. Inventories are NOT deducted. No execution actions happen.

## 16. Human Approval Boundary
The `optimization_node` returns state which subsequently stops at a `human_review_node`. The allocations wait for approval. 

## 17. Gemini Boundary
Gemini is heavily constrained and takes absolutely no part in numerical fulfillment operations.

## 18. Single-Candidate Limitation
Currently, the pipeline selects `state.incident_candidates[0]`. Multi-incident optimization is architecturally deferred.

## 19. Tests
A dedicated suite `test_phase4d_graph.py` validates the entire integration boundary.

## 20. Regression
- ML tests: 119 Passed
- Backend tests: 46 Passed

## 21. Static Audit
- Only one authoritative optimizer exists (OR-Tools GLOP).
- No fake resources exist.
- Thread ID cannot leak into `optimization_run_id`.

## 22. Limitations
Multi-incident orchestration is deferred.

## 23. Phase 4E Boundary
Phase 4D explicitly stops before human execution. Phase 4E handles Human Review workflows.
