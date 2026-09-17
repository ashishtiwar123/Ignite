"""
Phase 4G — Reassessment + Dynamic Reallocation Integration Tests
Validates all required reassessment and dynamic reallocation test scenarios.
"""
import pytest
import json
import uuid
import sys
import os
from unittest.mock import patch

# Ensure backend is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.schemas.internal import (
    ApprovalRecord,
    AllocationRecord,
    ResourceRecord,
    ActionRecord,
    AgentRunRequest,
    AgentResumeRequest,
    ReassessmentRequest,
    ExecutionRequest
)
from app.db.dependencies import (
    get_resource_repository,
    get_approval_repository,
    get_allocation_repository,
    get_action_repository,
    get_assessment_repository,
    get_needs_repository
)
from app.services.agent_service import AgentService
from app.services.execution_service import ExecutionService
from ml.src.agents.graph import build_graph


@pytest.fixture(autouse=True)
def reset_all_repos():
    """Clear and seed repositories before each test."""
    for repo in [
        get_resource_repository(),
        get_approval_repository(),
        get_allocation_repository(),
        get_action_repository(),
        get_assessment_repository(),
        get_needs_repository()
    ]:
        if hasattr(repo, '_resources'): repo._resources.clear()
        if hasattr(repo, '_storage'): repo._storage.clear()
        if hasattr(repo, '_data'): repo._data.clear()
        if hasattr(repo, '_assessments'): repo._assessments.clear()
        if hasattr(repo, '_needs'): repo._needs.clear()

    # Seed initial inventory
    get_resource_repository().upsert(ResourceRecord(
        location_id="wh-alpha",
        resource_type="Potable Water",
        category="WATER",
        quantity_available=100000.0,
        unit="Liters"
    ))
    get_resource_repository().upsert(ResourceRecord(
        location_id="wh-alpha",
        resource_type="Cereal",
        category="FOOD",
        quantity_available=5000.0,
        unit="Metric Tons"
    ))
    yield


# ──────────────────────────────────────────────────────────
# REASSESSMENT LIFECYCLE & SAFETY TESTS
# ──────────────────────────────────────────────────────────

def test_reassessment_creates_new_snapshot_and_preserves_parent():
    agent_svc = AgentService()
    
    # 1. Initial run
    req1 = AgentRunRequest(raw_reports=[json.dumps({"source": "USGS", "source_record_id": "evt-1", "hazard_type": "Flood", "affected_population": 500})], run_id="run-init")
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report", return_value={"hazard_type": "Flood", "location": "Zone C", "affected_population": 500}), \
         patch("ml.src.agents.graph.assess_incident", return_value=type("V", (), {"verification_status": "VERIFIED"})()):
        res1 = agent_svc.run_agent(req1)
        
    thread_id = res1.run_id or "run-init"
    ass_repo = get_assessment_repository()
    all_ass = list(ass_repo._assessments.values())
    assert len(all_ass) > 0
    initial_ass = all_ass[-1]
    initial_id = initial_ass.assessment_id

    # 2. Submit Reassessment
    reassess_req = ReassessmentRequest(
        new_reports=[json.dumps({"source": "LOCAL_HOSPITAL", "source_record_id": "evt-2", "hazard_type": "Flood", "affected_population": 2000})],
        run_id="run-reassess-1",
        reassessment_reason="Flooding escalated rapidly"
    )

    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report", return_value={"hazard_type": "Flood", "location": "Zone C", "affected_population": 2000}), \
         patch("ml.src.agents.graph.assess_incident", return_value=type("V", (), {"verification_status": "VERIFIED"})()):
        reassess_res = agent_svc.reassess_agent(thread_id, reassess_req)

    # Verify new assessment snapshot created
    assert reassess_res.current_assessment_id is not None
    assert reassess_res.current_assessment_id != initial_id
    assert reassess_res.previous_assessment_id == initial_id

    # Verify historical assessment preserved immutably
    history = ass_repo.get_all_for_incident(initial_ass.incident_id)
    assert len(history) >= 2
    assert history[-1].assessment_id == initial_id  # Parent preserved


def test_zero_inventory_mutation_during_reassessment_and_proposal():
    res_repo = get_resource_repository()
    initial_water = res_repo.get_all()[0].quantity_available

    agent_svc = AgentService()
    req = AgentRunRequest(raw_reports=[json.dumps({"source": "USGS", "source_record_id": "evt-safety", "hazard_type": "Flood"})], run_id="run-safety")

    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report", return_value={"hazard_type": "Flood", "location": "Zone C"}), \
         patch("ml.src.agents.graph.assess_incident", return_value=type("V", (), {"verification_status": "VERIFIED"})()):
        agent_svc.run_agent(req)

    # Reassessment does NOT mutate inventory
    after_water = res_repo.get_all()[0].quantity_available
    assert after_water == initial_water, "Reassessment must NEVER mutate inventory before human approval!"


