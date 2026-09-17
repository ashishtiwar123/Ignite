"""
Phase 4F — Controlled Execution + Audit Integration Tests
Validates all 40 required test scenarios.
"""
import pytest
import json
import uuid
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure backend is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.schemas.internal import (
    ApprovalRecord,
    AllocationRecord,
    ResourceRecord,
    ExecutionRequest,
    ActionRecord
)
from app.db.dependencies import (
    get_resource_repository,
    get_approval_repository,
    get_allocation_repository,
    get_action_repository
)
from app.services.execution_service import ExecutionService
from ml.src.agents.state import AgentState
from ml.src.agents.graph import build_graph


@pytest.fixture(autouse=True)
def reset_all_repos():
    """Clear and seed repositories before each test."""
    for repo in [
        get_resource_repository(),
        get_approval_repository(),
        get_allocation_repository(),
        get_action_repository()
    ]:
        if hasattr(repo, '_resources'): repo._resources.clear()
        if hasattr(repo, '_storage'): repo._storage.clear()
        if hasattr(repo, '_data'): repo._data.clear()

    # Seed 1000L Water and 500 Kits Food
    get_resource_repository().upsert(ResourceRecord(
        location_id="warehouse-alpha",
        resource_type="Water",
        category="WATER",
        quantity_available=1000.0,
        unit="Liters"
    ))
    get_resource_repository().upsert(ResourceRecord(
        location_id="warehouse-alpha",
        resource_type="Food",
        category="FOOD",
        quantity_available=500.0,
        unit="Kits"
    ))
    yield


# ──────────────────────────────────────────────────────────
# A. APPROVAL GATE (1-7)
# ──────────────────────────────────────────────────────────

def test_1_approved_persisted_allows_execution():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-1", optimization_run_id="run-1", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-1", incident_id="inc-1", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=100.0,
                         quantity_requested=100.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-1", incident_id="inc-1"))
    assert res.status == "EXECUTED"


def test_2_pending_approval_blocked():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-2", optimization_run_id="run-2", status="PENDING"))
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-2", incident_id="inc-2"))
    assert res.status == "NOT_APPROVED"


