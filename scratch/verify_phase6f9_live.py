"""
Real Live Verification Script for Phase 6F.9: LangGraph thread_id / optimization_run_id contract.

Runs against the live FastAPI server on http://localhost:8001.
"""

import urllib.request
import json
import uuid
import sys

BASE_URL = "http://localhost:8001"

def http_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def http_get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def run_live_verification():
    print("=" * 70)
    print("PHASE 6F.9 REAL LIVE VERIFICATION")
    print("=" * 70)

    # 1. Trigger fresh POST /agents/run
    print("\n1. Executing POST /agents/run with fresh report...")
    run_payload = {
        "raw_reports": [
            f"Live Verification Report {uuid.uuid4().hex[:6]}: Heavy monsoon inundation in Dadar West, 800 affected."
        ]
    }
    status, run_resp = http_post("/agents/run", run_payload)
    print(f"   Response Code: {status}")
    print(f"   AgentRunResponse: {json.dumps(run_resp, indent=2)}")

    thread_id = run_resp.get("thread_id")
    run_id = run_resp.get("run_id")
    approval_state = run_resp.get("human_approval_state")

    assert thread_id is not None, "FAILED: thread_id is None!"
    assert approval_state == "PENDING", f"FAILED: Expected PENDING, got {approval_state}"

    print(f"\nCaptured Identifiers:")
    print(f"   thread_id (LangGraph Checkpoint): {thread_id}")
    print(f"   run_id / optimization_run_id (Proposal): {run_id}")

    assert thread_id != run_id, "FAILED: thread_id and run_id must NOT be equal!"

    # 2. Query Governance Endpoint
    print("\n2. Executing GET /incidents/{incident_id}/governance...")
    # Extract incident_id from reports/candidates if available or check recent incidents
    incidents_status, incidents = http_get("/incidents")
    assert incidents_status == 200 and len(incidents) > 0, "FAILED: No incidents found!"
    
    # Target latest incident
    latest_inc_id = incidents[0]["incident_id"]
    gov_status, gov_resp = http_get(f"/incidents/{latest_inc_id}/governance")
    print(f"   Governance Response: {json.dumps(gov_resp, indent=2)}")
    
    opt_run_id = gov_resp.get("optimization_run_id")
    approval_id = gov_resp.get("approval_id")
    gov_thread_id = gov_resp.get("thread_id")

    print(f"\nPersisted Governance Identifiers:")
    print(f"   approval_id: {approval_id}")
    print(f"   optimization_run_id: {opt_run_id}")
    print(f"   thread_id in governance: {gov_thread_id}")

    # 3. Test Rejection when using optimization_run_id as thread_id in URL
    print("\n3. Testing Rejection: POST /agents/review/<OPTIMIZATION_RUN_ID>...")
    bad_url_opt_id = opt_run_id or "opt-fake-12345"
    try:
        http_post(f"/agents/review/{bad_url_opt_id}", {"decision": "APPROVED", "reason": "Should Fail"})
        print("   FAILED: Should have rejected optimization_run_id as thread_id!")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        print(f"   Correctly Rejected HTTP {e.code}: {body.get('detail')}")
        assert e.code == 400, f"Expected 400, got {e.code}"

    # 4. Resume LangGraph Checkpoint using ACTUAL thread_id in URL
    print(f"\n4. Resuming Graph: POST /agents/review/{thread_id}...")
    review_status, review_resp = http_post(f"/agents/review/{thread_id}", {
        "decision": "APPROVED",
        "reason": "Live test approval by Phase 6F.9 automated verifier"
    })
    print(f"   Response Code: {review_status}")
    print(f"   Review Response: {json.dumps(review_resp, indent=2)}")

    assert review_status == 200, f"Expected 200, got {review_status}"
    assert review_resp.get("thread_id") == thread_id, "FAILED: Returned thread_id mismatch!"
    assert review_resp.get("human_approval_state") == "APPROVED", "FAILED: Approval state was not APPROVED!"

    print("\n" + "=" * 70)
    print("LIVE VERIFICATION SUCCESSFUL!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_verification()
