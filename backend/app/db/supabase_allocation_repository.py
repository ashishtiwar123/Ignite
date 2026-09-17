from typing import List
import logging

from supabase import Client

from app.api.schemas.internal import AllocationRecord
from app.db.allocation_repository import BaseAllocationRepository

logger = logging.getLogger(__name__)


class SupabaseAllocationRepository(BaseAllocationRepository):
    def __init__(self, client: Client):
        self.client = client

    def _map_row(self, row: dict) -> AllocationRecord:
        return AllocationRecord(
            allocation_id=row["allocation_id"],
            optimization_run_id=row["optimization_run_id"],
            incident_id=row["incident_id"],
            requirement_id=row.get("requirement_id"),
            source_location_id=row["source_location_id"],
            resource_type=row["resource_type"],
            category=row.get("category"),
            unit=row["unit"],
            quantity_allocated=row["quantity_allocated"],
            quantity_requested=row["quantity_requested"],
            quantity_unmet=row["quantity_unmet"],
            priority_score=row.get("priority_score"),
            solver_status=row.get("solver_status"),
            explanation=row.get("explanation"),
            created_at=row["created_at"],
        )

    def save_allocations(
        self,
        allocations: List[AllocationRecord],
    ) -> None:

        # ---------------------------------------------------------
        # DEBUG 1: Confirm repository is reached
        # ---------------------------------------------------------
        print(
            "[DEBUG SUPABASE REPO] save_allocations CALLED "
            f"count={len(allocations)} "
            f"run_ids={[a.optimization_run_id for a in allocations]} "
            f"incident_ids={[a.incident_id for a in allocations]}"
        )

        if not allocations:
            logger.warning(
                "save_allocations called with empty allocation list"
            )
            return

        # ---------------------------------------------------------
        # 1. Validate optimization run IDs
        # ---------------------------------------------------------
        run_ids = {
            a.optimization_run_id
            for a in allocations
            if a.optimization_run_id
        }

        if len(run_ids) > 1:
            raise ValueError(
                "All allocations in one persistence operation must belong "
                "to the same optimization_run_id."
            )

        run_id = next(iter(run_ids), None)

        incident_ids = {
            a.incident_id
            for a in allocations
            if a.incident_id
        }

        if len(incident_ids) > 1:
            raise ValueError(
                "All allocations in one persistence operation must belong "
                "to the same incident_id."
            )

        incident_id = next(iter(incident_ids), None)

        # ---------------------------------------------------------
        # 2. Build payload
        # ---------------------------------------------------------
        payload = [
            a.model_dump(mode="json")
            for a in allocations
        ]

        logger.info(
            "Persisting %d allocation(s) "
            "for optimization_run_id=%s incident_id=%s",
            len(payload),
            run_id,
            incident_id,
        )

        try:

            # -----------------------------------------------------
            # 3. Exact-run idempotency check
            # -----------------------------------------------------
            if run_id:
                existing = (
                    self.client
                    .table("allocations")
                    .select(
                        "allocation_id,"
                        "optimization_run_id,"
                        "incident_id"
                    )
                    .eq("optimization_run_id", run_id)
                    .limit(1)
                    .execute()
                )

                if existing.data:
                    logger.info(
                        "Allocations already exist for "
                        "optimization_run_id=%s; "
                        "skipping duplicate persistence.",
                        run_id,
                    )
                    return

            # -----------------------------------------------------
            # 4. INSERT
            # -----------------------------------------------------
            response = (
                self.client
                .table("allocations")
                .insert(payload)
                .execute()
            )

            persisted_rows = response.data or []
            persisted_count = len(persisted_rows)

            # -----------------------------------------------------
            # DEBUG 2: Inspect actual INSERT response identities
            # -----------------------------------------------------
            print(
                "[DEBUG SUPABASE REPO] INSERT RESPONSE "
                f"run_id={run_id} "
                f"requested={len(payload)} "
                f"persisted={persisted_count}"
            )

            print(
                "[DEBUG SUPABASE REPO] INSERTED ROW IDENTITIES:",
                [
                    {
                        "allocation_id": row.get("allocation_id"),
                        "incident_id": row.get("incident_id"),
                        "optimization_run_id": row.get(
                            "optimization_run_id"
                        ),
                    }
                    for row in persisted_rows
                ],
            )

            # -----------------------------------------------------
            # 5. Validate row count
            # -----------------------------------------------------
            if persisted_count != len(payload):
                raise RuntimeError(
                    "Allocation persistence returned an unexpected "
                    "row count: "
                    f"requested={len(payload)}, "
                    f"persisted={persisted_count}, "
                    f"optimization_run_id={run_id}"
                )

            # -----------------------------------------------------
            # 6. Validate returned identity
            # -----------------------------------------------------
            returned_run_ids = {
                row.get("optimization_run_id")
                for row in persisted_rows
            }

            returned_incident_ids = {
                row.get("incident_id")
                for row in persisted_rows
            }

            if run_id and returned_run_ids != {run_id}:
                raise RuntimeError(
                    "Supabase returned allocation rows with an "
                    "unexpected optimization_run_id: "
                    f"expected={run_id}, "
                    f"returned={returned_run_ids}"
                )

            if incident_id and returned_incident_ids != {incident_id}:
                raise RuntimeError(
                    "Supabase returned allocation rows with an "
                    "unexpected incident_id: "
                    f"expected={incident_id}, "
                    f"returned={returned_incident_ids}"
                )

            logger.info(
                "Allocation persistence completed successfully: "
                "optimization_run_id=%s incident_id=%s "
                "requested=%d persisted=%d",
                run_id,
                incident_id,
                len(payload),
                persisted_count,
            )

        except Exception as e:
            logger.exception(
                "Failed to persist allocations for "
                "optimization_run_id=%s incident_id=%s",
                run_id,
                incident_id,
            )

            raise RuntimeError(
                "Database error saving allocations: "
                f"{str(e)}"
            ) from e

    def get_by_incident(
        self,
        incident_id: str,
    ) -> List[AllocationRecord]:

        try:
            response = (
                self.client
                .table("allocations")
                .select("*")
                .eq("incident_id", incident_id)
                .execute()
            )

            rows = response.data or []

            # -----------------------------------------------------
            # DEBUG: Show exactly what GET sees
            # -----------------------------------------------------
            print(
                "[DEBUG SUPABASE REPO] GET ALLOCATIONS "
                f"incident_id={incident_id} "
                f"count={len(rows)}"
            )

            print(
                "[DEBUG SUPABASE REPO] GET RUN IDS:",
                [
                    {
                        "allocation_id": row.get("allocation_id"),
                        "incident_id": row.get("incident_id"),
                        "optimization_run_id": row.get(
                            "optimization_run_id"
                        ),
                    }
                    for row in rows
                ],
            )

            return [
                self._map_row(row)
                for row in rows
            ]

        except Exception as e:
            logger.exception(
                "Failed to get allocations for incident_id=%s",
                incident_id,
            )

            raise RuntimeError(
                "Database error getting allocations: "
                f"{str(e)}"
            ) from e