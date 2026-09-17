-- supabase/migrations/008_approval_thread_id.sql

-- Add thread_id to approvals table to reference the LangGraph checkpoint identity
ALTER TABLE public.approvals
ADD COLUMN IF NOT EXISTS thread_id TEXT NULL;

-- Index to query approvals by thread_id if required
CREATE INDEX IF NOT EXISTS idx_approvals_thread_id ON public.approvals(thread_id);
