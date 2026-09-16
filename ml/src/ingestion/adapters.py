import abc
from datetime import datetime, timezone
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from ml.src.incident.schemas import Report
from ml.src.incident.normalization import normalize_hazard_type, normalize_timestamp
from ml.src.incident.validation import validate_report_fields

class BaseAdapter(abc.ABC):
    """
    Base interface for source adapters.
    Converts raw source JSON into a canonical Report object.
    """
    def __init__(self, source_name: str):
        self.source_name = source_name
        
    @abc.abstractmethod
    def parse(self, raw_record: Dict[str, Any]) -> Report:
        pass

class USGSAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("USGS")
        
    def parse(self, raw_record: Dict[str, Any]) -> Report:
        # Expected raw_record structure for USGS GeoJSON Feature
        properties = raw_record.get('properties', {})
        geometry = raw_record.get('geometry', {})
        
        source_id = raw_record.get('id') or properties.get('ids', 'unknown').strip(',')
        
        # Coordinates: [longitude, latitude, depth]
        coords = geometry.get('coordinates', [])
        lon = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None
        depth = coords[2] if len(coords) > 2 else None
        
        timestamp_ms = properties.get('time')
        observed_dt = normalize_timestamp(timestamp_ms)
        
        hazard_type = normalize_hazard_type("Earthquake")
        
        report_dict = {
            "source": self.source_name,
            "source_record_id": str(source_id),
            "source_url": properties.get('url'),
            "ingested_at": datetime.now(timezone.utc),
            "observed_at": observed_dt,
            "hazard_type": hazard_type,
            "latitude": lat,
            "longitude": lon,
            "location_name": properties.get('place'),
            "magnitude": properties.get('mag'),
            "depth": depth,
            "raw_payload_reference": raw_record,
            "source_confidence": 1.0 # USGS is highly authoritative for EQs
        }
        
        report_dict, _ = validate_report_fields(report_dict)
        return Report(**report_dict)

class GDACSAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("GDACS")
        
    def parse(self, raw_record: Dict[str, Any]) -> Report:
        source_id = str(raw_record.get('eventid', 'unknown'))
        raw_hazard = raw_record.get('eventtype', 'UNKNOWN')
        hazard_type = normalize_hazard_type(raw_hazard)
        
        observed_dt = normalize_timestamp(raw_record.get('fromdate'))
        
        report_dict = {
            "source": self.source_name,
            "source_record_id": source_id,
            "source_url": raw_record.get('link'),
            "ingested_at": datetime.now(timezone.utc),
            "observed_at": observed_dt,
            "hazard_type": hazard_type,
            "latitude": raw_record.get('latitude'),
            "longitude": raw_record.get('longitude'),
            "location_name": raw_record.get('country'),
            "country": raw_record.get('country'),
            "magnitude": raw_record.get('severitydata', {}).get('magnitude'),
            "raw_payload_reference": raw_record,
            "source_confidence": 0.9 
        }
        
        report_dict, _ = validate_report_fields(report_dict)
        return Report(**report_dict)
