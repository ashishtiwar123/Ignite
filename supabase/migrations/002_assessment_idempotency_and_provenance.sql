-- supabase/migrations/002_assessment_idempotency_and_provenance.sql

-- Add idempotency constraint
ALTER TABLE public.assessments 
ADD COLUMN idempotency_key TEXT;

-- Create unique constraint for incident_id + idempotency_key
CREATE UNIQUE INDEX idx_assessments_idempotency 
ON public.assessments (incident_id, idempotency_key) 
WHERE idempotency_key IS NOT NULL;

-- Drop generic policy_version
ALTER TABLE public.assessments 
DROP COLUMN IF EXISTS policy_version;

-- Add structured provenance fields
ALTER TABLE public.assessments ADD COLUMN severity_model_version TEXT;
ALTER TABLE public.assessments ADD COLUMN verification_policy_version TEXT;
ALTER TABLE public.assessments ADD COLUMN trajectory_policy_version TEXT;
ALTER TABLE public.assessments ADD COLUMN needs_policy_version TEXT;
ALTER TABLE public.assessments ADD COLUMN priority_policy_version TEXT;
