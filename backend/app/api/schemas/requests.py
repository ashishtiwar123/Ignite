from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ReportCreate(BaseModel):
    source: str
    source_record_id: str
    source_url: Optional[str] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    observed_at: Optional[datetime] = None
    hazard_type: str = "UNKNOWN"
    hazard_subtype: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    country: Optional[str] = None
    administrative_area: Optional[str] = None
    magnitude: Optional[float] = None
    intensity: Optional[float] = None
    depth: Optional[float] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None
    affected_population: Optional[int] = None
    damage_estimate: Optional[float] = None
    raw_text: Optional[str] = None

class AssessmentReassessRequest(BaseModel):
    reason: str
    new_evidence: Optional[Dict[str, Any]] = None

class AllocationOptimizeRequest(BaseModel):
    incident_id: str
    # Assuming minimal API for now. In reality this might include inventory updates.
