-- supabase/migrations/007_reassessment_metadata.sql

-- 1. Add parent_assessment_id and reassessment_reason to public.assessments
ALTER TABLE public.assessments
ADD COLUMN IF NOT EXISTS parent_assessment_id UUID REFERENCES public.assessments(assessment_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS reassessment_reason TEXT;

-- 2. Add index for parent_assessment_id
CREATE INDEX IF NOT EXISTS idx_assessments_parent_id ON public.assessments(parent_assessment_id);

-- 3. Add previous_optimization_run_id to public.allocations
ALTER TABLE public.allocations
ADD COLUMN IF NOT EXISTS previous_optimization_run_id TEXT;

-- 4. Add index for previous_optimization_run_id
CREATE INDEX IF NOT EXISTS idx_allocations_previous_run ON public.allocations(previous_optimization_run_id);
