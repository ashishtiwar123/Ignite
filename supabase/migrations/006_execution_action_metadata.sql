-- supabase/migrations/006_execution_action_metadata.sql

-- 1. Add execution metadata columns to public.actions table to capture Phase 4F execution records
ALTER TABLE public.actions
ADD COLUMN IF NOT EXISTS optimization_run_id TEXT,
ADD COLUMN IF NOT EXISTS approval_id UUID REFERENCES public.approvals(approval_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS execution_id TEXT,
ADD COLUMN IF NOT EXISTS payload JSONB,
ADD COLUMN IF NOT EXISTS executed_by TEXT,
ADD COLUMN IF NOT EXISTS executed_at TIMESTAMPTZ;

-- 2. Indexes for fast lookup by execution_id and optimization_run_id
CREATE INDEX IF NOT EXISTS idx_actions_execution_id ON public.actions(execution_id);
CREATE INDEX IF NOT EXISTS idx_actions_optimization_run_id ON public.actions(optimization_run_id);
