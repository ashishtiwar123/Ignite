-- supabase/migrations/003_needs_resources_persistence.sql

-- 1. Modify `needs` table to align with ML schema ResourceRequirement
ALTER TABLE public.needs ALTER COLUMN quantity DROP NOT NULL;
ALTER TABLE public.needs ALTER COLUMN unit DROP NOT NULL;

ALTER TABLE public.needs ADD COLUMN status TEXT;
ALTER TABLE public.needs ADD COLUMN time_window TEXT;
ALTER TABLE public.needs ADD COLUMN rule_id TEXT;
ALTER TABLE public.needs ADD COLUMN policy_version TEXT;
ALTER TABLE public.needs ADD COLUMN calculation_basis JSONB;
ALTER TABLE public.needs ADD COLUMN provenance JSONB;
ALTER TABLE public.needs ADD COLUMN explanation TEXT;

-- 2. Modify `resources` table to enforce unique inventory tracking per location + category
CREATE UNIQUE INDEX idx_resources_location_type_category 
ON public.resources (location_id, resource_type, COALESCE(category, ''));