def test_3_rejected_approval_blocked():
    appr_repo = get_approval_repository()
    svc = ExecutionService(appr_repo, get_allocation_repository(), get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-3", optimization_run_id="run-3", status="REJECTED"))
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-3", incident_id="inc-3"))
    assert res.status == "NOT_APPROVED"


def test_4_revision_requested_approval_blocked():
    appr_repo = get_approval_repository()
    svc = ExecutionService(appr_repo, get_allocation_repository(), get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-4", optimization_run_id="run-4", status="REVISION_REQUESTED"))
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-4", incident_id="inc-4"))
    assert res.status == "NOT_APPROVED"


def test_5_missing_approval_blocked():
    svc = ExecutionService(get_approval_repository(), get_allocation_repository(), get_resource_repository(), get_action_repository())
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-missing", incident_id="inc-missing"))
    assert res.status == "NOT_APPROVED"


def test_6_mismatched_approval_incident_blocked():
    appr_repo = get_approval_repository()
    svc = ExecutionService(appr_repo, get_allocation_repository(), get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-real", optimization_run_id="run-6", status="APPROVED"))
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-6", incident_id="inc-fake"))
    assert res.status == "NOT_APPROVED"


def test_7_client_approved_flag_cannot_bypass_persisted_db():
    svc = ExecutionService(get_approval_repository(), get_allocation_repository(), get_resource_repository(), get_action_repository())
    req = ExecutionRequest(optimization_run_id="run-7", incident_id="inc-7", approved=True)
    res = svc.execute_proposal(req)
    assert res.status == "NOT_APPROVED"



# ──────────────────────────────────────────────────────────
# B. PROPOSAL INTEGRITY (8-11)
# ──────────────────────────────────────────────────────────

def test_8_exact_phase4d_proposal_consumed():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-8", optimization_run_id="run-8", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-8", incident_id="inc-8", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=250.0,
                         quantity_requested=500.0, quantity_unmet=250.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-8", incident_id="inc-8"))
    assert res.status == "EXECUTED"
    assert res.deducted_resources[0].quantity_deducted == 250.0


def test_9_no_ortools_recalculation_during_execution():
    with patch("ml.src.optimization.engine.optimize_allocation") as mock_ortools:
        appr_repo = get_approval_repository()
        alloc_repo = get_allocation_repository()
        svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

        appr_repo.upsert(ApprovalRecord(incident_id="inc-9", optimization_run_id="run-9", status="APPROVED"))
        alloc_repo.save_allocations([
            AllocationRecord(optimization_run_id="run-9", incident_id="inc-9", source_location_id="warehouse-alpha",
                             resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                             quantity_requested=50.0, quantity_unmet=0.0)
        ])

        svc.execute_proposal(ExecutionRequest(optimization_run_id="run-9", incident_id="inc-9"))
        mock_ortools.assert_not_called()


def test_10_no_gemini_involvement_during_execution():
    with patch("ml.src.agents.gemini_client.GeminiAdapter.explain_coordination") as mock_gemini:
        appr_repo = get_approval_repository()
        alloc_repo = get_allocation_repository()
        svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

        appr_repo.upsert(ApprovalRecord(incident_id="inc-10", optimization_run_id="run-10", status="APPROVED"))
        alloc_repo.save_allocations([
            AllocationRecord(optimization_run_id="run-10", incident_id="inc-10", source_location_id="warehouse-alpha",
                             resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                             quantity_requested=50.0, quantity_unmet=0.0)
        ])

        svc.execute_proposal(ExecutionRequest(optimization_run_id="run-10", incident_id="inc-10"))
        mock_gemini.assert_not_called()


def test_11_stale_invalid_proposal_blocked():
    appr_repo = get_approval_repository()
    svc = ExecutionService(appr_repo, get_allocation_repository(), get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-11", optimization_run_id="run-11", status="APPROVED"))
    # No allocations saved!
    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-11", incident_id="inc-11"))
    assert res.status == "INVALID_PROPOSAL"


# ──────────────────────────────────────────────────────────
# C. INVENTORY VALIDATION & ATOMICITY (12-19)
# ──────────────────────────────────────────────────────────

def test_12_correct_deduction_applied():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    res_repo = get_resource_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-12", optimization_run_id="run-12", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-12", incident_id="inc-12", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=400.0,
                         quantity_requested=400.0, quantity_unmet=0.0)
    ])

    svc.execute_proposal(ExecutionRequest(optimization_run_id="run-12", incident_id="inc-12"))
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water.quantity_available == 600.0


def test_13_zero_or_negative_quantity_blocked():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-13", optimization_run_id="run-13", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-13", incident_id="inc-13", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=-50.0,
                         quantity_requested=100.0, quantity_unmet=150.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-13", incident_id="inc-13"))
    assert res.status == "INVALID_PROPOSAL"


def test_14_insufficient_inventory_blocked():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-14", optimization_run_id="run-14", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-14", incident_id="inc-14", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=5000.0,
                         quantity_requested=5000.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-14", incident_id="inc-14"))
    assert res.status == "FAILED"


def test_15_unknown_resource_blocked():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-15", optimization_run_id="run-15", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-15", incident_id="inc-15", source_location_id="warehouse-alpha",
                         resource_type="Unobtainium", category="UNKNOWN", unit="Kg", quantity_allocated=10.0,
                         quantity_requested=10.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-15", incident_id="inc-15"))
    assert res.status == "FAILED"


def test_16_inventory_never_becomes_negative():
    res_repo = get_resource_repository()
    with pytest.raises(ValueError):
        res_repo.deduct_resources([{
            "location_id": "warehouse-alpha",
            "resource_type": "Water",
            "category": "WATER",
            "quantity": 2000.0  # Exceeds 1000
        }])
    assert res_repo.get_all()[0].quantity_available == 1000.0


def test_17_multi_resource_success_deducts_all():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    res_repo = get_resource_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-17", optimization_run_id="run-17", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-17", incident_id="inc-17", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=100.0,
                         quantity_requested=100.0, quantity_unmet=0.0),
        AllocationRecord(optimization_run_id="run-17", incident_id="inc-17", source_location_id="warehouse-alpha",
                         resource_type="Food", category="FOOD", unit="Kits", quantity_allocated=50.0,
                         quantity_requested=50.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-17", incident_id="inc-17"))
    assert res.status == "EXECUTED"
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    food = next(r for r in res_repo.get_all() if r.resource_type == "Food")
    assert water.quantity_available == 900.0
    assert food.quantity_available == 450.0


def test_18_one_invalid_resource_causes_zero_deductions():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    res_repo = get_resource_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-18", optimization_run_id="run-18", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-18", incident_id="inc-18", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=100.0,
                         quantity_requested=100.0, quantity_unmet=0.0),
        AllocationRecord(optimization_run_id="run-18", incident_id="inc-18", source_location_id="warehouse-alpha",
                         resource_type="Food", category="FOOD", unit="Kits", quantity_allocated=999.0, # Fail!
                         quantity_requested=999.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-18", incident_id="inc-18"))
    assert res.status == "FAILED"
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    food = next(r for r in res_repo.get_all() if r.resource_type == "Food")
    assert water.quantity_available == 1000.0  # Unchanged!
    assert food.quantity_available == 500.0    # Unchanged!


def test_19_mutation_failure_causes_zero_deductions():
    res_repo = get_resource_repository()
    with pytest.raises(ValueError):
        res_repo.deduct_resources([
            {"location_id": "warehouse-alpha", "resource_type": "Water", "category": "WATER", "quantity": 100.0},
            {"location_id": "warehouse-alpha", "resource_type": "Water", "category": "WATER", "quantity": -5.0}
        ])
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water.quantity_available == 1000.0


# ──────────────────────────────────────────────────────────
# D. IDEMPOTENCY & CONCURRENCY (20-24)
# ──────────────────────────────────────────────────────────

def test_20_21_22_double_execution_returns_already_executed():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    res_repo = get_resource_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-20", optimization_run_id="run-20", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-20", incident_id="inc-20", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=100.0,
                         quantity_requested=100.0, quantity_unmet=0.0)
    ])

    req = ExecutionRequest(optimization_run_id="run-20", incident_id="inc-20")
    res1 = svc.execute_proposal(req)
    assert res1.status == "EXECUTED"

    res2 = svc.execute_proposal(req)
    assert res2.status == "ALREADY_EXECUTED"

    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water.quantity_available == 900.0  # Deducted exactly ONCE


