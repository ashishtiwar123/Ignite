from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class Report(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    source_record_id: str
    source_url: Optional[str] = None
    ingested_at: datetime
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
    source_confidence: Optional[float] = None
    extraction_confidence: Optional[float] = None
    raw_payload_reference: Optional[Dict[str, Any]] = None
    schema_version: str = "1.0"

class IncidentCandidate(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hazard_type: str
    status: str = "CANDIDATE" # CANDIDATE, NEEDS_VERIFICATION, VERIFIED, REJECTED
    first_observed_at: Optional[datetime] = None
    last_observed_at: Optional[datetime] = None
    
    centroid_latitude: Optional[float] = None
    centroid_longitude: Optional[float] = None
    location_precision: Optional[str] = None
    
    report_ids: List[str] = Field(default_factory=list)
    source_count: int = 0
    source_list: List[str] = Field(default_factory=list)
    
    matching_confidence: Optional[float] = None
    matching_reasons: List[str] = Field(default_factory=list)
    conflicting_information: List[Dict[str, Any]] = Field(default_factory=list)
    
    raw_report_count: int = 0
    canonical_attributes: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"