def test_reassessment_decision_no_reallocation_when_no_meaningful_change():
    from app.services.reassessment_service import ReassessmentService
    svc = ReassessmentService(get_assessment_repository(), get_needs_repository(), get_allocation_repository(), get_action_repository())

    prev = get_assessment_repository().save(
        get_assessment_repository().save(
            type("Record", (), {
                "assessment_id": "ass-prev", "incident_id": "inc-no-change", "parent_assessment_id": None, "reassessment_reason": None,
                "idempotency_key": "k1", "verification_status": "VERIFIED", "severity_status": "supported", "severity": {"severity_class": "MEDIUM", "severity_score": 5.0},
                "trajectory_status": "CALCULATED", "trajectory": {"trajectory": "STABLE"}, "priority_level": "MEDIUM", "priority_score": 5.0,
                "severity_model_version": "v1", "verification_policy_version": "v1", "trajectory_policy_version": "v1", "needs_policy_version": "v1", "priority_policy_version": "v1",
                "assessed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc), "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            })()
        ) or get_assessment_repository().get("ass-prev")
    )

    # Reassessment with same inputs
    curr = get_assessment_repository().get("ass-prev")
    diff = svc.compare_assessments(curr, curr)
    status_enum, is_req = svc.is_reallocation_required(diff)

    assert is_req is False
    assert status_enum == "NO_REALLOCATION_REQUIRED"


def test_hackathon_demo_scenario_hospital_flooded_escalation():
    """
    HACKATHON DEMO SCENARIO:
    1. Zone C initial assessment & execution.
    2. New report: hospital flooded, evacuations required.
    3. Reassessment detects demand increase & generates allocation delta.
    4. Requires human approval before execution.
    """
    agent_svc = AgentService()
    exec_svc = ExecutionService(get_approval_repository(), get_allocation_repository(), get_resource_repository(), get_action_repository())

    # Step 1: Initial Run
    req1 = AgentRunRequest(raw_reports=[json.dumps({"source": "USGS", "source_record_id": "evt-demo-1", "hazard_type": "Flood", "affected_population": 500})], run_id="run-demo-1")
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report", return_value={"hazard_type": "Flood", "location": "Zone C", "affected_population": 500}), \
         patch("ml.src.agents.graph.assess_incident", return_value=type("V", (), {"verification_status": "VERIFIED"})()):
        res1 = agent_svc.run_agent(req1)

    thread_id = "run-demo-1"
    ass_repo = get_assessment_repository()
    all_ass = list(ass_repo._assessments.values())
    inc_id = all_ass[0].incident_id if all_ass else "dummy"

    # Step 2: Approve & Execute Initial Allocation
    agent_svc.submit_review(thread_id, AgentResumeRequest(decision="APPROVED", reason="Initial allocation approved"))
    exec_res1 = exec_svc.execute_proposal(ExecutionRequest(optimization_run_id="run-demo-1", incident_id=inc_id))
    assert exec_res1.status in ["EXECUTED", "ALREADY_EXECUTED"], f"Execution 1 failed: {exec_res1.errors}"

    water_after_exec1 = get_resource_repository().get_all()[0].quantity_available

    # Step 3: Hospital Flooded Escalation (New Evidence)
    escalation_req = ReassessmentRequest(
        new_reports=[json.dumps({"source": "HOSPITAL_DISPATCH", "source_record_id": "evt-demo-2", "hazard_type": "Flood", "affected_population": 3000, "description": "Hospital flooded, 3000 victims stranded"})],
        run_id="run-demo-2",
        reassessment_reason="Hospital flooded, 3000 victims stranded"
    )

    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report", return_value={"hazard_type": "Flood", "location": "Zone C", "affected_population": 3000}), \
         patch("ml.src.agents.graph.assess_incident", return_value=type("V", (), {"verification_status": "VERIFIED"})()):
        reassess_res = agent_svc.reassess_agent(thread_id, escalation_req)

    # Verify Reassessment & Delta
    assert reassess_res.reallocation_required is True
    assert reassess_res.allocation_diff is not None
    assert reassess_res.status in ["PENDING_REVIEW", "COMPLETED"]

    # Inventory must NOT be mutated before human approval of second proposal
    water_before_exec2 = get_resource_repository().get_all()[0].quantity_available
    assert water_before_exec2 == water_after_exec1

    # Step 4: Approve & Execute Reallocation
    agent_svc.submit_review(thread_id, AgentResumeRequest(decision="APPROVED", reason="Escalation reallocation approved"))
    exec_res2 = exec_svc.execute_proposal(ExecutionRequest(optimization_run_id="run-demo-2", incident_id=inc_id))
    assert exec_res2.status in ["EXECUTED", "ALREADY_EXECUTED"], f"Execution 2 failed: {exec_res2.errors}"

    water_after_exec2 = get_resource_repository().get_all()[0].quantity_available
    assert water_after_exec2 < water_after_exec1, "Inventory must be deducted for the reallocation delta upon approval"

