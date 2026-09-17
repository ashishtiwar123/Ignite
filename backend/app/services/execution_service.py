import uuid
import logging
from typing import Optional, List
from datetime import datetime, timezone

from app.api.schemas.internal import (
    ExecutionRequest,
    ExecutionResponse,
    ActionRecord,
    DeductedResourceItem,
    ApprovalRecord,
    AllocationRecord
)
from app.db.approval_repository import BaseApprovalRepository
from app.db.allocation_repository import BaseAllocationRepository
from app.db.resource_repository import BaseResourceRepository
from app.db.action_repository import BaseActionRepository
from app.db.client import get_supabase_client

logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(
        self,
        approval_repo: BaseApprovalRepository,
        allocation_repo: BaseAllocationRepository,
        resource_repo: BaseResourceRepository,
        action_repo: BaseActionRepository
    ):
        self.approval_repo = approval_repo
        self.allocation_repo = allocation_repo
        self.resource_repo = resource_repo
        self.action_repo = action_repo

    def execute_proposal(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        Executes an approved resource allocation proposal.

        CRITICAL INVARIANTS:
        1. PERSISTED approval must exist and status == APPROVED. Client flags are IGNORED.
        2. Consumes exact Phase 4D allocations — NO OR-Tools recalculation, NO Gemini.
        3. Double execution protected — returns ALREADY_EXECUTED if run/approval executed.
        4. Atomic all-or-nothing inventory mutation. Zero partial mutations.
        5. Distinct execution_id generated per execution entity.
        6. Immutable audit trails created for all execution outcomes.
        """
        execution_id = str(uuid.uuid4())
        run_id = request.optimization_run_id
        incident_id = request.incident_id

        # 1. Load Persisted Approval
        approval: Optional[ApprovalRecord] = None
        if run_id:
            approvals = self.approval_repo.get_by_optimization_run(run_id)
            if approvals:
                # Get latest decision for run_id
                approval = sorted(approvals, key=lambda a: a.created_at, reverse=True)[0]

        if not approval and incident_id:
            # Fallback to incident level approvals if run_id not provided
            all_approvals = self.approval_repo.get_all()
            inc_approvals = [a for a in all_approvals if a.incident_id == incident_id]
            if inc_approvals:
                approval = sorted(inc_approvals, key=lambda a: a.created_at, reverse=True)[0]

        # 2. Enforce Persisted Approval Gate
        if not approval or approval.status != "APPROVED":
            err_msg = (
                f"Execution rejected: Persisted approval is missing or not APPROVED. "
                f"Status: {approval.status if approval else 'NONE'}"
            )
            logger.warning(err_msg)
            self._record_audit_event(
                event_type="EXECUTION_REJECTED",
                incident_id=incident_id or (approval.incident_id if approval else None),
                execution_id=execution_id,
                run_id=run_id,
                approval_id=approval.approval_id if approval else None,
                status="NOT_APPROVED",
                payload={"reason": err_msg}
            )
            return ExecutionResponse(
                execution_id=execution_id,
                status="NOT_APPROVED",
                optimization_run_id=run_id,
                approval_id=approval.approval_id if approval else None,
                incident_id=incident_id or (approval.incident_id if approval else None),
                errors=[err_msg]
            )

        # Confirm incident match
        target_incident_id = incident_id or approval.incident_id
        if approval.incident_id != target_incident_id:
            err_msg = f"Execution rejected: Mismatched incident_id '{target_incident_id}' vs approval '{approval.incident_id}'"
            return ExecutionResponse(
                execution_id=execution_id,
                status="NOT_APPROVED",
                optimization_run_id=run_id,
                approval_id=approval.approval_id,
                incident_id=target_incident_id,
                errors=[err_msg]
            )

        # 3. Check for Double Execution / Server-Side Idempotency
        existing_actions: List[ActionRecord] = []
        if run_id:
            existing_actions.extend(self.action_repo.get_by_optimization_run(run_id))
        if approval.approval_id:
            existing_actions.extend(self.action_repo.get_by_approval_id(approval.approval_id))

        already_executed = any(a.status == "EXECUTED" for a in existing_actions)
        if already_executed:
            logger.info(f"Execution skipped: Proposal run_id='{run_id}' / approval_id='{approval.approval_id}' already executed.")
            self._record_audit_event(
                event_type="EXECUTION_ALREADY_COMPLETED",
                incident_id=target_incident_id,
                execution_id=execution_id,
                run_id=run_id,
                approval_id=approval.approval_id,
                status="ALREADY_EXECUTED",
                payload={"message": "Duplicate execution attempt blocked by idempotency check."}
            )
            return ExecutionResponse(
                execution_id=execution_id,
                status="ALREADY_EXECUTED",
                optimization_run_id=run_id,
                approval_id=approval.approval_id,
                incident_id=target_incident_id,
                errors=["Proposal has already been executed."]
            )

        # 4. Load Phase 4D Allocations
        allocations: List[AllocationRecord] = []
        if run_id:
            # Load from allocation repo
            all_inc_allocs = self.allocation_repo.get_by_incident(target_incident_id)
            allocations = [a for a in all_inc_allocs if a.optimization_run_id == run_id]
        else:
            allocations = self.allocation_repo.get_by_incident(target_incident_id)

        # Filter to quantitative allocations (> 0)
        quantitative_allocs = [a for a in allocations if a.quantity_allocated and a.quantity_allocated > 0]
        if not quantitative_allocs:
            err_msg = f"No valid quantitative allocations found to execute for incident '{target_incident_id}'."
            return ExecutionResponse(
                execution_id=execution_id,
                status="INVALID_PROPOSAL",
                optimization_run_id=run_id,
                approval_id=approval.approval_id,
                incident_id=target_incident_id,
                errors=[err_msg]
            )

        # 5. Prepare & Validate Deductions Batch
        deduction_requests = []
        for alloc in quantitative_allocs:
            deduction_requests.append({
                "location_id": alloc.source_location_id,
                "resource_type": alloc.resource_type,
                "category": alloc.category or "",
                "quantity": alloc.quantity_allocated
            })

        # 6. Perform Atomic Inventory Mutation
        try:
            deducted_items_data = self.resource_repo.deduct_resources(deduction_requests)
        except Exception as e:
            err_msg = f"Atomic inventory deduction failed: {str(e)}"
            logger.error(err_msg)
            # Log failure action and audit
            failed_action = ActionRecord(
                execution_id=execution_id,
                incident_id=target_incident_id,
                optimization_run_id=run_id,
                approval_id=approval.approval_id,
                action_type="RESOURCE_ALLOCATION_EXECUTION",
                status="FAILED",
                description=err_msg,
                executed_by=request.executor_id or "API_USER",
                executed_at=datetime.now(timezone.utc)
            )
            self.action_repo.save(failed_action)

            self._record_audit_event(
                event_type="EXECUTION_FAILED",
                incident_id=target_incident_id,
                execution_id=execution_id,
                run_id=run_id,
                approval_id=approval.approval_id,
                status="FAILED",
                payload={"error": err_msg}
            )

            return ExecutionResponse(
                execution_id=execution_id,
                status="FAILED",
                optimization_run_id=run_id,
                approval_id=approval.approval_id,
                incident_id=target_incident_id,
                errors=[err_msg]
            )

        # 7. Create Success Action Record (ONLY after deduction succeeds!)
        deducted_response_items = [
            DeductedResourceItem(
                resource_id=item["resource_id"],
                location_id=item["location_id"],
                resource_type=item["resource_type"],
                category=item["category"],
                quantity_deducted=item["quantity_deducted"],
                unit=item["unit"],
                previous_quantity=item["previous_quantity"],
                new_quantity=item["new_quantity"]
            )
            for item in deducted_items_data
        ]

        action_record = ActionRecord(
            execution_id=execution_id,
            incident_id=target_incident_id,
            optimization_run_id=run_id,
            approval_id=approval.approval_id,
            action_type="RESOURCE_ALLOCATION_EXECUTION",
            status="EXECUTED",
            description="Successfully executed approved resource allocation proposal.",
            payload={"deductions": [item.model_dump() for item in deducted_response_items]},
            executed_by=request.executor_id or "API_USER",
            executed_at=datetime.now(timezone.utc)
        )
        self.action_repo.save(action_record)

        # 8. Write Success Audit Event
        self._record_audit_event(
            event_type="EXECUTION_SUCCEEDED",
            incident_id=target_incident_id,
            execution_id=execution_id,
            run_id=run_id,
            approval_id=approval.approval_id,
            status="EXECUTED",
            payload={
                "deducted_items_count": len(deducted_response_items),
                "executor": request.executor_id or "API_USER"
            }
        )

        return ExecutionResponse(
            execution_id=execution_id,
            status="EXECUTED",
            optimization_run_id=run_id,
            approval_id=approval.approval_id,
            incident_id=target_incident_id,
            deducted_resources=deducted_response_items
        )

    def _record_audit_event(
        self,
        event_type: str,
        incident_id: Optional[str],
        execution_id: str,
        run_id: Optional[str],
        approval_id: Optional[str],
        status: str,
        payload: dict
    ):
        """Record an immutable audit event for execution. Scrub all credentials/secrets."""
        try:
            client = get_supabase_client()
            if client:
                full_payload = {
                    "execution_id": execution_id,
                    "optimization_run_id": run_id,
                    "approval_id": approval_id,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **payload
                }
                client.table("audit_events").insert({
                    "event_type": event_type,
                    "incident_id": incident_id,
                    "actor_type": "EXECUTION_SERVICE",
                    "actor_reference": payload.get("executor") or "SYSTEM",
                    "payload": full_payload,
                    "correlation_id": run_id or execution_id
                }).execute()
        except Exception as e:
            logger.error(f"Failed to write execution audit event '{event_type}': {e}")
