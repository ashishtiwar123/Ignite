import sys
sys.path.insert(0, 'backend')
from app.db.client import get_supabase_client

client = get_supabase_client()
if not client:
    print("FAIL: get_supabase_client returned None!")
    sys.exit(1)

print("SUCCESS: get_supabase_client initialized with server-side credentials.")

tables_to_check = [
    ("reports", ["report_id", "source", "source_record_id", "hazard_type", "ingested_at"]),
    ("incidents", ["incident_id", "hazard_type", "status", "centroid_latitude", "centroid_longitude"]),
    ("incident_evidence", ["evidence_id", "incident_id", "report_id"]),
    ("assessments", [
        "assessment_id", "incident_id", "idempotency_key",
        "severity_model_version", "verification_policy_version", "trajectory_policy_version",
        "needs_policy_version", "priority_policy_version",
        "parent_assessment_id", "reassessment_reason"
    ]),
    ("needs", [
        "need_id", "incident_id", "assessment_id", "resource_type",
        "quantity", "unit", "status", "time_window", "rule_id",
        "policy_version", "calculation_basis", "provenance"
    ]),
    ("resources", ["resource_id", "location_id", "resource_type", "category", "quantity_available", "unit"]),
    ("allocations", [
        "allocation_id", "optimization_run_id", "incident_id", "requirement_id",
        "source_location_id", "resource_type", "quantity_allocated", "previous_optimization_run_id"
    ]),
    ("actions", [
        "action_id", "incident_id", "action_type", "status",
        "optimization_run_id", "approval_id", "execution_id", "payload", "executed_by", "executed_at"
    ]),
    ("approvals", ["approval_id", "incident_id", "optimization_run_id", "action_id", "status", "reviewer_id", "reason", "decided_at"]),
    ("audit_events", ["event_id", "event_type", "incident_id", "report_id", "actor_type", "payload", "event_timestamp"])
]

all_passed = True
results = {}

for table_name, cols in tables_to_check:
    try:
        # Check table existence and specific columns
        col_selector = ",".join(cols)
        resp = client.table(table_name).select(col_selector).limit(1).execute()
        print(f"PASS: Table '{table_name}' exists with columns: {cols}")
        results[table_name] = "EXISTS"
    except Exception as e:
        print(f"FAIL: Table '{table_name}' query error: {e}")
        all_passed = False
        results[table_name] = f"ERROR: {e}"

if all_passed:
    print("\nALL 10 OPERATIONAL TABLES AND PHASE 4-6 CRITICAL COLUMNS EXIST REMOTELY!")
else:
    print("\nONE OR MORE SCHEMA ELEMENTS ARE MISSING REMOTELY!")
    sys.exit(2)
