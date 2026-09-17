from typing import List, Optional

from datetime import datetime, timezone

import logging

from app.api.schemas.internal import ApprovalRecord
from app.db.approval_repository import BaseApprovalRepository

from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseApprovalRepository(BaseApprovalRepository):

    def __init__(self, client: Client):
        self.client = client

    # ============================================================
    # GET BY ID
    # ============================================================

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:

        response = (
            self.client
            .table("approvals")
            .select("*")
            .eq("approval_id", approval_id)
            .execute()
        )

        if response.data:
            return ApprovalRecord(**response.data[0])

        return None

    # ============================================================
    # GET ALL
    # ============================================================

    def get_all(self) -> List[ApprovalRecord]:

        response = (
            self.client
            .table("approvals")
            .select("*")
            .execute()
        )

        return [
            ApprovalRecord(**r)
            for r in response.data
        ]

    # ============================================================
    # GET BY OPTIMIZATION RUN
    # ============================================================

    def get_by_optimization_run(
        self,
        optimization_run_id: str,
    ) -> List[ApprovalRecord]:

        response = (
            self.client
            .table("approvals")
            .select("*")
            .eq(
                "optimization_run_id",
                optimization_run_id,
            )
            .execute()
        )

        return [
            ApprovalRecord(**r)
            for r in response.data
        ]

    # ============================================================
    # GET BY INCIDENT
    # ============================================================

    def get_by_incident(
        self,
        incident_id: str,
    ) -> List[ApprovalRecord]:

        response = (
            self.client
            .table("approvals")
            .select("*")
            .eq(
                "incident_id",
                incident_id,
            )
            .execute()
        )

        return [
            ApprovalRecord(**r)
            for r in response.data
        ]

    # ============================================================
    # UPSERT
    # ============================================================

    def upsert(
        self,
        record: ApprovalRecord,
    ) -> ApprovalRecord:

        # --------------------------------------------------------
        # 1. Enforce immutability
        # --------------------------------------------------------

        existing = self.get(
            record.approval_id
        )

        if (
            existing
            and existing.status
            in [
                "APPROVED",
                "REJECTED",
                "REVISION_REQUESTED",
            ]
        ):

            if record.status != existing.status:

                raise ValueError(
                    "Cannot mutate an already finalized "
                    "approval decision "
                    f"('{existing.status}' -> "
                    f"'{record.status}')."
                )

        # --------------------------------------------------------
        # 2. Enforce no conflicting decisions
        #    for the same optimization run
        # --------------------------------------------------------

        if (
            record.optimization_run_id
            and record.status
            in [
                "APPROVED",
                "REJECTED",
                "REVISION_REQUESTED",
            ]
        ):

            existing_for_run = (
                self.get_by_optimization_run(
                    record.optimization_run_id
                )
            )

            for ex in existing_for_run:

                if (
                    ex.approval_id
                    != record.approval_id
                    and ex.status
                    in [
                        "APPROVED",
                        "REJECTED",
                        "REVISION_REQUESTED",
                    ]
                ):

                    raise ValueError(
                        "Cannot create a conflicting "
                        "approval record for this "
                        "optimization run."
                    )

        # --------------------------------------------------------
        # 3. Serialize Pydantic model
        # --------------------------------------------------------

        data = record.model_dump()

        # ========================================================
        # DEBUG — IMPORTANT
        # ========================================================
        #
        # This tells us whether thread_id is already present
        # when the repository receives the ApprovalRecord.
        #
        # Do NOT log API keys, credentials, or raw secrets here.
        # ========================================================

        print(
            "[DEBUG APPROVAL REPO] "
            f"approval_id={record.approval_id} "
            f"incident_id={record.incident_id} "
            f"optimization_run_id={record.optimization_run_id} "
            f"thread_id={record.thread_id}"
        )

        print(
            f"[DEBUG APPROVAL DATA] {data}"
        )

        # --------------------------------------------------------
        # 4. Serialize datetime values
        # --------------------------------------------------------

        data["created_at"] = (
            data["created_at"].isoformat()
            if data.get("created_at")
            else None
        )

        data["decided_at"] = (
            data["decided_at"].isoformat()
            if data.get("decided_at")
            else None
        )

        # --------------------------------------------------------
        # 5. Persist to Supabase
        # --------------------------------------------------------

        try:

            response = (
                self.client
                .table("approvals")
                .upsert(data)
                .execute()
            )

        except Exception as ex:

            # ----------------------------------------------------
            # Backward compatibility:
            # If an older database does not yet have thread_id,
            # retry without that column.
            # ----------------------------------------------------

            error_text = str(ex).lower()

            if (
                "thread_id" in error_text
                and (
                    "column" in error_text
                    or "does not exist" in error_text
                )
            ):

                print(
                    "[DEBUG APPROVAL REPO] "
                    "thread_id column unavailable; "
                    "using legacy approval payload."
                )

                data_legacy = dict(data)

                data_legacy.pop(
                    "thread_id",
                    None,
                )

                response = (
                    self.client
                    .table("approvals")
                    .upsert(data_legacy)
                    .execute()
                )

            else:

                raise

        # --------------------------------------------------------
        # 6. Validate Supabase response
        # --------------------------------------------------------

        if not response.data:

            raise RuntimeError(
                "Supabase approval upsert returned "
                "no data."
            )

        # --------------------------------------------------------
        # 7. Reconstruct persisted record
        # --------------------------------------------------------

        res_record = ApprovalRecord(
            **response.data[0]
        )

        # ========================================================
        # DEBUG — PERSISTED RESULT
        # ========================================================

        print(
            "[DEBUG APPROVAL REPO RESULT] "
            f"approval_id={res_record.approval_id} "
            f"incident_id={res_record.incident_id} "
            f"optimization_run_id="
            f"{res_record.optimization_run_id} "
            f"thread_id={res_record.thread_id} "
            f"status={res_record.status}"
        )

        # --------------------------------------------------------
        # 8. Preserve thread_id in returned object
        #
        # If Supabase response does not return the column for
        # whatever reason, preserve the value received from the
        # caller in the Python object.
        #
        # IMPORTANT:
        # This does NOT change the database row.
        # It only preserves the returned application object.
        # --------------------------------------------------------

        if (
            record.thread_id is not None
            and not getattr(
                res_record,
                "thread_id",
                None,
            )
        ):

            res_record.thread_id = (
                record.thread_id
            )

            print(
                "[DEBUG APPROVAL REPO RESULT] "
                "thread_id restored from input "
                "record in returned object."
            )

        return res_record

    # ============================================================
    # DELETE
    # ============================================================

    def delete(
        self,
        approval_id: str,
    ) -> bool:

        response = (
            self.client
            .table("approvals")
            .delete()
            .eq(
                "approval_id",
                approval_id,
            )
            .execute()
        )

        return len(response.data) > 0