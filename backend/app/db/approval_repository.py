from abc import ABC, abstractmethod
from typing import List, Optional
from app.api.schemas.internal import ApprovalRecord
import logging

logger = logging.getLogger(__name__)

class BaseApprovalRepository(ABC):
    @abstractmethod
    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        pass

    @abstractmethod
    def get_all(self) -> List[ApprovalRecord]:
        pass

    @abstractmethod
    def get_by_optimization_run(self, optimization_run_id: str) -> List[ApprovalRecord]:
        pass

    @abstractmethod
    def upsert(self, record: ApprovalRecord) -> ApprovalRecord:
        pass

    @abstractmethod
    def delete(self, approval_id: str) -> bool:
        pass


class InMemoryApprovalRepository(BaseApprovalRepository):
    def __init__(self):
        self._storage: dict = {}

    def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        return self._storage.get(approval_id)

    def get_all(self) -> List[ApprovalRecord]:
        return list(self._storage.values())

    def get_by_optimization_run(self, optimization_run_id: str) -> List[ApprovalRecord]:
        return [r for r in self._storage.values() if r.optimization_run_id == optimization_run_id]

    def upsert(self, record: ApprovalRecord) -> ApprovalRecord:
        existing = self.get(record.approval_id)

        # IMMUTABILITY: Once finalized, status cannot be changed to a different value
        if existing and existing.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
            if record.status != existing.status:
                raise ValueError(
                    f"Cannot mutate an already finalized approval decision "
                    f"('{existing.status}' -> '{record.status}')."
                )

        # CONFLICT: No two separate records may both be finalized for the same run
        if record.optimization_run_id and record.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
            for ex in self.get_by_optimization_run(record.optimization_run_id):
                if ex.approval_id != record.approval_id and ex.status in ["APPROVED", "REJECTED", "REVISION_REQUESTED"]:
                    raise ValueError(
                        "Cannot create a conflicting approval record for this optimization run."
                    )

        self._storage[record.approval_id] = record
        return record

    def delete(self, approval_id: str) -> bool:
        if approval_id in self._storage:
            del self._storage[approval_id]
            return True
        return False
