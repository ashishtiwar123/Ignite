from typing import List

from ml.src.optimization.engine import optimize_allocation
from ml.src.optimization.schemas import (
    AllocationContext,
    ResourceInventory,
)
from ml.src.needs.schemas import ResourceRequirement
from ml.src.priority.schemas import PriorityAssessment

from app.api.schemas.internal import (
    AllocationRecord,
    OptimizationRequest,
    OptimizationResponse,
)
from app.db.allocation_repository import BaseAllocationRepository
from app.db.needs_repository import BaseNeedsRepository
from app.db.resource_repository import BaseResourceRepository
from app.db.assessment_repository import BaseAssessmentRepository


class AllocationService:
    def __init__(
        self,
        allocation_repo: BaseAllocationRepository,
        needs_repo: BaseNeedsRepository,
        resource_repo: BaseResourceRepository,
        assessment_repo: BaseAssessmentRepository,
    ):
        self.allocation_repo = allocation_repo
        self.needs_repo = needs_repo
        self.resource_repo = resource_repo
        self.assessment_repo = assessment_repo

    def optimize(self, request: OptimizationRequest) -> OptimizationResponse:
        run_id = request.optimization_run_id

        # ---------------------------------------------------------
        # 1. Fetch assessments for priority context
        # ---------------------------------------------------------
        priority_assessments = []

        for inc_id in request.incident_ids:
            latest = self.assessment_repo.get_latest_for_incident(inc_id)

            if latest and latest.priority_score is not None:
                priority_assessments.append(
                    PriorityAssessment(
                        verified_incident_id=inc_id,
                        priority_level=latest.priority_level or "UNKNOWN",
                        priority_score=latest.priority_score,
                        explanation=(
                            f"Fetched from latest assessment "
                            f"{latest.assessment_id}"
                        ),
                    )
                )
            else:
                # Fallback to zero priority if no assessment exists.
                priority_assessments.append(
                    PriorityAssessment(
                        verified_incident_id=inc_id,
                        priority_level="UNKNOWN",
                        priority_score=0.0,
                        explanation="No assessment found",
                    )
                )

        # ---------------------------------------------------------
        # 2. Fetch needs for context
        # ---------------------------------------------------------
        all_requirements = []

        for inc_id in request.incident_ids:
            needs = self.needs_repo.get_by_incident(inc_id)

            for n in needs:
                # Qualitative needs have quantity=None and are ignored
                # naturally by the optimizer.
                req = ResourceRequirement(
                    requirement_id=n.need_id,
                    verified_incident_id=n.incident_id,
                    resource_type=n.resource_type,
                    category=n.category or "GENERAL",
                    quantity=n.quantity,
                    unit=n.unit or "unknown",
                    urgency=n.urgency or "MEDIUM",
                    status=n.status or "CALCULATED",
                    rule_id=n.rule_id or "persisted",
                    explanation=n.explanation or "",
                )

                all_requirements.append(req)

        # ---------------------------------------------------------
        # 3. Fetch all inventory
        # ---------------------------------------------------------
        all_resources = self.resource_repo.get_all()
        inventory = []

        for r in all_resources:
            inv = ResourceInventory(
                inventory_id=r.resource_id,
                location_id=r.location_id,
                resource_type=r.resource_type,
                category=r.category or "GENERAL",
                quantity_available=r.quantity_available,
                unit=r.unit,
            )

            inventory.append(inv)

        # ---------------------------------------------------------
        # 4. Construct AllocationContext
        # ---------------------------------------------------------
        context = AllocationContext(
            optimization_run_id=run_id,
            incidents=priority_assessments,
            requirements=all_requirements,
            inventory=inventory,
        )

        # ---------------------------------------------------------
        # 5. Invoke OR-Tools optimization engine
        # ---------------------------------------------------------
        ml_result = optimize_allocation(context)

        # ---------------------------------------------------------
        # 6. Map AllocationResult -> internal AllocationRecord
        # ---------------------------------------------------------
        records = []

        for a in ml_result.allocations:
            rec = AllocationRecord(
                optimization_run_id=a.optimization_run_id,
                incident_id=a.verified_incident_id,
                requirement_id=a.requirement_id,
                source_location_id=a.source_location_id,
                resource_type=a.resource_type,
                category=a.category,
                unit=a.unit,
                quantity_allocated=a.quantity_allocated,
                quantity_requested=a.quantity_requested,
                quantity_unmet=a.quantity_unmet,
                priority_score=a.priority_score,
                solver_status=ml_result.solver_status,
                explanation=a.explanation,
            )

            records.append(rec)

        # ---------------------------------------------------------
        # 7. DEBUG: verify allocation generation before persistence
        # ---------------------------------------------------------
        print(
            f"[DEBUG ALLOCATION] "
            f"run_id={run_id} "
            f"ml_allocations={len(ml_result.allocations)} "
            f"records={len(records)}"
        )

        # ---------------------------------------------------------
        # 8. Persist allocation records
        # ---------------------------------------------------------
        if records:
            self.allocation_repo.save_allocations(records)

        # ---------------------------------------------------------
        # 9. Return optimization response
        # ---------------------------------------------------------
        return OptimizationResponse(
            optimization_run_id=ml_result.optimization_run_id,
            solver_status=ml_result.solver_status,
            allocations=records,
            total_requested=ml_result.total_requested,
            total_allocated=ml_result.total_allocated,
            total_unmet=ml_result.total_unmet,
            objective_value=ml_result.objective_value,
            generated_at=ml_result.generated_at,
        )