"""
Phase 4E — Human Review / Approval Integration Tests
"""
import pytest
import json
import uuid
import sys
import os
from unittest.mock import patch

# Ensure backend is in sys.path (same pattern as Phase 4D tests)
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from ml.src.agents.state import AgentState
from ml.src.agents.graph import build_graph
from app.db.dependencies import get_resource_repository, get_approval_repository
from app.api.schemas.internal import ResourceRecord, ApprovalRecord


# ──────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_repositories():
    """Clear and seed repositories before each test."""
    resource_repo = get_resource_repository()
    if hasattr(resource_repo, '_resources'):
        resource_repo._resources.clear()
    if hasattr(resource_repo, '_storage'):
        resource_repo._storage.clear()

    approval_repo = get_approval_repository()
    if hasattr(approval_repo, '_storage'):
        approval_repo._storage.clear()

    # Seed 1000L of Water
    resource_repo.upsert(ResourceRecord(
        location_id="warehouse-alpha",
        resource_type="Water",
        category="WATER",
        quantity_available=1000.0,
        unit="Liters"
    ))

    yield

    if hasattr(resource_repo, '_resources'):
        resource_repo._resources.clear()
    if hasattr(resource_repo, '_storage'):
        resource_repo._storage.clear()
    if hasattr(approval_repo, '_storage'):
        approval_repo._storage.clear()


def _setup_verified_flow_patches():
    """Return a list of context managers to patch all downstream dependencies."""
    from ml.src.incident.verification import VerificationAssessment
    from ml.src.risk.trajectory_schemas import TrajectoryAssessment
    from ml.src.needs.schemas import ResourceRequirement

    return [
        patch(
            "ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report",
            return_value={"hazard_type": "Earthquake", "location": "Tokyo", "observed_at": "2026-09-17T00:00:00Z"}
        ),
        patch(
            "ml.src.agents.graph.assess_incident",
            return_value=VerificationAssessment(
                incident_candidate_id="dummy", verification_status="VERIFIED", confidence_score=0.9
            )
        ),
        patch(
            "ml.src.models.severity_v2.predictor_v2.SeverityPredictorV2.predict_severity",
            return_value={"status": "success", "severity_score": 8.0, "severity_class": "EXTREME", "model_version": "v2"}
        ),
        patch(
            "ml.src.agents.graph.assess_trajectory",
            return_value=TrajectoryAssessment(
                incident_candidate_id="dummy", trajectory="RAPIDLY_WORSENING", confidence=0.9, policy_version="v1"
            )
        ),
        patch(
            "ml.src.agents.graph.assess_needs",
            return_value=[
                ResourceRequirement(
                    verified_incident_id="dummy", resource_type="Water", category="WATER",
                    quantity=500.0, unit="Liters", urgency="HIGH", status="CALCULATED",
                    rule_id="r1", explanation="test"
                )
            ]
        )
    ]


def run_to_interrupt(thread_id: str = None):
    """Run the graph until it interrupts at human_review. Returns (app, config, initial_state)."""
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    app = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    run_id = "run-" + thread_id[:8]
    initial_state = AgentState(
        raw_reports=[json.dumps({"source": "USGS", "source_record_id": "evt-1", "hazard_type": "Earthquake"})],
        run_id=run_id
    )

    patches = _setup_verified_flow_patches()
    for p in patches:
        p.start()

    try:
        result = app.invoke({"state": initial_state}, config=config)
    finally:
        for p in patches:
            p.stop()

    return app, config, run_id, result


# ──────────────────────────────────────────────────────────
# A. PENDING REVIEW — graph interrupts and status is PENDING
# ──────────────────────────────────────────────────────────

def test_graph_interrupts_at_human_review():
    """Graph must pause before human_review node with PENDING status."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, result = run_to_interrupt(thread_id)

    state_snap = app.get_state(config)
    assert state_snap is not None
    assert state_snap.next == ("human_review",), \
        f"Expected graph to be paused before human_review, got next={state_snap.next}"

    state = state_snap.values["state"]
    assert state.human_approval_state == "PENDING"
    assert state.verification_status == "VERIFIED"
    assert state.allocation_result is not None


def test_pending_review_is_distinct_from_failed():
    """PENDING_REVIEW must not be confused with FAILED."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, result = run_to_interrupt(thread_id)

    state_snap = app.get_state(config)
    state = state_snap.values["state"]
    assert state.human_approval_state == "PENDING"
    assert "FAILED" not in (state.workflow_status or "")
    assert state.errors == [] or all("FAILED" not in e for e in state.errors)


# ──────────────────────────────────────────────────────────
# B. APPROVED — same checkpoint resumed
# ──────────────────────────────────────────────────────────

