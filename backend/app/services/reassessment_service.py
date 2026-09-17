import logging
from typing import List, Optional, Tuple, Dict, Any

from app.api.schemas.internal import (
    AssessmentRecord,
    NeedRecord,
    AllocationRecord,
    ActionRecord,
    AssessmentDiff,
    AllocationDeltaItem,
    AllocationDiff
)
from app.db.assessment_repository import BaseAssessmentRepository
from app.db.needs_repository import BaseNeedsRepository
from app.db.allocation_repository import BaseAllocationRepository
from app.db.action_repository import BaseActionRepository

logger = logging.getLogger(__name__)


class ReassessmentService:
    def __init__(
        self,
        assessment_repo: BaseAssessmentRepository,
        needs_repo: BaseNeedsRepository,
        allocation_repo: BaseAllocationRepository,
        action_repo: BaseActionRepository
    ):
        self.assessment_repo = assessment_repo
        self.needs_repo = needs_repo
        self.allocation_repo = allocation_repo
        self.action_repo = action_repo

    def validate_parent_assessment(self, parent_assessment_id: Optional[str], incident_id: str, current_assessment_id: Optional[str] = None) -> Optional[AssessmentRecord]:
        """
        Validates that parent_assessment_id belongs to the same incident, exists, and is not self-referential.
        """
        if not parent_assessment_id:
            return None

        if current_assessment_id and parent_assessment_id == current_assessment_id:
            raise ValueError(f"Self-referential parent_assessment_id '{parent_assessment_id}' is invalid.")

        parent = self.assessment_repo.get(parent_assessment_id)
        if not parent:
            raise ValueError(f"Parent assessment ID '{parent_assessment_id}' not found.")

        if parent.incident_id != incident_id:
            raise ValueError(f"Parent assessment incident_id '{parent.incident_id}' mismatch with target '{incident_id}'.")

        return parent

    def compare_assessments(
        self,
        prev: Optional[AssessmentRecord],
        curr: AssessmentRecord,
        prev_needs: Optional[List[NeedRecord]] = None,
        curr_needs: Optional[List[NeedRecord]] = None
    ) -> AssessmentDiff:
        """
        Computes deterministic diff between previous and current assessment.
        PRESERVES UNKNOWN/UNSUPPORTED/INSUFFICIENT_EVIDENCE explicitly without fabricating deltas.
        """
        if prev_needs is None and prev:
            prev_needs = self.needs_repo.get_by_incident(prev.incident_id)
        prev_needs = prev_needs or []

        if curr_needs is None:
            curr_needs = self.needs_repo.get_by_incident(curr.incident_id)
        curr_needs = curr_needs or []

        # 1. Severity Comparison
        prev_sev_class = prev.severity.get("severity_class") if (prev and isinstance(getattr(prev, "severity", None), dict)) else (getattr(prev, "severity_status", None) if prev else None)
        curr_sev_class = curr.severity.get("severity_class") if isinstance(getattr(curr, "severity", None), dict) else getattr(curr, "severity_status", None)

        def _get_sev_score(record):
            if not record:
                return None
            sev_dict = getattr(record, "severity", None)
            if isinstance(sev_dict, dict) and "severity_score" in sev_dict:
                return sev_dict.get("severity_score")
            return getattr(record, "severity_score", None)

        prev_sev_score = _get_sev_score(prev)
        curr_sev_score = _get_sev_score(curr)

        sev_changed = (prev_sev_class != curr_sev_class) or (prev_sev_score != curr_sev_score)

        # 2. Trajectory Comparison
        prev_traj = prev.trajectory.get("trajectory") if (prev and isinstance(getattr(prev, "trajectory", None), dict)) else (getattr(prev, "trajectory_status", None) if prev else None)
        curr_traj = curr.trajectory.get("trajectory") if isinstance(getattr(curr, "trajectory", None), dict) else getattr(curr, "trajectory_status", None)

        traj_changed = prev_traj != curr_traj

        # 3. Priority Comparison
        prev_prio_lvl = getattr(prev, "priority_level", None) if prev else None
        curr_prio_lvl = getattr(curr, "priority_level", None)

        prev_prio_score = getattr(prev, "priority_score", None) if prev else None
        curr_prio_score = getattr(curr, "priority_score", None)

        prio_changed = (prev_prio_lvl != curr_prio_lvl) or (prev_prio_score != curr_prio_score)
        prio_score_delta = (curr_prio_score or 0.0) - (prev_prio_score or 0.0)

        # 4. Needs Comparison (Quantitative & Qualitative preserved)
        prev_map: Dict[Tuple[str, str], NeedRecord] = {
            (n.resource_type, n.category or ""): n for n in prev_needs
        }
        curr_map: Dict[Tuple[str, str], NeedRecord] = {
            (n.resource_type, n.category or ""): n for n in curr_needs
        }

        added_needs = []
        increased_needs = []
        decreased_needs = []
        resolved_needs = []

        for key, curr_n in curr_map.items():
            if key not in prev_map:
                added_needs.append(curr_n.model_dump())
            else:
                prev_n = prev_map[key]
                p_qty = prev_n.quantity or 0.0
                c_qty = curr_n.quantity or 0.0
                if c_qty > p_qty:
                    increased_needs.append({"current": curr_n.model_dump(), "previous_quantity": p_qty})
                elif c_qty < p_qty:
                    decreased_needs.append({"current": curr_n.model_dump(), "previous_quantity": p_qty})

        for key, prev_n in prev_map.items():
            if key not in curr_map:
                resolved_needs.append(prev_n.model_dump())

        needs_changed = bool(added_needs or increased_needs or decreased_needs or resolved_needs)

        return AssessmentDiff(
            parent_assessment_id=prev.assessment_id if prev else None,
            current_assessment_id=curr.assessment_id,
            severity_changed=sev_changed,
            previous_severity=prev_sev_class,
            current_severity=curr_sev_class,
            previous_severity_score=prev_sev_score,
            current_severity_score=curr_sev_score,
            trajectory_changed=traj_changed,
            previous_trajectory=prev_traj,
            current_trajectory=curr_traj,
            priority_changed=prio_changed,
            previous_priority_level=prev_prio_lvl,
            current_priority_level=curr_prio_lvl,
            previous_priority_score=prev_prio_score,
            current_priority_score=curr_prio_score,
            priority_score_delta=prio_score_delta,
            needs_changed=needs_changed,
            added_needs=added_needs,
            increased_needs=increased_needs,
            decreased_needs=decreased_needs,
            resolved_needs=resolved_needs
        )

    def get_operational_allocation_baseline(self, incident_id: str) -> Tuple[Optional[str], List[AllocationRecord]]:
        """
        CORRECTION 2: Identifies the operational allocation baseline.
        Baseline MUST represent the latest successfully EXECUTED allocation/action.
        Rejected, pending, or failed proposals are NOT current operational state.
        """
        all_actions = self.action_repo.get_by_optimization_run("") if hasattr(self.action_repo, "get_all") else []
        # Get actions for incident
        inc_actions = [a for a in all_actions if a.incident_id == incident_id and a.status == "EXECUTED"]

        if not inc_actions:
            # Fallback check all actions if get_by_optimization_run didn't list all
            if hasattr(self.action_repo, "_storage"):
                inc_actions = [a for a in self.action_repo._storage.values() if a.incident_id == incident_id and a.status == "EXECUTED"]

        if not inc_actions:
            return None, []

        # Sort by executed_at descending
        inc_actions.sort(key=lambda a: a.executed_at or a.created_at, reverse=True)
        latest_executed = inc_actions[0]
        run_id = latest_executed.optimization_run_id

        if not run_id:
            return None, []

        all_allocs = self.allocation_repo.get_by_incident(incident_id)
        executed_allocs = [a for a in all_allocs if a.optimization_run_id == run_id]

        return run_id, executed_allocs

    def compare_allocations(
        self,
        prev_allocs: List[AllocationRecord],
        curr_allocs: List[AllocationRecord],
        baseline_run_id: Optional[str] = None,
        new_run_id: Optional[str] = None
    ) -> AllocationDiff:
        """
        CORRECTIONS 4 & 5: Computes deterministic allocation delta:
        NEW PROPOSAL - CURRENT OPERATIONAL ALLOCATION.
        Keyed by (resource_type, category, source_location_id, unit).
        """
        KeyType = Tuple[str, str, str, str]

        prev_map: Dict[KeyType, AllocationRecord] = {
            (a.resource_type, a.category or "", a.source_location_id, a.unit): a
            for a in prev_allocs if a.quantity_allocated > 0
        }
        curr_map: Dict[KeyType, AllocationRecord] = {
            (a.resource_type, a.category or "", a.source_location_id, a.unit): a
            for a in curr_allocs if a.quantity_allocated > 0
        }

        deltas: List[AllocationDeltaItem] = []
        total_prev = sum(a.quantity_allocated for a in prev_allocs)
        total_curr = sum(a.quantity_allocated for a in curr_allocs)

        for key, curr_a in curr_map.items():
            rtype, cat, loc, unit = key
            if key not in prev_map:
                deltas.append(AllocationDeltaItem(
                    resource_type=rtype,
                    category=cat,
                    source_location_id=loc,
                    unit=unit,
                    change_type="ADDED",
                    previous_quantity=0.0,
                    new_quantity=curr_a.quantity_allocated,
                    delta_quantity=curr_a.quantity_allocated,
                    explanation=f"New allocation of {curr_a.quantity_allocated} {unit} from {loc}"
                ))
            else:
                prev_a = prev_map[key]
                p_qty = prev_a.quantity_allocated
                c_qty = curr_a.quantity_allocated
                diff_qty = c_qty - p_qty

                if abs(diff_qty) < 1e-4:
                    deltas.append(AllocationDeltaItem(
                        resource_type=rtype, category=cat, source_location_id=loc, unit=unit,
                        change_type="UNCHANGED", previous_quantity=p_qty, new_quantity=c_qty, delta_quantity=0.0
                    ))
                elif diff_qty > 0:
                    deltas.append(AllocationDeltaItem(
                        resource_type=rtype, category=cat, source_location_id=loc, unit=unit,
                        change_type="INCREASED", previous_quantity=p_qty, new_quantity=c_qty, delta_quantity=diff_qty,
                        explanation=f"Increased allocation by +{diff_qty} {unit}"
                    ))
                else:
                    deltas.append(AllocationDeltaItem(
                        resource_type=rtype, category=cat, source_location_id=loc, unit=unit,
                        change_type="DECREASED", previous_quantity=p_qty, new_quantity=c_qty, delta_quantity=diff_qty,
                        explanation=f"Decreased allocation by {diff_qty} {unit}"
                    ))

        for key, prev_a in prev_map.items():
            rtype, cat, loc, unit = key
            if key not in curr_map:
                deltas.append(AllocationDeltaItem(
                    resource_type=rtype, category=cat, source_location_id=loc, unit=unit,
                    change_type="REMOVED", previous_quantity=prev_a.quantity_allocated, new_quantity=0.0,
                    delta_quantity=-prev_a.quantity_allocated,
                    explanation=f"Removed allocation of {prev_a.quantity_allocated} {unit}"
                ))

        meaningful = any(d.change_type != "UNCHANGED" for d in deltas)

        return AllocationDiff(
            baseline_optimization_run_id=baseline_run_id,
            new_optimization_run_id=new_run_id,
            deltas=deltas,
            total_previous_allocated=total_prev,
            total_new_allocated=total_curr,
            net_allocated_delta=total_curr - total_prev,
            has_meaningful_change=meaningful
        )

    def is_reallocation_required(self, diff: AssessmentDiff, alloc_diff: Optional[AllocationDiff] = None) -> Tuple[str, bool]:
        """
        CORRECTION 6: Deterministic policy for whether reallocation is required.
        Returns (reallocation_decision_status, reallocation_required_bool).
        """
        if not diff:
            return "INSUFFICIENT_DATA", False

        # Operationally meaningful triggers:
        # 1. Newly added quantitative needs
        # 2. Increased quantitative needs
        # 3. Material priority score increase (> 0.05)
        # 4. Severity class change or score increase
        # 5. Meaningful allocation diff
        if diff.added_needs:
            return "REALLOCATION_REQUIRED", True

        if diff.increased_needs:
            return "REALLOCATION_REQUIRED", True

        if diff.priority_score_delta > 0.05:
            return "REALLOCATION_REQUIRED", True

        if diff.severity_changed:
            return "REALLOCATION_REQUIRED", True

        if alloc_diff and alloc_diff.has_meaningful_change:
            return "REALLOCATION_REQUIRED", True

        return "NO_REALLOCATION_REQUIRED", False