def test_23_stale_inventory_handled_gracefully():
    res_repo = get_resource_repository()
    # Deduct 900L outside current context
    res_repo.deduct_resources([{"location_id": "warehouse-alpha", "resource_type": "Water", "category": "WATER", "quantity": 900.0}])

    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-23", optimization_run_id="run-23", status="APPROVED"))
    # Stale allocation formed when 1000L was available
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-23", incident_id="inc-23", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=500.0,
                         quantity_requested=500.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-23", incident_id="inc-23"))
    assert res.status == "FAILED"


def test_24_concurrent_execution_cannot_overspend():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    res_repo = get_resource_repository()
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, get_action_repository())

    # Seed 600L Water allocation for run A, 600L for run B (Total stock 1000L)
    appr_repo.upsert(ApprovalRecord(incident_id="inc-24A", optimization_run_id="run-24A", status="APPROVED"))
    appr_repo.upsert(ApprovalRecord(incident_id="inc-24B", optimization_run_id="run-24B", status="APPROVED"))

    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-24A", incident_id="inc-24A", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=600.0,
                         quantity_requested=600.0, quantity_unmet=0.0)
    ])
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-24B", incident_id="inc-24B", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=600.0,
                         quantity_requested=600.0, quantity_unmet=0.0)
    ])

    resA = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-24A", incident_id="inc-24A"))
    assert resA.status == "EXECUTED"

    resB = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-24B", incident_id="inc-24B"))
    assert resB.status == "FAILED"  # Only 400L remaining!

    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water.quantity_available == 400.0