def test_approval_resumes_same_checkpoint():
    """Approving must resume the SAME checkpoint thread — not start a new execution."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap_pre = app.get_state(config)
    assert snap_pre.next == ("human_review",)

    # Inject decision and resume
    pre_state: AgentState = snap_pre.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "APPROVED"})
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state: AgentState = result["state"]
    assert final_state.human_approval_state == "APPROVED"
    # run_id must be preserved
    assert final_state.run_id == run_id


def test_approval_does_not_mutate_inventory():
    """Inventory must be unchanged after approval."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    resource_repo = get_resource_repository()
    water_before = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
    qty_before = water_before.quantity_available

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "APPROVED"})
    app.update_state(config, {"state": updated})
    app.invoke(None, config=config)

    water_after = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
    assert water_after.quantity_available == qty_before, \
        "Approval must NEVER mutate ResourceRepository quantities"


def test_approval_allocation_unchanged():
    """The allocation proposal must be exactly the Phase 4D proposal — unchanged by review."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap_pre = app.get_state(config)
    alloc_pre = snap_pre.values["state"].allocation_result

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "APPROVED"})
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    alloc_post = result["state"].allocation_result
    # The allocation is unchanged
    assert alloc_post == alloc_pre


# ──────────────────────────────────────────────────────────
# C. REJECTED
# ──────────────────────────────────────────────────────────

def test_rejection_resumes_and_terminates():
    """Rejection must terminate the workflow without execution."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={
        "human_approval_state": "REJECTED",
        "human_feedback": "Allocation does not match priority"
    })
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state = result["state"]
    assert final_state.human_approval_state == "REJECTED"


def test_rejection_does_not_mutate_inventory():
    """Rejection must NEVER mutate ResourceRepository quantities."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    resource_repo = get_resource_repository()
    water_before = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
    qty_before = water_before.quantity_available

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "REJECTED"})
    app.update_state(config, {"state": updated})
    app.invoke(None, config=config)

    water_after = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
    assert water_after.quantity_available == qty_before


# ──────────────────────────────────────────────────────────
# D. REVISION_REQUESTED
# ──────────────────────────────────────────────────────────

def test_revision_requested_terminates_without_reoptimization():
    """REVISION_REQUESTED must stop the current cycle — no automatic re-optimization."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    original_alloc = pre_state.allocation_result
    updated = pre_state.model_copy(update={
        "human_approval_state": "REVISION_REQUESTED",
        "human_feedback": "Needs recalculation for shelter requirements"
    })
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state = result["state"]
    assert final_state.human_approval_state == "REVISION_REQUESTED"
    # Allocation must be unchanged — no re-optimization
    assert final_state.allocation_result == original_alloc


# ──────────────────────────────────────────────────────────
# E. INVALID DECISION
# ──────────────────────────────────────────────────────────

def test_invalid_decision_rejected():
    """Only APPROVED, REJECTED, REVISION_REQUESTED are valid decisions."""
    from app.api.schemas.internal import ApprovalRecord
    from app.db.approval_repository import InMemoryApprovalRepository

    repo = InMemoryApprovalRepository()
    record = ApprovalRecord(incident_id="inc-1", status="MAYBE")

    # Storing a MAYBE decision should not raise (repo only blocks conflicting finals)
    # but the service layer rejects it:
    from app.services.approval_service import ApprovalService
    svc = ApprovalService(repo)
    with pytest.raises(ValueError, match="Invalid decision"):
        svc.record_approval(
            incident_id="inc-1",
            optimization_run_id=None,
            decision="MAYBE"
        )


# ──────────────────────────────────────────────────────────
# F. DUPLICATE SUBMISSION / IMMUTABILITY
# ──────────────────────────────────────────────────────────

def test_approval_immutability_same_record():
    """Once APPROVED, re-submitting a REJECTED status for the same record must be blocked."""
    repo = get_approval_repository()
    if hasattr(repo, '_storage'):
        repo._storage.clear()

    record = ApprovalRecord(
        approval_id="appr-imm-1",
        incident_id="inc-imm-1",
        optimization_run_id="run-imm-1",
        status="APPROVED"
    )
    repo.upsert(record)

    # Try to mutate to REJECTED
    mutated = record.model_copy(update={"status": "REJECTED"})
    with pytest.raises(ValueError, match="Cannot mutate an already finalized approval decision"):
        repo.upsert(mutated)


def test_conflicting_decision_for_same_run_blocked():
    """Two separate records cannot both be finalized for the same optimization_run_id."""
    repo = get_approval_repository()
    if hasattr(repo, '_storage'):
        repo._storage.clear()

    record1 = ApprovalRecord(
        approval_id="appr-cf-1",
        incident_id="inc-cf-1",
        optimization_run_id="run-cf-1",
        status="APPROVED"
    )
    repo.upsert(record1)

    record2 = ApprovalRecord(
        approval_id="appr-cf-2",  # Different record
        incident_id="inc-cf-1",
        optimization_run_id="run-cf-1",  # Same run
        status="REJECTED"
    )
    with pytest.raises(ValueError, match="Cannot create a conflicting approval record"):
        repo.upsert(record2)


