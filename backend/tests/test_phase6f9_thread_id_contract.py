"""
Phase 6F.9 / 6F.10 Contract & Persistence Verification Suite: LangGraph thread_id vs OR-Tools optimization_run_id.

Tests focus on ensuring:
- thread_id and optimization_run_id are distinct and separate.
- /agents/run returns actual LangGraph thread_id used in graph config.
- PENDING & APPROVED approvals persist and preserve original thread_id.
- Governance returns actual thread_id or null for older records safely.
- LangGraph review/resume uses exact thread_id without prefix checking.
- optimization_run_id cannot be passed as thread_id to /agents/review.
- Supabase repo payload includes thread_id field.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.services.agent_service import AgentService
from app.services.approval_service import ApprovalService
from app.api.schemas.internal import AgentRunRequest, AgentResumeRequest, ExecutionRequest, ApprovalRecord
from app.db.dependencies import get_approval_repository

client = TestClient(app)

def test_agents_run_returns_actual_thread_id_and_separate_optimization_run_id():
    """Requirement 5, 10: /agents/run returns actual thread_id distinct from optimization_run_id."""
    payload = {
        "raw_reports": ["Heavy flooding reported in Kurla West area, 500 displaced."]
    }
    response = client.post("/agents/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "thread_id" in data
    assert data["thread_id"] is not None
    
    # run_id / optimization_run_id is returned separately when present
    if data.get("run_id"):
        assert data["thread_id"] != data["run_id"]

def test_caller_supplied_run_id_semantics_preserved():
    """Requirement 4, 10: Caller-supplied run_id semantics remain unchanged."""
    custom_run_id = f"custom-run-{uuid4().hex[:8]}"
    payload = {
        "run_id": custom_run_id,
        "raw_reports": ["Landslide in suburban area requiring rescue."]
    }
    response = client.post("/agents/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # caller-supplied run_id is preserved
    assert data["run_id"] == custom_run_id
    # thread_id matches exact invocation identity
    assert data["thread_id"] == custom_run_id

def test_wrong_optimization_run_id_cannot_be_used_as_thread_id():
    """Requirement 2, 6, 10: Passing optimization_run_id ('opt-...') as thread_id fails to resume graph state."""
    fake_opt_id = f"opt-{uuid4()}"
    payload = {
        "decision": "APPROVED",
        "reason": "Testing invalid thread ID"
    }
    response = client.post(f"/agents/review/{fake_opt_id}", json=payload)
    assert response.status_code == 400
    assert "No active graph state found" in response.json()["detail"]

def test_langgraph_resume_uses_exact_thread_id():
    """Requirement 5, 6, 10: Approval sends actual thread_id and resumes LangGraph checkpoint."""
    # 1. Trigger agent run to interrupt at human_review
    run_resp = client.post("/agents/run", json={
        "raw_reports": ["Severe storm surge in Coastal Zone B, 1000 affected."]
    })
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    thread_id = run_data["thread_id"]
    assert thread_id is not None

    # 2. Submit approval using the EXACT thread_id
    review_resp = client.post(f"/agents/review/{thread_id}", json={
        "decision": "APPROVED",
        "reason": "Approved by automated contract test"
    })
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    
    assert review_data["thread_id"] == thread_id
    assert review_data["human_approval_state"] == "APPROVED"
    assert review_data["status"] == "APPROVED"

def test_governance_returns_persisted_thread_id():
    """Phase 6F.10: Governance endpoint returns persisted thread_id from PENDING/APPROVED approval."""
    approval_repo = get_approval_repository()
    inc_id = str(uuid4())
    opt_id = f"opt-{uuid4().hex[:8]}"
    test_thread_id = f"thread-gov-{uuid4().hex[:8]}"

    pending_appr = ApprovalRecord(
        incident_id=inc_id,
        optimization_run_id=opt_id,
        thread_id=test_thread_id,
        status="PENDING"
    )
    approval_repo.upsert(pending_appr)

    # Fetch governance for this incident
    gov_resp = client.get(f"/incidents/{inc_id}/governance")
    assert gov_resp.status_code == 200
    gov_data = gov_resp.json()

    # Governance must return the persisted thread_id
    assert gov_data["thread_id"] == test_thread_id
    assert gov_data["optimization_run_id"] == opt_id

def test_approval_transition_preserves_thread_id():
    """Phase 6F.10: Transitioning PENDING -> APPROVED preserves original thread_id."""
    approval_repo = get_approval_repository()
    svc = ApprovalService(approval_repo)
    
    inc_id = str(uuid4())
    opt_id = f"opt-{uuid4().hex[:8]}"
    orig_thread_id = f"thread-orig-{uuid4().hex[:8]}"

    # Create PENDING approval
    pending_appr = ApprovalRecord(
        incident_id=inc_id,
        optimization_run_id=opt_id,
        thread_id=orig_thread_id,
        status="PENDING"
    )
    approval_repo.upsert(pending_appr)

    # Transition to APPROVED
    approved_rec = svc.record_approval(
        incident_id=inc_id,
        optimization_run_id=opt_id,
        decision="APPROVED",
        reason="Approved in unit test",
        thread_id=orig_thread_id
    )

    assert approved_rec.approval_id == pending_appr.approval_id
    assert approved_rec.thread_id == orig_thread_id
    assert approved_rec.status == "APPROVED"

def test_governance_returns_null_thread_id_for_old_records():
    """Requirement 8, 10: Governance returns thread_id if available, or null for older records without faking."""
    # 1. Create a dummy incident with an older approval record (thread_id is None)
    incident_id = str(uuid4())
    approval_repo = get_approval_repository()
    old_appr = ApprovalRecord(
        incident_id=incident_id,
        optimization_run_id=f"opt-old-{uuid4().hex[:8]}",
        thread_id=None,
        status="APPROVED"
    )
    approval_repo.upsert(old_appr)

    # 2. Fetch governance
    gov_resp = client.get(f"/incidents/{incident_id}/governance")
    assert gov_resp.status_code == 200
    gov_data = gov_resp.json()
    
    # Must be null, not fake or derived from optimization_run_id
    assert gov_data["thread_id"] is None
    assert gov_data["optimization_run_id"] == old_appr.optimization_run_id

def test_execution_uses_correct_identity_and_prevents_unapproved_opt_id():
    """Requirement 7, 10: Execution verifies approval authorization cleanly."""
    fake_thread_id = f"custom-thread-{uuid4().hex[:8]}"
    exec_resp = client.post(f"/agents/execute/{fake_thread_id}", json={
        "optimization_run_id": "opt-unapproved-12345"
    })
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] in ["NOT_APPROVED", "INVALID_PROPOSAL", "FAILED"]
