import pytest
import sys
import os
from datetime import datetime, timezone

# Ensure backend is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.schemas.internal import (
    AssessmentRecord,
    NeedRecord,
    AllocationRecord,
    ActionRecord
)
from app.db.assessment_repository import InMemoryAssessmentRepository
from app.db.needs_repository import InMemoryNeedsRepository
from app.db.allocation_repository import InMemoryAllocationRepository
from app.db.action_repository import InMemoryActionRepository
from app.services.reassessment_service import ReassessmentService


@pytest.fixture
def repos():
    ass_repo = InMemoryAssessmentRepository()
    needs_repo = InMemoryNeedsRepository()
    alloc_repo = InMemoryAllocationRepository()
    act_repo = InMemoryActionRepository()
    return ass_repo, needs_repo, alloc_repo, act_repo


def test_parent_assessment_validation(repos):
    ass_repo, needs_repo, alloc_repo, act_repo = repos
    svc = ReassessmentService(ass_repo, needs_repo, alloc_repo, act_repo)

    parent = AssessmentRecord(incident_id="inc-1", severity_status="supported")
    ass_repo.save(parent)

    # Valid parent reference
    res = svc.validate_parent_assessment(parent.assessment_id, "inc-1")
    assert res.assessment_id == parent.assessment_id

    # Self reference error
    with pytest.raises(ValueError, match="Self-referential"):
        svc.validate_parent_assessment(parent.assessment_id, "inc-1", current_assessment_id=parent.assessment_id)

    # Mismatched incident error
    with pytest.raises(ValueError, match="mismatch"):
        svc.validate_parent_assessment(parent.assessment_id, "inc-2")


def test_assessment_comparison_preserves_unknown_and_computes_diff(repos):
    ass_repo, needs_repo, alloc_repo, act_repo = repos
    svc = ReassessmentService(ass_repo, needs_repo, alloc_repo, act_repo)

    prev = AssessmentRecord(
        incident_id="inc-cmp",
        severity_status="unsupported_hazard",
        severity=None,
        trajectory={"trajectory": "INSUFFICIENT_EVIDENCE"},
        priority_level="LOW",
        priority_score=2.0
    )
    curr = AssessmentRecord(
        incident_id="inc-cmp",
        severity_status="supported",
        severity={"severity_class": "EXTREME", "severity_score": 9.0},
        trajectory={"trajectory": "RAPIDLY_WORSENING"},
        priority_level="CRITICAL",
        priority_score=8.5
    )

    prev_needs = [NeedRecord(incident_id="inc-cmp", resource_type="Water", category="WATER", quantity=100.0, unit="Liters")]
    curr_needs = [
        NeedRecord(incident_id="inc-cmp", resource_type="Water", category="WATER", quantity=300.0, unit="Liters"),
        NeedRecord(incident_id="inc-cmp", resource_type="Food", category="FOOD", quantity=50.0, unit="Kits")
    ]

    diff = svc.compare_assessments(prev, curr, prev_needs, curr_needs)

    assert diff.severity_changed is True
    assert diff.previous_severity == "unsupported_hazard"
    assert diff.current_severity == "EXTREME"
    assert diff.trajectory_changed is True
    assert diff.previous_trajectory == "INSUFFICIENT_EVIDENCE"
    assert diff.current_trajectory == "RAPIDLY_WORSENING"
    assert diff.priority_score_delta == 6.5
    assert len(diff.added_needs) == 1
    assert diff.added_needs[0]["resource_type"] == "Food"
    assert len(diff.increased_needs) == 1
    assert diff.increased_needs[0]["current"]["resource_type"] == "Water"


def test_operational_allocation_baseline_selection(repos):
    ass_repo, needs_repo, alloc_repo, act_repo = repos
    svc = ReassessmentService(ass_repo, needs_repo, alloc_repo, act_repo)

    # Allocation run 1 (EXECUTED)
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-exec-1", incident_id="inc-base", source_location_id="wh-1",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=100.0,
                         quantity_requested=100.0, quantity_unmet=0.0)
    ])
    act_repo.save(ActionRecord(execution_id="exec-1", incident_id="inc-base", optimization_run_id="run-exec-1", status="EXECUTED"))

    # Allocation run 2 (REJECTED / Failed execution - should NOT become baseline)
    alloc_repo.save_allocations([
        AllocationRecord(optimization_run_id="run-rej-2", incident_id="inc-base", source_location_id="wh-1",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=999.0,
                         quantity_requested=999.0, quantity_unmet=0.0)
    ])
    act_repo.save(ActionRecord(execution_id="exec-2", incident_id="inc-base", optimization_run_id="run-rej-2", status="FAILED"))

    run_id, allocs = svc.get_operational_allocation_baseline("inc-base")
    assert run_id == "run-exec-1"
    assert len(allocs) == 1
    assert allocs[0].quantity_allocated == 100.0


def test_allocation_diff_computation(repos):
    ass_repo, needs_repo, alloc_repo, act_repo = repos
    svc = ReassessmentService(ass_repo, needs_repo, alloc_repo, act_repo)

    prev_allocs = [
        AllocationRecord(optimization_run_id="run-old", incident_id="inc-diff", source_location_id="wh-1",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=500.0,
                         quantity_requested=500.0, quantity_unmet=0.0),
        AllocationRecord(optimization_run_id="run-old", incident_id="inc-diff", source_location_id="wh-1",
                         resource_type="Food", category="FOOD", unit="Kits", quantity_allocated=200.0,
                         quantity_requested=200.0, quantity_unmet=0.0)
    ]

    curr_allocs = [
        AllocationRecord(optimization_run_id="run-new", incident_id="inc-diff", source_location_id="wh-1",
                         resource_type="Water", category="WATER", unit="Liters", quantity_allocated=800.0, # Increased +300
                         quantity_requested=800.0, quantity_unmet=0.0),
        # Food removed
        AllocationRecord(optimization_run_id="run-new", incident_id="inc-diff", source_location_id="wh-1",
                         resource_type="MedicalKits", category="MEDICAL", unit="Kits", quantity_allocated=30.0, # Added
                         quantity_requested=30.0, quantity_unmet=0.0)
    ]

    diff = svc.compare_allocations(prev_allocs, curr_allocs, "run-old", "run-new")

    assert diff.has_meaningful_change is True
    assert diff.net_allocated_delta == 130.0  # (800+30) - (500+200) = 830 - 700 = 130

    water_delta = next(d for d in diff.deltas if d.resource_type == "Water")
    assert water_delta.change_type == "INCREASED"
    assert water_delta.delta_quantity == 300.0

    food_delta = next(d for d in diff.deltas if d.resource_type == "Food")
    assert food_delta.change_type == "REMOVED"
    assert food_delta.delta_quantity == -200.0

    med_delta = next(d for d in diff.deltas if d.resource_type == "MedicalKits")
    assert med_delta.change_type == "ADDED"
    assert med_delta.delta_quantity == 30.0
