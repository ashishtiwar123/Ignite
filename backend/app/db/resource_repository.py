from abc import ABC, abstractmethod
from typing import List, Optional
from app.api.schemas.internal import ResourceRecord
from datetime import datetime, timezone

class BaseResourceRepository(ABC):
    @abstractmethod
    def upsert(self, resource: ResourceRecord) -> None:
        """
        Upserts inventory. Uniqueness is based on (location_id, resource_type, category).
        """
        pass

    @abstractmethod
    def get_all(self) -> List[ResourceRecord]:
        """
        Retrieves all available resources.
        """
        pass

    @abstractmethod
    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        """
        Retrieves resources for a specific location.
        """
        pass

    @abstractmethod
    def deduct_resources(self, deductions: List[dict]) -> List[dict]:
        """
        Atomically deducts resource quantities.
        deductions is a list of dicts with:
        {"location_id": str, "resource_type": str, "category": str, "quantity": float}
        Returns list of deducted item results. Raises ValueError if validation fails, leaving all resources untouched.
        """
        pass

class InMemoryResourceRepository(BaseResourceRepository):
    def __init__(self):
        self._resources: dict[str, ResourceRecord] = {}

    def upsert(self, resource: ResourceRecord) -> None:
        # Check for existing inventory by (location, type, category)
        category = resource.category or ""
        existing_key = f"{resource.location_id}:{resource.resource_type}:{category}"
        
        # We store internally by this unique key to simulate the UPSERT index
        if existing_key in self._resources:
            existing = self._resources[existing_key]
            # Upsert logic: keep existing ID, update quantity/timestamp
            existing.quantity_available = resource.quantity_available
            existing.unit = resource.unit
            existing.provenance = resource.provenance
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self._resources[existing_key] = resource

    def get_all(self) -> List[ResourceRecord]:
        return list(self._resources.values())

    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        return [r for r in self._resources.values() if r.location_id == location_id]

    def deduct_resources(self, deductions: List[dict]) -> List[dict]:
        import math
        if not deductions:
            return []

        # 1. Validation Phase (No mutations allowed until ALL validations pass)
        validated_items = []
        for item in deductions:
            loc = item["location_id"]
            rtype = item["resource_type"]
            cat = item.get("category") or ""
            qty = item["quantity"]

            if qty is None or math.isnan(qty) or math.isinf(qty) or qty <= 0:
                raise ValueError(f"Invalid deduction quantity '{qty}' for {rtype} at {loc}")

            key = f"{loc}:{rtype}:{cat}"
            if key not in self._resources:
                raise ValueError(f"Resource not found for location='{loc}', resource_type='{rtype}', category='{cat}'")

            rec = self._resources[key]
            if rec.quantity_available < qty:
                raise ValueError(
                    f"Insufficient inventory for {rtype} at {loc}. "
                    f"Requested: {qty}, Available: {rec.quantity_available}"
                )

            validated_items.append((key, rec, qty))

        # 2. Mutation Phase (Atomic commit)
        results = []
        for key, rec, qty in validated_items:
            prev_qty = rec.quantity_available
            rec.quantity_available -= qty
            rec.updated_at = datetime.now(timezone.utc)
            results.append({
                "resource_id": rec.resource_id,
                "location_id": rec.location_id,
                "resource_type": rec.resource_type,
                "category": rec.category,
                "quantity_deducted": qty,
                "unit": rec.unit,
                "previous_quantity": prev_qty,
                "new_quantity": rec.quantity_available
            })

        return results

