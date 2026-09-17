from typing import Optional, List, Any
import logging
from supabase import Client
from ml.src.incident.schemas import IncidentCandidate, Report
from app.db.base_repository import BaseIncidentRepository

logger = logging.getLogger(__name__)

class SupabaseIncidentRepository(BaseIncidentRepository):
    def __init__(self, client: Client):
        self.client = client

    def save_report(self, report: Any) -> None:
        if not isinstance(report, Report):
            return
            
        data = {
            "report_id": report.report_id,
            "source": report.source,
            "source_record_id": report.source_record_id,
            "source_url": report.source_url,
            "reported_at": report.observed_at.isoformat() if report.observed_at else None,
            "ingested_at": report.ingested_at.isoformat(),
            "hazard_type": report.hazard_type,
            "hazard_subtype": report.hazard_subtype,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "location_name": report.location_name,
            "country": report.country,
            "administrative_area": report.administrative_area,
            "magnitude": report.magnitude,
            "intensity": report.intensity,
            "depth": report.depth,
            "wind_speed": report.wind_speed,
            "pressure": report.pressure,
            "affected_population": report.affected_population,
            "damage_estimate": report.damage_estimate,
            "raw_text": report.raw_text
        }
        try:
            # Re-use existing report_id if source + source_record_id already exists
            if report.source and report.source_record_id:
                try:
                    res = self.client.table("reports").select("report_id").eq("source", report.source).eq("source_record_id", report.source_record_id).limit(1).execute()
                    if isinstance(res.data, list) and len(res.data) > 0 and isinstance(res.data[0], dict):
                        report.report_id = res.data[0]["report_id"]
                        data["report_id"] = report.report_id
                except Exception:
                    pass

            try:
                self.client.table("reports").upsert(data, on_conflict="source,source_record_id").execute()
            except Exception:
                self.client.table("reports").upsert(data).execute()
        except Exception as e:
            logger.error(f"Supabase save_report error: {e}")
            raise RuntimeError(f"Database error saving report: {str(e)}")

    def save(self, incident: IncidentCandidate) -> None:
        incident_data = {
            "incident_id": incident.incident_id,
            "hazard_type": incident.hazard_type,
            "status": incident.status,
            "centroid_latitude": incident.centroid_latitude,
            "centroid_longitude": incident.centroid_longitude,
            "first_observed_at": incident.first_observed_at.isoformat() if incident.first_observed_at else None,
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat()
        }
        
        try:
            self.client.table("incidents").upsert(incident_data).execute()
            
            # Map reports via incident_evidence (idempotent upsert on unique constraint)
            for report_id in incident.report_ids:
                evidence_data = {
                    "incident_id": incident.incident_id,
                    "report_id": report_id
                }
                self.client.table("incident_evidence").upsert(evidence_data, on_conflict="incident_id,report_id").execute()
                
        except Exception as e:
            logger.error(f"Supabase save incident error: {e}")
            raise RuntimeError(f"Database error saving incident: {str(e)}")

    def get(self, incident_id: str) -> Optional[IncidentCandidate]:
        try:
            res = self.client.table("incidents").select("*").eq("incident_id", incident_id).execute()
            if not res.data:
                return None
            
            row = res.data[0]
            # Fetch related evidence
            ev_res = self.client.table("incident_evidence").select("report_id").eq("incident_id", incident_id).execute()
            report_ids = [r["report_id"] for r in ev_res.data]
            
            canonical_attrs = {}
            conflicts = []
            if report_ids:
                try:
                    rep_res = self.client.table("reports").select("*").in_("report_id", report_ids).execute()
                    if rep_res.data:
                        field_values = {}
                        tracked_fields = [
                            "affected_population", 
                            "damage_estimate", 
                            "magnitude", 
                            "intensity", 
                            "depth", 
                            "wind_speed", 
                            "pressure"
                        ]
                        for rep in rep_res.data:
                            src = rep.get("source", "UNKNOWN")
                            for f in tracked_fields:
                                val = rep.get(f)
                                if val is not None:
                                    if f not in field_values:
                                        field_values[f] = []
                                    field_values[f].append({"source": src, "value": val})
                        
                        for field, values in field_values.items():
                            unique_vals = {v["value"] for v in values}
                            if len(unique_vals) > 1:
                                conflicts.append({"field": field, "values": values})
                                canonical_attrs[field] = values[0]["value"]
                            else:
                                canonical_attrs[field] = values[0]["value"]
                except Exception as ex:
                    logger.warning(f"Error fetching report attributes for incident {incident_id}: {ex}")

            return IncidentCandidate(
                incident_id=row["incident_id"],
                hazard_type=row["hazard_type"],
                status=row["status"],
                centroid_latitude=row.get("centroid_latitude"),
                centroid_longitude=row.get("centroid_longitude"),
                first_observed_at=row.get("first_observed_at"),
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
                report_ids=report_ids,
                canonical_attributes=canonical_attrs,
                conflicting_information=conflicts
            )
        except Exception as e:
            logger.error(f"Supabase get incident error: {e}")
            raise RuntimeError(f"Database error getting incident: {str(e)}")

    def get_all(self) -> List[IncidentCandidate]:
        try:
            res = self.client.table("incidents").select("*").execute()
            incidents = []
            for row in res.data:
                incident = IncidentCandidate(
                    incident_id=row["incident_id"],
                    hazard_type=row["hazard_type"],
                    status=row["status"],
                    centroid_latitude=row.get("centroid_latitude"),
                    centroid_longitude=row.get("centroid_longitude"),
                    first_observed_at=row.get("first_observed_at"),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at")
                )
                incidents.append(incident)
            return incidents
        except Exception as e:
            logger.error(f"Supabase get_all incidents error: {e}")
            raise RuntimeError(f"Database error getting all incidents: {str(e)}")
