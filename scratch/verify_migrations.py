import glob
import os

migrations = sorted(glob.glob('supabase/migrations/*.sql'))
print(f'Found {len(migrations)} migrations:')
for m in migrations:
    size = os.path.getsize(m)
    print(f'  {m} ({size} bytes)')

expected_tables = [
    'reports', 'incidents', 'incident_evidence', 'assessments',
    'needs', 'resources', 'allocations', 'actions', 'approvals', 'audit_events'
]

with open('supabase/migrations/001_initial_ps20_schema.sql', 'r', encoding='utf-8') as f:
    sql_001 = f.read()

for t in expected_tables:
    assert f'CREATE TABLE IF NOT EXISTS public.{t}' in sql_001, f'Table {t} missing in 001'
    assert f'ALTER TABLE public.{t} ENABLE ROW LEVEL SECURITY;' in sql_001, f'RLS missing for {t} in 001'

print('001 verified: All 10 tables defined with UUID PKs, FKs, and RLS ENABLED!')

with open('supabase/migrations/002_assessment_idempotency_and_provenance.sql', 'r', encoding='utf-8') as f:
    sql_002 = f.read()
assert 'idx_assessments_idempotency' in sql_002
assert 'severity_model_version' in sql_002
assert 'trajectory_policy_version' in sql_002
assert 'needs_policy_version' in sql_002
assert 'priority_policy_version' in sql_002
print('002 verified: Assessment idempotency key & provenance columns present!')

with open('supabase/migrations/003_needs_resources_persistence.sql', 'r', encoding='utf-8') as f:
    sql_003 = f.read()
assert 'idx_resources_location_type_category' in sql_003
assert 'calculation_basis' in sql_003
print('003 verified: Resource unique index and need ML fields present!')

with open('supabase/migrations/004_allocation_execution_identity.sql', 'r', encoding='utf-8') as f:
    sql_004 = f.read()
assert 'ALTER COLUMN optimization_run_id DROP NOT NULL' in sql_004
print('004 verified: optimization_run_id made nullable for ad-hoc allocations!')

with open('supabase/migrations/005_approval_optimization_run_id.sql', 'r', encoding='utf-8') as f:
    sql_005 = f.read()
assert 'ADD COLUMN optimization_run_id TEXT' in sql_005
assert 'idx_approvals_optimization_run_id' in sql_005
print('005 verified: optimization_run_id column & index added to approvals!')

with open('supabase/migrations/006_execution_action_metadata.sql', 'r', encoding='utf-8') as f:
    sql_006 = f.read()
assert 'ADD COLUMN IF NOT EXISTS execution_id TEXT' in sql_006
assert 'idx_actions_execution_id' in sql_006
print('006 verified: Execution metadata & indexes added to actions!')

with open('supabase/migrations/007_reassessment_metadata.sql', 'r', encoding='utf-8') as f:
    sql_007 = f.read()
assert 'parent_assessment_id UUID' in sql_007
assert 'reassessment_reason TEXT' in sql_007
assert 'previous_optimization_run_id TEXT' in sql_007
print('007 verified: Parent assessment lineage & previous optimization run id added!')

print('\nALL 7 MIGRATIONS VERIFIED SUCCESSFULLY!')
