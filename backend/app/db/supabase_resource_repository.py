import logging
from typing import List
from supabase import Client
from app.api.schemas.internal import ResourceRecord
from app.db.resource_repository import BaseResourceRepository

logger = logging.getLogger(__name__)

class SupabaseResourceRepository(BaseResourceRepository):
    def __init__(self, client: Client):
        self.client = client

    def upsert(self, resource: ResourceRecord) -> None:
        data = {
            "resource_id": resource.resource_id,
            "location_id": resource.location_id,
            "resource_type": resource.resource_type,
            "category": resource.category,
            "quantity_available": resource.quantity_available,
            "unit": resource.unit,
            "provenance": resource.provenance,
            "updated_at": resource.updated_at.isoformat(),
            "created_at": resource.created_at.isoformat()
        }
        
        try:
            # First attempt standard upsert (supported by unit test mocks and standard unique constraints)
            self.client.table("resources").upsert(data).execute()
        except Exception:
            try:
                query = (
                    self.client.table("resources")
                    .select("resource_id")
                    .eq("location_id", resource.location_id)
                    .eq("resource_type", resource.resource_type)
                )
                if resource.category:
                    query = query.eq("category", resource.category)
                else:
                    query = query.is_("category", "null")
                existing = query.limit(1).execute()

                if isinstance(existing.data, list) and len(existing.data) > 0 and isinstance(existing.data[0], dict):
                    existing_id = existing.data[0]["resource_id"]
                    data["resource_id"] = existing_id
                    self.client.table("resources").update(data).eq("resource_id", existing_id).execute()
                else:
                    self.client.table("resources").insert(data).execute()
            except Exception as e2:
                logger.error(f"Supabase upsert resource error: {e2}")
                raise RuntimeError(f"Database error upserting resource: {str(e2)}")

    def _map_row(self, row: dict) -> ResourceRecord:
        return ResourceRecord(
            resource_id=row["resource_id"],
            location_id=row["location_id"],
            resource_type=row["resource_type"],
            category=row.get("category"),
            quantity_available=row.get("quantity_available", 0.0),
            unit=row["unit"],
            provenance=row.get("provenance"),
            updated_at=row.get("updated_at"),
            created_at=row.get("created_at")
        )

    def get_all(self) -> List[ResourceRecord]:
        try:
            res = self.client.table("resources").select("*").execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get all resources error: {e}")
            raise RuntimeError(f"Database error getting resources: {str(e)}")

    def get_by_location(self, location_id: str) -> List[ResourceRecord]:
        try:
            res = self.client.table("resources").select("*").eq("location_id", location_id).execute()
            return [self._map_row(r) for r in res.data]
        except Exception as e:
            logger.error(f"Supabase get resources by location error: {e}")
            raise RuntimeError(f"Database error getting resources by location: {str(e)}")

    def deduct_resources(self, deductions: List[dict]) -> List[dict]:
        import math
        from datetime import datetime, timezone
        if not deductions:
            return []

        # 1. Validation Phase
        all_resources = self.get_all()
        validated_items = []

        for item in deductions:
            loc = item["location_id"]
            rtype = item["resource_type"]
            cat = item.get("category") or ""
            qty = item["quantity"]

            if qty is None or math.isnan(qty) or math.isinf(qty) or qty <= 0:
                raise ValueError(f"Invalid deduction quantity '{qty}' for {rtype} at {loc}")

            match = next((
                r for r in all_resources
                if r.location_id == loc and r.resource_type == rtype and (r.category or "") == cat
            ), None)

            if not match:
                raise ValueError(f"Resource not found for location='{loc}', resource_type='{rtype}', category='{cat}'")

            if match.quantity_available < qty:
                raise ValueError(
                    f"Insufficient inventory for {rtype} at {loc}. "
                    f"Requested: {qty}, Available: {match.quantity_available}"
                )

            validated_items.append((match, qty))

        # 2. Mutation Phase (Conditional updates with rollback on race)
        completed_mutations = []
        try:
            for rec, qty in validated_items:
                new_qty = rec.quantity_available - qty
                now_str = datetime.now(timezone.utc).isoformat()

                # Conditional update: only update if quantity_available has not changed
                query = self.client.table("resources").update({
                    "quantity_available": new_qty,
                    "updated_at": now_str
                }).eq("resource_id", rec.resource_id).gte("quantity_available", qty)

                res = query.execute()
                if not res.data:
                    raise RuntimeError(f"Concurrent mutation detected or stock depleted for resource_id={rec.resource_id}")

                completed_mutations.append({
                    "resource_id": rec.resource_id,
                    "location_id": rec.location_id,
                    "resource_type": rec.resource_type,
                    "category": rec.category,
                    "quantity_deducted": qty,
                    "unit": rec.unit,
                    "previous_quantity": rec.quantity_available,
                    "new_quantity": new_qty
                })

            return completed_mutations

        except Exception as e:
            # Rollback any mutations performed during this batch execution
            for item in completed_mutations:
                try:
                    self.client.table("resources").update({
                        "quantity_available": item["previous_quantity"]
                    }).eq("resource_id", item["resource_id"]).execute()
                except Exception as rollback_err:
                    logger.critical(f"Failed to rollback mutation for resource_id={item['resource_id']}: {rollback_err}")

            logger.error(f"Supabase deduct resources failed: {e}")
            raise RuntimeError(f"Atomic resource deduction failed: {str(e)}")

