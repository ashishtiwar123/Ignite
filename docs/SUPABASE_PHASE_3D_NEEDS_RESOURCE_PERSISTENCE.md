# Phase 3D Needs & Resource Persistence

## 1. Objective
Build the persistence layer for `Needs` and `Resources` connecting the ML engines to the database to support future LangGraph allocation.

## 2. Existing Schema Inspected
The initial migration `001` enforced `NOT NULL` on `quantity` and `unit` for the `needs` table and lacked multiple ML output metadata fields.

## 3. Schema Changes
Added `003_needs_resources_persistence.sql`:
- Dropped `NOT NULL` constraints on `quantity` and `unit` to support qualitative needs (e.g. RESCUE).
- Added `status`, `time_window`, `rule_id`, `policy_version`, `calculation_basis`, `provenance`, and `explanation` to `needs`.
- Enforced a unique index on `resources(location_id, resource_type, category)` for inventory UPSERT support.

## 4. Needs Data Model
Mapped the canonical ML `ResourceRequirement` directly to `NeedRecord` internal schemas, supporting nullable physical quantifiers and complete provenance metadata.

## 5. Resource Data Model
Aligned operational inventory schemas in `ResourceRecord` providing UPSERT guarantees.

## 6. Repository Architecture
Implemented `BaseNeedsRepository` & `BaseResourceRepository` with in-memory and Supabase implementations based on `PERSISTENCE_BACKEND`.

## 7. Service Architecture
Created `NeedsService` mapping raw dictionaries to `NeedRecord` models and saving them via repo. Created `ResourceService` for CRUD logic with constraint validation (no negative quantities).

## 8. API Contracts
Created `/incidents/{incident_id}/needs` and `/resources` endpoints. They separate calculation concerns from persistence, merely persisting and retrieving records.

## 9. Validation Rules
- No negative quantities for resources.
- UPSERTs safely fallback and merge using `location_id`, `resource_type`, and `category`.
- Implicit NULL mapping for qualitative Needs quantity/unit.

## 10. Idempotency/Duplication Semantics
- Needs: Handled via `assessment_id`. Existing queries preemptively block duplicate bulk inserts for the same assessment context, supporting immutable execution snapshots.
- Resources: `UPSERT` semantics leveraging the unique constraints on `(location_id, resource_type, COALESCE(category, ''))`.

## 11. Tests
Created `test_needs_repository.py` and `test_resource_repository.py` running mocked integration checks covering duplicate blocking, UPSERT constraints, and retrieval operations.

## 12. Regression Results
- Backend: 30/30 (includes 6 new Phase 3D tests).
- ML: 98/98 baseline sustained. No modifications made.

## 13. Limitations
Authentication and explicit warehouse geolocation remain unmanaged, strictly following current mock/UI behavior parameters.

## 14. What remains for Phase 3E
- OR-Tools integration via `allocations` persistence.
- Modifying resource inventory states based on specific solved `allocations`.
- Actions tracking.

Phase 3D does NOT implement resource allocation.
Phase 3D does NOT implement OR-Tools persistence.
Phase 3D does NOT implement LangGraph integration.
Phase 3D does NOT implement frontend integration.
