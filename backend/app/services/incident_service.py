from ml.src.incident.schemas import Report, IncidentCandidate
from app.db.base_repository import BaseIncidentRepository

class IncidentService:
    def __init__(self, incident_repo: BaseIncidentRepository):
        self.incident_repo = incident_repo

    def process_report(self, report_data: dict) -> tuple[Report, IncidentCandidate]:
        """
        Thin wrapper around ML incident extraction/matching
        """
        report = Report(**report_data)
        
        self.incident_repo.save_report(report)
        
        canonical_attrs = {}
        for f in ["affected_population", "damage_estimate", "magnitude", "intensity", "depth", "wind_speed", "pressure"]:
            val = getattr(report, f, None)
            if val is not None:
                canonical_attrs[f] = val

        incident = IncidentCandidate(
            hazard_type=report.hazard_type,
            status="CANDIDATE",
            first_observed_at=report.observed_at,
            centroid_latitude=report.latitude,
            centroid_longitude=report.longitude,
            canonical_attributes=canonical_attrs
        )
        incident.report_ids.append(report.report_id)
        
        # Save to repo
        self.incident_repo.save(incident)
        
        return report, incident

    def verify_incident(self, incident_id: str):
        """
        Trigger ML incident verification policy
        """
        pass