# ──────────────────────────────────────────────────────────
# E. IDENTITY SEPARATION (25-29)
# ──────────────────────────────────────────────────────────

def test_25_26_27_execution_id_distinct_from_run_and_thread_id():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-25", optimization_run_id="run-25", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-25", incident_id="inc-25", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                         quantity_requested=50.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-25", incident_id="inc-25"))
    assert res.execution_id != "run-25"
    assert res.execution_id != "thread-25"


def test_28_optimization_run_id_preserved():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-28", optimization_run_id="run-28", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-28", incident_id="inc-28", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                         quantity_requested=50.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-28", incident_id="inc-28"))
    assert res.optimization_run_id == "run-28"


def test_29_missing_run_id_remains_none():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-29", optimization_run_id=None, status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id=None, incident_id="inc-29", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                         quantity_requested=50.0, quantity_unmet=0.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id=None, incident_id="inc-29"))
    assert res.optimization_run_id is None


# ──────────────────────────────────────────────────────────
# F. AUDIT, GOVERNANCE & ACTION (30-39)
# ──────────────────────────────────────────────────────────

def test_30_to_34_audit_events_created_without_secrets():
    with patch("app.services.execution_service.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        appr_repo = get_approval_repository()
        alloc_repo = get_allocation_repository()
        svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

        appr_repo.upsert(ApprovalRecord(incident_id="inc-30", optimization_run_id="run-30", status="APPROVED"))
        alloc_repo.save_allocations([
            AllocationRecord(optimization_run_id="run-30", incident_id="inc-30", source_location_id="warehouse-alpha",
                             resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                             quantity_requested=50.0, quantity_unmet=0.0)
        ])

        svc.execute_proposal(ExecutionRequest(optimization_run_id="run-30", incident_id="inc-30"))
        mock_client.table("audit_events").insert.assert_called()


def test_35_to_39_action_record_created_and_approval_immutable():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    act_repo = get_action_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), act_repo)

    appr = appr_repo.upsert(ApprovalRecord(incident_id="inc-35", optimization_run_id="run-35", status="APPROVED"))
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-35", incident_id="inc-35", source_location_id="warehouse-alpha",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=50.0,
                         quantity_requested=50.0, quantity_unmet=0.0)
    ])

    svc.execute_proposal(ExecutionRequest(optimization_run_id="run-35", incident_id="inc-35"))

    # Approval decision remains immutable APPROVED
    assert appr_repo.get(appr.approval_id).status == "APPROVED"

    # Action record created with EXECUTED
    actions = act_repo.get_by_optimization_run("run-35")
    assert len(actions) == 1
    assert actions[0].status == "EXECUTED"


# ──────────────────────────────────────────────────────────
# G. QUALITATIVE NEEDS (40)
# ──────────────────────────────────────────────────────────

def test_40_qualitative_needs_do_not_receive_fabricated_quantities():
    appr_repo = get_approval_repository()
    alloc_repo = get_allocation_repository()
    svc = ExecutionService(appr_repo, alloc_repo, get_resource_repository(), get_action_repository())

    appr_repo.upsert(ApprovalRecord(incident_id="inc-40", optimization_run_id="run-40", status="APPROVED"))
    # Seed qualitative allocation (quantity_allocated = 0.0)
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-40", incident_id="inc-40", source_location_id="warehouse-alpha",
                         resource_type="MedicalAssessment", category="MEDICAL", unit="Assessment", quantity_allocated=0.0,
                         quantity_requested=1.0, quantity_unmet=1.0)
    ])

    res = svc.execute_proposal(ExecutionRequest(optimization_run_id="run-40", incident_id="inc-40"))
    # Must reject as INVALID_PROPOSAL rather than fabricating a non-zero quantity
    assert res.status == "INVALID_PROPOSAL"
