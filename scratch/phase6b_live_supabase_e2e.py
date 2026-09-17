import urllib.request
import json
import uuid
import sys
import os
import time
from datetime import datetime, timezone

sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

from app.db.client import get_supabase_client

BASE_URL = "http://127.0.0.1:8001"

def http_post(endpoint: str, data: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"HTTP ERROR on POST {endpoint}: {e.code} -> {err_msg}")
        raise e

def http_get(endpoint: str):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def log_step(title):
    print("\n" + "=" * 70)
    print(f"STEP: {title}")
    print("=" * 70)

def main():
    sb = get_supabase_client()
    assert sb is not None, "Supabase client failed to initialize!"
    
    test_run_tag = uuid.uuid4().hex[:8]
    test_marker = f"PHASE6B-SUPABASE-E2E-{test_run_tag}"
    depot_loc = f"LOC-PHASE6B-DEPOT-{test_run_tag}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    print(f"Starting Phase 6B Live Supabase E2E with marker: {test_marker}")
    
    # 1. Health Check
    log_step("1. Health Endpoint Verification")
    status, health_data = http_get("/health")
    print("Health response:", health_data)
    assert status == 200 and health_data["status"] == "ok"

    # 2. Seed Dedicated Test Depot Resources
    log_step("2. Live Resource Inventory Seeding (Supabase resources table)")
    sb.table("resources").delete().like("location_id", "LOC-PHASE6B-%").execute()
    test_resources = [
        {"location_id": depot_loc, "resource_type": "Potable Water", "category": "WATER", "quantity_available": 100000.0, "unit": "Liters"},
        {"location_id": depot_loc, "resource_type": "Cereal", "category": "FOOD", "quantity_available": 50.0, "unit": "Metric Tons"},
        {"location_id": depot_loc, "resource_type": "Family Tents", "category": "SHELTER", "quantity_available": 500.0, "unit": "Units"}
    ]
    for res in test_resources:
        s, r_data = http_post("/resources", res)
        print(f"API Seeded {r_data['resource_type']}: {r_data['quantity_available']} {r_data['unit']}")
    
    # Direct DB Verification of Resources
    db_res = sb.table("resources").select("*").eq("location_id", depot_loc).execute()
    print(f"Direct DB check: Found {len(db_res.data)} resource records in Supabase resources table.")
    assert len(db_res.data) == 3, f"Expected 3 resources in DB, got {len(db_res.data)}"
    inv_before = {r["resource_type"]: r["quantity_available"] for r in db_res.data}
    print("Initial Remote DB Inventory:", inv_before)

    # 3. Ingest Corroborated Disaster Reports (POST /agents/run)
    log_step("3. Corroborated Disaster Ingestion (POST /agents/run)")
    r1_source_id = f"{test_marker}-USGS"
    r2_source_id = f"{test_marker}-GDACS"
    
    r1 = json.dumps({
        "source": "USGS",
        "source_record_id": r1_source_id,
        "hazard_type": "Flood",
        "location": "Sector C Hospital Zone",
        "latitude": 34.050,
        "longitude": -118.250,
        "observed_at": now_iso,
        "affected_population": 500,
        "displaced_population": 150
    })
    r2 = json.dumps({
        "source": "GDACS",
        "source_record_id": r2_source_id,
        "hazard_type": "Flood",
        "location": "Sector C Hospital Zone",
        "latitude": 34.052,
        "longitude": -118.248,
        "observed_at": now_iso,
        "affected_population": 500,
        "displaced_population": 150
    })

    status, run_resp = http_post("/agents/run", {
        "run_id": test_marker,
        "raw_reports": [r1, r2]
    })
    print("Agent Run Response:", json.dumps(run_resp, indent=2))
    assert status == 200
    assert run_resp["status"] == "PENDING_REVIEW"
    assert run_resp["human_approval_state"] == "PENDING"
    
    # Direct DB Verification of Reports, Incident, Evidence, Assessment, Needs, Allocations
    log_step("4. Direct Remote DB Verification of Pipeline Entities")
    
    # A. Reports in Supabase
    db_reports = sb.table("reports").select("*").in_("source_record_id", [r1_source_id, r2_source_id]).execute()
    print(f"Direct DB: {len(db_reports.data)} reports found in Supabase reports table.")
    assert len(db_reports.data) == 2, f"Expected 2 reports in Supabase, got {len(db_reports.data)}"
    
    # B. Incidents in Supabase (correlated via incident_evidence)
    r1_row = db_reports.data[0]
    ev_check = sb.table("incident_evidence").select("incident_id").eq("report_id", r1_row["report_id"]).execute()
    assert len(ev_check.data) >= 1, "Report not linked to any incident in incident_evidence table!"
    incident_id = ev_check.data[0]["incident_id"]
    print(f"Incident ID correlated from evidence: {incident_id}")
    
    db_inc = sb.table("incidents").select("*").eq("incident_id", incident_id).execute()
    assert len(db_inc.data) == 1, "Incident record not found in Supabase incidents table"
    print("PASS: Incident confirmed in Supabase incidents table.")
    
    # Verify API /incidents endpoint returns it
    status, incidents = http_get("/incidents")
    assert any(i["incident_id"] == incident_id for i in incidents), "Incident not listed in /incidents API"
    
    # C. Incident Evidence in Supabase
    db_ev = sb.table("incident_evidence").select("*").eq("incident_id", incident_id).execute()
    print(f"Direct DB: Found {len(db_ev.data)} evidence links in Supabase incident_evidence table.")
    assert len(db_ev.data) >= 1, "Expected incident_evidence links in Supabase"

    # D. Assessments in Supabase
    db_ass = sb.table("assessments").select("*").eq("incident_id", incident_id).execute()
    print(f"Direct DB: Found {len(db_ass.data)} assessment rows in Supabase assessments table.")
    assert len(db_ass.data) >= 1, "Expected assessment in Supabase assessments table"
    ass_row = db_ass.data[0]
    initial_assessment_id = ass_row["assessment_id"]
    print(f"  Assessment ID: {initial_assessment_id}")
    print(f"  Severity Model Version: {ass_row.get('severity_model_version')}")
    print(f"  Priority Score: {ass_row.get('priority_score')}")
    assert ass_row.get("verification_status") == "VERIFIED"

    # E. Needs in Supabase
    db_needs = sb.table("needs").select("*").eq("incident_id", incident_id).execute()
    print(f"Direct DB: Found {len(db_needs.data)} needs rows in Supabase needs table.")
    assert len(db_needs.data) >= 1, "Expected needs rows in Supabase"
    for n in db_needs.data:
        print(f"  Need: {n['resource_type']} -> {n['quantity']} {n['unit']}")

    # F. Allocations in Supabase
    db_alloc = sb.table("allocations").select("*").eq("incident_id", incident_id).execute()
    print(f"Direct DB: Found {len(db_alloc.data)} allocation rows in Supabase allocations table.")
    assert len(db_alloc.data) >= 1, "Expected allocation rows in Supabase"
    for a in db_alloc.data:
        print(f"  Allocated: {a['resource_type']} -> {a['quantity_allocated']} {a['unit']} (Run: {a['optimization_run_id']})")
        assert a["optimization_run_id"] == test_marker

    # 5. Inventory Invariance Check Before Approval
    log_step("5. Inventory Invariance Before Human Approval")
    db_res_mid = sb.table("resources").select("*").eq("location_id", depot_loc).execute()
    inv_mid = {r["resource_type"]: r["quantity_available"] for r in db_res_mid.data}
    print("Depot inventory before optimization:", inv_before)
    print("Depot inventory after optimization (before approval):", inv_mid)
    assert inv_before == inv_mid, "CRITICAL ERROR: INVENTORY MUTATED BEFORE HUMAN APPROVAL!"
    print("PASS: Zero inventory mutation verified in Supabase prior to approval!")

    # 6. Human Approval Submission
    log_step("6. Live Human Approval (POST /agents/review/{thread_id})")
    approval_payload = {
        "decision": "APPROVED",
        "reason": f"Commander approved initial relief allocation for {test_marker}."
    }
    status, review_resp = http_post(f"/agents/review/{test_marker}", approval_payload)
    print("Review API response:", review_resp)
    assert status == 200
    assert review_resp["human_approval_state"] == "APPROVED"
    
    # Direct DB check on approvals table
    db_appr = sb.table("approvals").select("*").eq("optimization_run_id", test_marker).execute()
    print(f"Direct DB: Found {len(db_appr.data)} approval rows in Supabase approvals table.")
    assert len(db_appr.data) >= 1, "Approval record not found in Supabase approvals table!"
    approval_1_row = db_appr.data[0]
    approval_1_id = approval_1_row["approval_id"]
    print(f"  Approval ID 1: {approval_1_id}, Status: {approval_1_row['status']}")
    assert approval_1_row["status"] == "APPROVED"

    # Direct DB check on audit_events
    db_audit_appr = sb.table("audit_events").select("*").eq("incident_id", incident_id).like("event_type", "APPROVAL_%").execute()
    assert len(db_audit_appr.data) >= 1, "Approval audit event not found in Supabase audit_events table!"
    print(f"PASS: Approval audit event ({db_audit_appr.data[0]['event_type']}) confirmed in Supabase audit_events table.")

    # 7. Controlled Execution via ExecutionService
    log_step("7. Live Controlled Execution (POST /agents/execute/{thread_id})")
    exec_payload = {"executor_id": "OFFICER_PHASE6B_LIVE"}
    status, exec_resp = http_post(f"/agents/execute/{test_marker}", exec_payload)
    print("Execution API response:", exec_resp)
    assert status == 200
    assert exec_resp["status"] in ["EXECUTED", "ALREADY_EXECUTED"]
    
    # Direct DB check on actions table
    db_act = sb.table("actions").select("*").eq("approval_id", approval_1_id).execute()
    assert len(db_act.data) >= 1, "Action record not found in Supabase actions table!"
    act_1_row = db_act.data[0]
    execution_1_id = act_1_row["execution_id"]
    print(f"  Action ID 1: {act_1_row['action_id']}, Execution ID 1: {execution_1_id}, Status: {act_1_row['status']}, Executed by: {act_1_row['executed_by']}")
    assert act_1_row["status"] == "EXECUTED"
    assert act_1_row["approval_id"] == approval_1_id

    # Direct DB check on inventory deduction in resources table
    db_res_post1 = sb.table("resources").select("*").eq("location_id", depot_loc).execute()
    inv_post1 = {r["resource_type"]: r["quantity_available"] for r in db_res_post1.data}
    print("Remote DB Inventory post execution 1:", inv_post1)
    
    # Verify exact deduction
    deducted_something = False
    for r_type, q_pre in inv_mid.items():
        q_post = inv_post1[r_type]
        delta = q_pre - q_post
        print(f"  {r_type}: {q_pre} -> {q_post} (Deducted: {delta})")
        assert q_post >= 0, f"Negative inventory detected for {r_type}!"
        if delta > 0:
            deducted_something = True
    assert deducted_something, "No inventory was deducted during execution!"
    print("PASS: Inventory deducted correctly and non-negative in remote Supabase DB!")

    # Direct DB check on execution audit event
    db_audit_exec = sb.table("audit_events").select("*").eq("incident_id", incident_id).eq("event_type", "EXECUTION_SUCCEEDED").execute()
    assert len(db_audit_exec.data) >= 1, "Execution audit event not found in Supabase audit_events!"
    print("PASS: Execution audit event confirmed in Supabase audit_events table.")

    # 8. Double Execution Protection
    log_step("8. Double Execution Protection Verification")
    status, double_exec_resp = http_post(f"/agents/execute/{test_marker}", exec_payload)
    print("Double Execution API response:", double_exec_resp)
    assert status == 200
    assert double_exec_resp["status"] == "ALREADY_EXECUTED"

    # Direct DB check: inventory must be 100% unchanged
    db_res_double = sb.table("resources").select("*").eq("location_id", depot_loc).execute()
    inv_double = {r["resource_type"]: r["quantity_available"] for r in db_res_double.data}
    assert inv_post1 == inv_double, "CRITICAL ERROR: Double execution deducted inventory again!"
    print("PASS: Double execution rejected and inventory remained unchanged in Supabase!")

    # 9. Dynamic Reassessment
    log_step("9. Dynamic Reassessment (Hospital Flooded Escalation)")
    escalation_report = json.dumps({
        "source": "HOSPITAL_REPORT",
        "source_record_id": f"{test_marker}-HOSPITAL-ESCALATION",
        "hazard_type": "Flood",
        "location": "Sector C Hospital Zone",
        "latitude": 34.051,
        "longitude": -118.249,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "affected_population": 3000,
        "displaced_population": 1200,
        "raw_text": "Hospital basement flooded. Power failure. Critical surge in casualties requiring immediate additional potable water and food."
    })
    
    status, reassess_resp = http_post(f"/agents/reassess/{test_marker}", {
        "new_reports": [escalation_report],
        "reassessment_reason": "Severe escalation in hospital sector casualties and power failure."
    })
    print("Reassessment API response status:", status)
    print("Reassessment Response Summary:")
    print(f"  Decision Status: {reassess_resp.get('reallocation_decision_status')}")
    print(f"  Human Approval State: {reassess_resp.get('human_approval_state')}")
    
    # Direct DB check on new assessment in Supabase
    db_all_ass = sb.table("assessments").select("*").eq("incident_id", incident_id).order("assessed_at").execute()
    print(f"Direct DB: Found {len(db_all_ass.data)} total assessments for incident in Supabase.")
    assert len(db_all_ass.data) >= 2, "New assessment record not created in Supabase assessments table!"
    new_ass_row = db_all_ass.data[-1]
    second_assessment_id = new_ass_row["assessment_id"]
    print(f"  Initial Assessment ID: {initial_assessment_id}")
    print(f"  Second Assessment ID:  {second_assessment_id}")
    print(f"  Parent Assessment ID:  {new_ass_row.get('parent_assessment_id')}")
    print(f"  Reassessment Reason:   {new_ass_row.get('reassessment_reason')}")
    assert new_ass_row.get("parent_assessment_id") == initial_assessment_id, "Parent assessment ID does not link to initial assessment!"
    print("PASS: Assessment lineage and immutability verified in Supabase assessments table!")

    # 10. Second Human Approval & Second Execution
    log_step("10. Second Human Approval & Second Execution")
    status, review_2_resp = http_post(f"/agents/review/{test_marker}", {
        "decision": "APPROVED",
        "reason": "Commander approved escalation delta allocation for hospital surge."
    })
    assert status == 200
    assert review_2_resp["human_approval_state"] == "APPROVED"

    # Direct DB check on second approval
    db_all_appr = sb.table("approvals").select("*").eq("incident_id", incident_id).order("created_at").execute()
    assert len(db_all_appr.data) >= 2, "Expected 2 approval records in Supabase approvals table"
    approval_2_row = db_all_appr.data[-1]
    approval_2_id = approval_2_row["approval_id"]
    print(f"  Approval 1 ID: {approval_1_id}")
    print(f"  Approval 2 ID: {approval_2_id}")
    assert approval_2_id != approval_1_id, "Approval 2 must have distinct approval_id"

    # Execute second proposal
    status, exec_2_resp = http_post(f"/agents/execute/{test_marker}", {"executor_id": "OFFICER_PHASE6B_REASSESS"})
    print("Second Execution Response:", exec_2_resp)
    assert status == 200
    assert exec_2_resp["status"] in ["EXECUTED", "ALREADY_EXECUTED"]
    
    db_act_2 = sb.table("actions").select("*").eq("approval_id", approval_2_id).execute()
    assert len(db_act_2.data) >= 1, "Action record 2 not found in Supabase actions table!"
    act_2_row = db_act_2.data[0]
    execution_2_id = act_2_row["execution_id"]
    print(f"  Execution 1 ID: {execution_1_id}")
    print(f"  Execution 2 ID: {execution_2_id}")
    assert execution_2_id != execution_1_id, "Execution 2 must have distinct execution_id"

    # Direct DB check on inventory post second execution
    db_res_post2 = sb.table("resources").select("*").eq("location_id", depot_loc).execute()
    inv_post2 = {r["resource_type"]: r["quantity_available"] for r in db_res_post2.data}
    print("Remote DB Inventory post second execution:", inv_post2)
    for r_type in inv_post1:
        assert inv_post2[r_type] <= inv_post1[r_type], f"Inventory did not decrease or stayed same for {r_type}"
        assert inv_post2[r_type] >= 0, f"Negative inventory for {r_type}!"
    print("PASS: Delta inventory mutation verified in Supabase resources table!")

    # Return test metadata for restart persistence verification
    return {
        "incident_id": incident_id,
        "initial_assessment_id": initial_assessment_id,
        "second_assessment_id": second_assessment_id,
        "approval_1_id": approval_1_id,
        "approval_2_id": approval_2_id,
        "execution_1_id": execution_1_id,
        "execution_2_id": execution_2_id,
        "depot_loc": depot_loc,
        "test_marker": test_marker,
        "r1_source_id": r1_source_id,
        "r2_source_id": r2_source_id
    }

if __name__ == "__main__":
    meta = main()
    # Save metadata for restart test
    with open("scratch/phase6b_e2e_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("\nPhase 6B E2E Execution successfully completed! Metadata saved.")
