-- supabase/migrations/005_approval_optimization_run_id.sql

-- 1. Add optimization_run_id to approvals table to stably reference the allocation proposal
ALTER TABLE public.approvals
ADD COLUMN optimization_run_id TEXT;

-- 2. Relax the NOT NULL constraint on action_id since approvals will now track optimization runs (wait, it was already nullable, but let's be sure).
-- Wait, in 001, action_id is `action_id UUID REFERENCES public.actions(action_id) ON DELETE CASCADE`. So it's already nullable.
-- We will just make sure it's clear.

-- 3. Add an index to efficiently query approvals by optimization_run_id
CREATE INDEX IF NOT EXISTS idx_approvals_optimization_run_id ON public.approvals(optimization_run_id);