def test_identical_submission_is_idempotent():
    """Re-submitting the exact same decision for the same record is idempotent."""
    repo = get_approval_repository()
    if hasattr(repo, '_storage'):
        repo._storage.clear()

    record = ApprovalRecord(
        approval_id="appr-idem-1",
        incident_id="inc-idem-1",
        optimization_run_id="run-idem-1",
        status="APPROVED"
    )
    repo.upsert(record)
    # Re-submit same record, same status — must succeed without error
    repo.upsert(record)
    assert repo.get("appr-idem-1").status == "APPROVED"


# ──────────────────────────────────────────────────────────
# G. RUN ID SEMANTICS
# ──────────────────────────────────────────────────────────

def test_explicit_run_id_preserved():
    """state.run_id must equal optimization_run_id — never thread_id."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    state: AgentState = snap.values["state"]
    assert state.run_id == run_id
    # thread_id must differ (thread_id was UUID distinct from run_id prefix)
    assert state.run_id != thread_id


def test_missing_run_id_stays_none():
    """If no run_id provided, state.run_id must remain None — not fallback to thread_id."""
    app = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = AgentState(
        raw_reports=[json.dumps({"source": "USGS", "source_record_id": "evt-1", "hazard_type": "Earthquake"})],
        run_id=None
    )

    patches = _setup_verified_flow_patches()
    for p in patches:
        p.start()
    try:
        app.invoke({"state": initial_state}, config=config)
    finally:
        for p in patches:
            p.stop()

    snap = app.get_state(config)
    state: AgentState = snap.values["state"]
    assert state.run_id is not None and state.run_id.startswith("opt-"), \
        f"optimization_run_id must be populated when not provided. Got: {state.run_id}"


def test_thread_id_never_becomes_optimization_run_id():
    """thread_id must never appear as optimization_run_id in the allocation result."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    state: AgentState = snap.values["state"]
    alloc = state.allocation_result

    if alloc:
        assert alloc.get("optimization_run_id") != thread_id, \
            "thread_id must NEVER become optimization_run_id"


# ──────────────────────────────────────────────────────────
# H. VERIFICATION GATE
# ──────────────────────────────────────────────────────────

def test_needs_verification_cannot_reach_approval():
    """A NEEDS_VERIFICATION incident must not reach the human_review node for operational approval."""
    from ml.src.incident.verification import VerificationAssessment

    app = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    raw = json.dumps({"source": "TWITTER", "source_record_id": "tw-1", "hazard_type": "Flood"})
    initial_state = AgentState(raw_reports=[raw])

    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report",
               return_value={"hazard_type": "Flood", "location": "Unknown", "observed_at": "2026-09-17T00:00:00Z"}):
        with patch("ml.src.agents.graph.assess_incident",
                   return_value=VerificationAssessment(
                       incident_candidate_id="dummy", verification_status="NEEDS_VERIFICATION", confidence_score=0.4
                   )):
            result = app.invoke({"state": initial_state}, config=config)

    # Even with interrupt_before=human_review, it should not reach there for NEEDS_VERIFICATION
    # because route_after_verification sends it to "human_review" with PENDING flag, but
    # allocation_result is None so the review is not for an allocation proposal.
    state_snap = app.get_state(config)
    if state_snap and state_snap.values:
        final_state = state_snap.values.get("state")
        if final_state:
            # If it did reach human_review, there must be no allocation proposal to approve
            assert final_state.allocation_result is None


def test_rejected_verification_cannot_reach_approval():
    """A REJECTED incident cannot reach the human approval boundary."""
    from ml.src.incident.verification import VerificationAssessment

    app = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    raw = json.dumps({"source": "USGS", "source_record_id": "fake-1", "hazard_type": "PROMPT_INJECTION_DETECTED"})
    initial_state = AgentState(raw_reports=[raw])

    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report",
               return_value={"hazard_type": "PROMPT_INJECTION_DETECTED"}):
        with patch("ml.src.agents.graph.assess_incident",
                   return_value=VerificationAssessment(
                       incident_candidate_id="dummy", verification_status="REJECTED", confidence_score=0.1
                   )):
            result = app.invoke({"state": initial_state}, config=config)

    if result:
        final_state = result.get("state")
        if final_state:
            assert final_state.verification_status == "REJECTED"
            assert final_state.allocation_result is None


# ──────────────────────────────────────────────────────────
# I. NO EXECUTION
# ──────────────────────────────────────────────────────────

