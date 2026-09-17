import urllib.request
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8001"

def http_get(endpoint: str):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def main():
    with open("scratch/phase6b_e2e_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    incident_id = meta["incident_id"]
    initial_assessment_id = meta["initial_assessment_id"]
    second_assessment_id = meta["second_assessment_id"]
    approval_1_id = meta["approval_1_id"]
    approval_2_id = meta["approval_2_id"]
    execution_1_id = meta["execution_1_id"]
    execution_2_id = meta["execution_2_id"]
    depot_loc = meta["depot_loc"]

    print("=" * 70)
    print("STEP 12: POST-RESTART PERSISTENCE VERIFICATION")
    print(f"Target Incident ID: {incident_id}")
    print("=" * 70)

    # 1. Health check
    status, h = http_get("/health")
    assert status == 200 and h["status"] == "ok"
    print("FastAPI process restarted and healthy.")

    # 2. Query /incidents
    status, incidents = http_get("/incidents")
    assert status == 200
    inc = next((i for i in incidents if i["incident_id"] == incident_id), None)
    assert inc is not None, f"Incident {incident_id} not found after restart!"
    print(f"PASS: Incident {incident_id} loaded from DB after server restart. Status: {inc['status']}")

    # 3. Query /incidents/{id}/assessment
    status, ass_data = http_get(f"/incidents/{incident_id}/assessment")
    assert status == 200
    assert ass_data["incident_id"] == incident_id
    assert ass_data["verification_status"] == "VERIFIED"
    assert ass_data["severity"] is not None
    print(f"PASS: /incidents/{incident_id}/assessment returned verified assessment with severity: {ass_data['severity'].get('status', 'success')}")

    # 4. Query /allocations/incident/{id}
    status, allocs = http_get(f"/allocations/incident/{incident_id}")
    assert status == 200
    assert len(allocs) >= 1, "Allocations missing after server restart!"
    print(f"PASS: {len(allocs)} allocation records retrieved from DB after process restart.")

    # 5. Query /resources
    status, resources = http_get("/resources")
    assert status == 200
    depot_resources = {r["resource_type"]: r["quantity_available"] for r in resources if r["location_id"] == depot_loc}
    print(f"Depot {depot_loc} post-restart inventory:", depot_resources)
    assert depot_resources["Potable Water"] == 85000, f"Expected 85000 Potable Water, got {depot_resources.get('Potable Water')}"
    assert abs(depot_resources["Cereal"] - 49.55) < 0.001, f"Expected 49.55 Cereal, got {depot_resources.get('Cereal')}"
    assert depot_resources["Family Tents"] == 500, f"Expected 500 Family Tents, got {depot_resources.get('Family Tents')}"
    print("PASS: Persistent inventory deduction strictly survived process restart!")

    # 6. Direct Supabase verification
    sys.path.insert(0, '.')
    sys.path.insert(0, 'backend')
    from app.db.client import get_supabase_client
    sb = get_supabase_client()
    db_actions = sb.table("actions").select("*").eq("incident_id", incident_id).execute()
    print(f"PASS: Direct Supabase query confirms {len(db_actions.data)} executed action rows in remote Supabase.")
    assert len(db_actions.data) >= 2, f"Expected at least 2 executed actions in remote DB, got {len(db_actions.data)}"

    db_audits = sb.table("audit_events").select("*").eq("incident_id", incident_id).execute()
    print(f"PASS: Direct Supabase query confirms {len(db_audits.data)} audit event rows in remote Supabase.")
    assert len(db_audits.data) >= 2, f"Expected audit events in remote DB, got {len(db_audits.data)}"

    print("\nALL POST-RESTART PERSISTENCE CHECKS PASSED LIVE!")

if __name__ == "__main__":
    main()
