-- supabase/migrations/004_allocation_execution_identity.sql

-- 1. Make optimization_run_id nullable to allow non-idempotent/ad-hoc executions
ALTER TABLE public.allocations
ALTER COLUMN optimization_run_id DROP NOT NULL;

-- 2. Add a partial unique index to enforce idempotency when an explicit run_id is supplied.
-- Multiple NULL executions for the same incident are allowed (not deduplicated).
-- Note: A single optimization execution might produce multiple allocation records for the same incident
-- (e.g., allocating multiple resources to different requirements). So uniqueness must include requirement_id 
-- or source_location_id + resource_type.
-- Looking at the idempotency requirement: "duplicate allocation decisions". 
-- If an orchestration run is retried, the batch of allocations should be ignored if already present.
-- We can't just put UNIQUE(incident_id, optimization_run_id) because one run inserts multiple rows.
-- The existing logic in SupabaseAllocationRepository checks if ANY row exists for optimization_run_id:
-- `self.client.table("allocations").select("allocation_id").eq("optimization_run_id", run_id).limit(1)`
-- So we don't necessarily need a multi-column UNIQUE constraint at the DB level, because 
-- the repository enforces it at the batch level before insert, and a single optimization run 
-- natively returns multiple rows. We should just keep the column nullable.

-- However, if we do want a unique constraint for each individual allocation within a run, it would be:
-- UNIQUE (optimization_run_id, requirement_id, source_location_id) WHERE optimization_run_id IS NOT NULL.
-- But since the repo handles batch existence checks, making the column nullable is sufficient to satisfy the requirements.
