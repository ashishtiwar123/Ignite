import pytest
import uuid
import sys
import os
from datetime import datetime, timezone

# Ensure backend is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.schemas.internal import (

    ExecutionRequest,
    ApprovalRecord,
    AllocationRecord,
    ResourceRecord,
    ActionRecord
)
from app.db.approval_repository import InMemoryApprovalRepository
from app.db.allocation_repository import InMemoryAllocationRepository
from app.db.resource_repository import InMemoryResourceRepository
from app.db.action_repository import InMemoryActionRepository
from app.services.execution_service import ExecutionService


@pytest.fixture
def repos():
    appr_repo = InMemoryApprovalRepository()
    alloc_repo = InMemoryAllocationRepository()
    res_repo = InMemoryResourceRepository()
    act_repo = InMemoryActionRepository()

    # Seed resources
    res_repo.upsert(ResourceRecord(
        location_id="wh-1",
        resource_type="Water",
        category="WATER",
        quantity_available=1000.0,
        unit="Liters"
    ))
    res_repo.upsert(ResourceRecord(
        location_id="wh-1",
        resource_type="Food",
        category="FOOD",
        quantity_available=500.0,
        unit="Kits"
    ))

    return appr_repo, alloc_repo, res_repo, act_repo


def test_execution_requires_persisted_approved_status(repos):
    appr_repo, alloc_repo, res_repo, act_repo = repos
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, act_repo)

    # Scenario: Missing approval
    req = ExecutionRequest(optimization_run_id="run-100", incident_id="inc-1")
    res = svc.execute_proposal(req)
    assert res.status == "NOT_APPROVED"
    assert "missing or not APPROVED" in res.errors[0]
    assert res_repo.get_by_location("wh-1")[0].quantity_available == 1000.0

    # Scenario: Approval exists but is REJECTED
    appr_repo.upsert(ApprovalRecord(
        incident_id="inc-1",
        optimization_run_id="run-100",
        status="REJECTED"
    ))
    res2 = svc.execute_proposal(req)
    assert res2.status == "NOT_APPROVED"
    assert res_repo.get_by_location("wh-1")[0].quantity_available == 1000.0


def test_successful_execution_deducts_inventory_and_logs_action(repos):
    appr_repo, alloc_repo, res_repo, act_repo = repos
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, act_repo)

    # Seed approval
    appr = appr_repo.upsert(ApprovalRecord(
        incident_id="inc-2",
        optimization_run_id="run-200",
        status="APPROVED"
    ))

    # Seed Phase 4D allocation
    alloc_repo.save_allocations([
        AllocationRecord(
            optimization_run_id="run-200",
            incident_id="inc-2",
            source_location_id="wh-1",
            resource_type="Water",
            category="WATER",
            unit="Liters",
            quantity_allocated=300.0,
            quantity_requested=500.0,
            quantity_unmet=200.0
        )
    ])

    req = ExecutionRequest(optimization_run_id="run-200", incident_id="inc-2")
    res = svc.execute_proposal(req)

    assert res.status == "EXECUTED"
    assert len(res.deducted_resources) == 1
    assert res.deducted_resources[0].quantity_deducted == 300.0
    assert res.deducted_resources[0].new_quantity == 700.0

    # Check inventory deducted
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water.quantity_available == 700.0

    # Check action record logged
    actions = act_repo.get_by_optimization_run("run-200")
    assert len(actions) == 1
    assert actions[0].status == "EXECUTED"
    assert actions[0].approval_id == appr.approval_id


def test_double_execution_is_prevented_by_idempotency(repos):
    appr_repo, alloc_repo, res_repo, act_repo = repos
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, act_repo)

    appr_repo.upsert(ApprovalRecord(
        incident_id="inc-3",
        optimization_run_id="run-300",
        status="APPROVED"
    ))

    alloc_repo.save_allocations([
        AllocationRecord(
            optimization_run_id="run-300",
            incident_id="inc-3",
            source_location_id="wh-1",
            resource_type="Water",
            category="WATER",
            unit="Liters",
            quantity_allocated=100.0,
            quantity_requested=100.0,
            quantity_unmet=0.0
        )
    ])

    req = ExecutionRequest(optimization_run_id="run-300", incident_id="inc-3")

    # First execution
    res1 = svc.execute_proposal(req)
    assert res1.status == "EXECUTED"
    water1 = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water1.quantity_available == 900.0

    # Second execution attempt
    res2 = svc.execute_proposal(req)
    assert res2.status == "ALREADY_EXECUTED"

    # Inventory must NOT be deducted a second time!
    water2 = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    assert water2.quantity_available == 900.0


def test_atomic_rollback_on_insufficient_stock(repos):
    appr_repo, alloc_repo, res_repo, act_repo = repos
    svc = ExecutionService(appr_repo, alloc_repo, res_repo, act_repo)

    appr_repo.upsert(ApprovalRecord(
        incident_id="inc-4",
        optimization_run_id="run-400",
        status="APPROVED"
    ))

    # Allocates 200L Water (valid) AND 9999 Kits Food (exceeds 500 stock!)
    alloc_repo.save_allocations([
        AllocationRecord(
            optimization_run_id="run-400",
            incident_id="inc-4",
            source_location_id="wh-1",
            resource_type="Water",
            category="WATER",
            unit="Liters",
            quantity_allocated=200.0,
            quantity_requested=200.0,
            quantity_unmet=0.0
        ),
        AllocationRecord(
            optimization_run_id="run-400",
            incident_id="inc-4",
            source_location_id="wh-1",
            resource_type="Food",
            category="FOOD",
            unit="Kits",
            quantity_allocated=9999.0,
            quantity_requested=9999.0,
            quantity_unmet=0.0
        )
    ])

    req = ExecutionRequest(optimization_run_id="run-400", incident_id="inc-4")
    res = svc.execute_proposal(req)

    assert res.status == "FAILED"

    # NO resources must be deducted (Water must remain 1000.0, Food must remain 500.0)
    water = next(r for r in res_repo.get_all() if r.resource_type == "Water")
    food = next(r for r in res_repo.get_all() if r.resource_type == "Food")
    assert water.quantity_available == 1000.0
    assert food.quantity_available == 500.0