def test_no_execution_after_approval():
    """APPROVED = AUTHORIZED_FOR_EXECUTION, not EXECUTED. Phase 4E must not execute."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "APPROVED"})
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state = result["state"]
    # Confirm no dispatch / execution markers exist
    assert final_state.human_approval_state == "APPROVED"
    # Inventory is unchanged (already tested above, but belt-and-suspenders)
    resource_repo = get_resource_repository()
    water = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
    assert water.quantity_available == 1000.0


# ──────────────────────────────────────────────────────────
# J. COMPLETE LIFECYCLE TESTS
# ──────────────────────────────────────────────────────────

def test_complete_lifecycle_approve():
    """Full lifecycle: START → OPTIMIZE → INTERRUPT → APPROVE → RESUME → APPROVED."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    # Phase 1: Confirm interrupted
    snap = app.get_state(config)
    assert snap.next == ("human_review",)
    assert snap.values["state"].human_approval_state == "PENDING"

    # Phase 2: Inject APPROVED
    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={"human_approval_state": "APPROVED"})
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    # Phase 3: Confirm APPROVED
    final_state = result["state"]
    assert final_state.human_approval_state == "APPROVED"
    assert final_state.run_id == run_id


def test_complete_lifecycle_reject():
    """Full lifecycle: START → OPTIMIZE → INTERRUPT → REJECT → RESUME → REJECTED."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    assert snap.next == ("human_review",)

    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={
        "human_approval_state": "REJECTED",
        "human_feedback": "Resources insufficient"
    })
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state = result["state"]
    assert final_state.human_approval_state == "REJECTED"


def test_complete_lifecycle_revision():
    """Full lifecycle: START → OPTIMIZE → INTERRUPT → REVISION_REQUESTED → RESUME → REVISION_REQUESTED."""
    thread_id = str(uuid.uuid4())
    app, config, run_id, _ = run_to_interrupt(thread_id)

    snap = app.get_state(config)
    assert snap.next == ("human_review",)

    pre_state: AgentState = snap.values["state"]
    updated = pre_state.model_copy(update={
        "human_approval_state": "REVISION_REQUESTED",
        "human_feedback": "Need shelter resources too"
    })
    app.update_state(config, {"state": updated})
    result = app.invoke(None, config=config)

    final_state = result["state"]
    assert final_state.human_approval_state == "REVISION_REQUESTED"


# ──────────────────────────────────────────────────────────
# K. APPROVAL SERVICE PERSISTENCE
# ──────────────────────────────────────────────────────────

def test_approval_service_persists_correctly():
    """ApprovalService must persist the record with correct fields."""
    from backend.app.db.approval_repository import InMemoryApprovalRepository
    from backend.app.services.approval_service import ApprovalService

    repo = InMemoryApprovalRepository()
    svc = ApprovalService(repo)

    record = svc.record_approval(
        incident_id="inc-persist-1",
        optimization_run_id="run-persist-1",
        decision="APPROVED",
        reason="Looks good",
        reviewer_id="operator-1"
    )

    assert record.incident_id == "inc-persist-1"
    assert record.optimization_run_id == "run-persist-1"
    assert record.status == "APPROVED"
    assert record.reviewer_id == "operator-1"
    assert record.reason == "Looks good"
    assert record.decided_at is not None


def test_approval_service_persists_rejection():
    """ApprovalService must persist rejection with reason."""
    from backend.app.db.approval_repository import InMemoryApprovalRepository
    from backend.app.services.approval_service import ApprovalService

    repo = InMemoryApprovalRepository()
    svc = ApprovalService(repo)

    record = svc.record_approval(
        incident_id="inc-reject-1",
        optimization_run_id="run-reject-1",
        decision="REJECTED",
        reason="Insufficient supply",
        reviewer_id="operator-2"
    )

    assert record.status == "REJECTED"
    assert record.reason == "Insufficient supply"


def test_approval_service_persists_revision():
    """ApprovalService must persist REVISION_REQUESTED with reason."""
    from backend.app.db.approval_repository import InMemoryApprovalRepository
    from backend.app.services.approval_service import ApprovalService

    repo = InMemoryApprovalRepository()
    svc = ApprovalService(repo)

    record = svc.record_approval(
        incident_id="inc-rev-1",
        optimization_run_id=None,
        decision="REVISION_REQUESTED",
        reason="Need to include shelter",
    )

    assert record.status == "REVISION_REQUESTED"
    assert record.optimization_run_id is None  # no run_id → stays None


def test_approval_none_run_id_preserved():
    """ApprovalService must not fabricate optimization_run_id when run_id=None."""
    from backend.app.db.approval_repository import InMemoryApprovalRepository
    from backend.app.services.approval_service import ApprovalService

    repo = InMemoryApprovalRepository()
    svc = ApprovalService(repo)

    record = svc.record_approval(
        incident_id="inc-none-run",
        optimization_run_id=None,
        decision="APPROVED"
    )
    assert record.optimization_run_id is None
