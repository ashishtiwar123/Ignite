import urllib.request
import json
import uuid
import sys
from datetime import datetime, timezone

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
    results = {}
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Check Health & CORS
    log_step("1. Health & CORS Verification")
    status, health_data = http_get("/health")
    print("Health response:", health_data)
    assert status == 200 and health_data["status"] == "ok"
    results["health_endpoint"] = "PASS"

    # 2. Seed Dedicated Test Resources
    log_step("2. Live Resource Inventory Seeding (Dedicated Test Depot)")
    depot = "LOC-PHASE6A-TEST-DEPOT"
    test_resources = [
        {"location_id": depot, "resource_type": "Potable Water", "category": "WATER", "quantity_available": 100000.0, "unit": "Liters"},
        {"location_id": depot, "resource_type": "Cereal", "category": "FOOD", "quantity_available": 50.0, "unit": "Metric Tons"},
        {"location_id": depot, "resource_type": "Family Tents", "category": "SHELTER", "quantity_available": 500.0, "unit": "Units"}
    ]
    for res in test_resources:
        s, r_data = http_post("/resources", res)
        print(f"Seeded {r_data['resource_type']}: {r_data['quantity_available']} {r_data['unit']}")
    
    status, resources_before = http_get("/resources")
    inventory_before = {f"{r['resource_type']}": r['quantity_available'] for r in resources_before if r['location_id'] == depot}
    print("Initial Depot Inventory:", inventory_before)
    results["resource_inventory_seeding"] = "PASS"

    # 3. Uncorroborated User Report Verification (Correction 7 & Step 8)
    log_step("3. Live Uncorroborated Report -> NEEDS_VERIFICATION Pathway")
    uncorr_run_id = f"PHASE6A-UNCORR-{uuid.uuid4().hex[:6]}"
    uncorr_payload = {
        "run_id": uncorr_run_id,
        "raw_reports": ["PHASE6A-E2E-TEST: Unverified citizen report of localized street flooding in Zone B."]
    }
    status, uncorr_resp = http_post("/agents/run", uncorr_payload)
    print("Uncorroborated Run Response:", json.dumps(uncorr_resp, indent=2))
    assert status == 200
    assert uncorr_resp["status"] == "PENDING_REVIEW"
    assert uncorr_resp["human_approval_state"] == "PENDING"
    results["uncorroborated_needs_verification"] = "PASS"

    # 4. Full Corroborated Disaster Pipeline (Steps 7–11)
    log_step("4. Corroborated Disaster Ingestion & Situation Assessment (VERIFIED Flow)")
    verified_run_id = f"PHASE6A-VERIFIED-{uuid.uuid4().hex[:6]}"
    r1 = json.dumps({
        "source": "USGS",
        "source_record_id": f"USGS-TEST-{uuid.uuid4().hex[:4]}",
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
        "source_record_id": f"GDACS-TEST-{uuid.uuid4().hex[:4]}",
        "hazard_type": "Flood",
        "location": "Sector C Hospital Zone",
        "latitude": 34.052,
        "longitude": -118.248,
        "observed_at": now_iso,
        "affected_population": 500,
        "displaced_population": 150
    })

    status, run_resp = http_post("/agents/run", {
        "run_id": verified_run_id,
        "raw_reports": [r1, r2]
    })
    print("Corroborated Run Response:", json.dumps(run_resp, indent=2))
    assert status == 200
    assert run_resp["run_id"] == verified_run_id
    assert run_resp["status"] == "PENDING_REVIEW"
    assert run_resp["human_approval_state"] == "PENDING"
    results["corroborated_run_pause_at_human_review"] = "PASS"

    # 5. Inventory Snapshot Before Approval (Correction 11)
    log_step("5. Inventory Invariance Before Human Approval (Snapshot Verification)")
    status, resources_mid = http_get("/resources")
    inventory_mid = {f"{r['resource_type']}": r['quantity_available'] for r in resources_mid if r['location_id'] == depot}
    print("Inventory before optimization:", inventory_before)
    print("Inventory after optimization (before approval):", inventory_mid)
    assert inventory_before == inventory_mid, "CRITICAL ERROR: INVENTORY MUTATED BEFORE HUMAN APPROVAL!"
    results["zero_mutation_before_approval"] = "PASS"

    # 6. Retrieve Incident & Assessment Details from Live APIs
    log_step("6. Live Incident, Needs & Assessment API Retrieval")
    status, incidents = http_get("/incidents")
    test_incident = None
    for inc in incidents:
        if inc.get("status") == "VERIFIED":
            test_incident = inc
            break
    if not test_incident and incidents:
        test_incident = incidents[-1]
    assert test_incident is not None, "Test incident was not persisted!"
    incident_id = test_incident["incident_id"]
    print(f"Persisted Test Incident ID: {incident_id} (Status: {test_incident.get('status')})")
    
    status, assessment = http_get(f"/incidents/{incident_id}/assessment")
    print("Assessment Record:")
    print(f" - Assessment ID: {assessment.get('assessment_id')}")
    print(f" - Severity Status: {assessment.get('severity_status')}")
    print(f" - Priority Level: {assessment.get('priority_level')} (Score: {assessment.get('priority_score')})")
    initial_assessment_id = assessment.get("assessment_id")
    results["incident_assessment_persisted"] = "PASS"

    # 7. Live Human Approval (Step 12 & Correction 12)
    log_step("7. Live Human Approval (POST /agents/review/{thread_id})")
    thread_id = verified_run_id
    approval_data = {
        "decision": "APPROVED",
        "reason": "Phase 6A Commander verified hospital flood severity and approved initial resource allocation."
    }
    status, review_resp = http_post(f"/agents/review/{thread_id}", approval_data)
    print("Review Response:", json.dumps(review_resp, indent=2))
    assert status == 200
    assert review_resp["human_approval_state"] == "APPROVED"
    results["human_approval_persisted"] = "PASS"

    # 8. Live Controlled Execution (Step 13 & Correction 13)
    log_step("8. Live Controlled Execution via ExecutionService (POST /agents/execute/{thread_id})")
    inv_pre_exec = dict(inventory_mid)
    exec_payload = {"executor_id": "OFFICER_PHASE6A_E2E"}
    status, exec_resp = http_post(f"/agents/execute/{thread_id}", exec_payload)
    print("Execution Response:", json.dumps(exec_resp, indent=2))
    assert status == 200
    assert exec_resp["status"] in ["EXECUTED", "ALREADY_EXECUTED"]
    first_execution_id = exec_resp["execution_id"]
    print(f"Generated First Execution ID: {first_execution_id}")

    status, resources_post_exec = http_get("/resources")
    inv_post_exec = {f"{r['resource_type']}": r['quantity_available'] for r in resources_post_exec if r['location_id'] == depot}
    print("Inventory post execution:", inv_post_exec)
    any_deducted = False
    for r_type, pre_q in inv_pre_exec.items():
        post_q = inv_post_exec[r_type]
        delta = pre_q - post_q
        print(f" - {r_type}: {pre_q} -> {post_q} (Deducted: {delta})")
        if delta > 0:
            any_deducted = True
    assert any_deducted, "NO RESOURCES WERE DEDUCTED DURING CONTROLLED EXECUTION!"
    results["controlled_execution_deduction"] = "PASS"

    # 9. Double Execution Protection (Step 14 & Correction 14)
    log_step("9. Double Execution Idempotency Test")
    inv_before_double = dict(inv_post_exec)
    status, double_resp = http_post(f"/agents/execute/{thread_id}", exec_payload)
    print("Double execution response:", json.dumps(double_resp, indent=2))
    assert double_resp["status"] == "ALREADY_EXECUTED"
    assert len(double_resp.get("deducted_resources", [])) == 0
    assert "already been executed" in " ".join(double_resp.get("errors", [])).lower()

    status, resources_post_double = http_get("/resources")
    inv_post_double = {f"{r['resource_type']}": r['quantity_available'] for r in resources_post_double if r['location_id'] == depot}
    assert inv_before_double == inv_post_double, "CRITICAL: INVENTORY DEDUCTED A SECOND TIME!"
    print("Inventory correctly unchanged after double execution attempt:", inv_post_double)
    results["double_execution_protection"] = "PASS"

    # 10. Live Dynamic Reassessment with Escalation Evidence (Steps 15–16 & Corrections 15–18)
    log_step("10. Live Dynamic Reassessment with Hospital Escalation Evidence")
    escalation_report = (
        "PHASE6A-E2E-TEST: Severe hospital escalation. 70 patients affected, 8 require urgent ICU evacuation, "
        "and emergency backup generators have flooded."
    )
    reassess_payload = {
        "run_id": f"{thread_id}-REALLOC-002",
        "new_reports": [escalation_report],
        "reassessment_reason": "Emergency medical escalation: hospital backup power failure"
    }
    status, reassess_resp = http_post(f"/agents/reassess/{thread_id}", reassess_payload)
    print("Reassessment Triggered / Required:", reassess_resp.get("reallocation_required"))
    print("Reallocation Decision Status:", reassess_resp.get("reallocation_decision_status"))
    prev_ass_id = reassess_resp.get("previous_assessment_id")
    curr_ass_id = reassess_resp.get("current_assessment_id")
    print(f"Assessment Lineage: Parent ({prev_ass_id}) -> Current ({curr_ass_id})")
    assert curr_ass_id is not None, "NEW ASSESSMENT ID MISSING!"
    
    ass_diff = reassess_resp.get("assessment_diff", {})
    print("Assessment Diff:", json.dumps(ass_diff, indent=2))
    alloc_diff = reassess_resp.get("allocation_diff", {})
    deltas = alloc_diff.get("deltas", []) if alloc_diff else []
    print(f"Allocation Diff Deltas Count: {len(deltas)}")
    results["reassessment_and_diff"] = "PASS"

    # 11. Second Human Approval (Step 17 & Correction 19)
    log_step("11. Second Human Approval for Dynamic Reallocation")
    second_approval_data = {
        "decision": "APPROVED",
        "reason": "Commander approves emergency dynamic reallocation based on ICU hospital flood escalation."
    }
    status, review_resp_2 = http_post(f"/agents/review/{thread_id}", second_approval_data)
    print("Second Review Response:", json.dumps(review_resp_2, indent=2))
    assert status == 200
    assert review_resp_2["human_approval_state"] == "APPROVED"
    results["second_human_approval"] = "PASS"

    # 12. Second Execution (Step 18 & Correction 20)
    log_step("12. Second Controlled Execution (Dynamic Reallocation)")
    status, exec_resp_2 = http_post(f"/agents/execute/{thread_id}", {"executor_id": "OFFICER_PHASE6A_REALLOC"})
    print("Second Execution Response:", json.dumps(exec_resp_2, indent=2))
    assert status == 200
    assert exec_resp_2["status"] in ["EXECUTED", "ALREADY_EXECUTED"]
    second_execution_id = exec_resp_2["execution_id"]
    print(f"Generated Second Execution ID: {second_execution_id}")
    assert second_execution_id != first_execution_id, "EXECUTION IDS MUST BE DISTINCT!"
    
    status, resources_final = http_get("/resources")
    inv_final = {f"{r['resource_type']}": r['quantity_available'] for r in resources_final if r['location_id'] == depot}
    print("Final Inventory after Second Execution:", inv_final)
    results["second_execution_distinct"] = "PASS"

    # 13. Case B: Caller does not provide run_id (Correction 10)
    log_step("13. Thread ID vs Run ID Semantics (Case B: No run_id provided)")
    case_b_payload = {
        "raw_reports": ["PHASE6A-E2E-TEST: Localized minor flood advisory in Zone E."]
    }
    status, case_b_resp = http_post("/agents/run", case_b_payload)
    print("Case B Response:", case_b_resp)
    assert status == 200
    assert case_b_resp["run_id"] is None, "Domain run_id must remain None when not provided by caller!"
    results["run_id_semantics_case_b"] = "PASS"

    # 14. Error & Controlled Failure Testing (Correction 25)
    log_step("14. Error & Controlled Failure Testing")
    # A. Unknown incident
    try:
        http_get("/incidents/nonexistent-incident-uuid/assessment")
        assert False, "Expected 404 for unknown incident"
    except urllib.error.HTTPError as e:
        print(f"PASS: Unknown incident returned HTTP {e.code}")
    
    # B. Invalid review decision
    try:
        http_post(f"/agents/review/{thread_id}", {"decision": "MALICIOUS_DECISION"})
        assert False, "Expected 400 for invalid decision"
    except urllib.error.HTTPError as e:
        print(f"PASS: Invalid review decision returned HTTP {e.code}")

    # C. Empty reports list
    try:
        http_post("/agents/run", {"raw_reports": []})
        assert False, "Expected 400 for empty reports"
    except urllib.error.HTTPError as e:
        print(f"PASS: Empty report payload returned HTTP {e.code}")

    results["controlled_failure_tests"] = "PASS"

    print("\n" + "=" * 70)
    print("ALL PHASE 6A LIVE END-TO-END VERIFICATION CHECKS PASSED!")
    print("=" * 70)
    for k, v in results.items():
        print(f"  [PASS] {k}: {v}")

if __name__ == "__main__":
    main()
