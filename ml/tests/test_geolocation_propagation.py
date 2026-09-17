import pytest
from datetime import datetime, timezone
from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.validation import validate_report_fields
from ml.src.incident.clustering import cluster_reports
from ml.src.agents.gemini_client import StructuredReportOutput

def test_validate_report_fields_valid_coordinates():
    data = {
        "hazard_type": "Flood",
        "latitude": 19.0701,
        "longitude": 72.8792
    }
    validated, errors = validate_report_fields(data)
    assert len(errors) == 0
    assert validated["latitude"] == 19.0701
    assert validated["longitude"] == 72.8792

def test_validate_report_fields_invalid_coordinates():
    data = {
        "hazard_type": "Flood",
        "latitude": 195.0, # out of bounds
        "longitude": -200.0
    }
    validated, errors = validate_report_fields(data)
    assert len(errors) == 2
    assert any(e["field"] == "latitude" for e in errors)
    assert any(e["field"] == "longitude" for e in errors)

def test_validate_report_fields_string_coordinates():
    data = {
        "hazard_type": "Flood",
        "latitude": "34.0522",
        "longitude": "-118.2437"
    }
    validated, errors = validate_report_fields(data)
    assert len(errors) == 0
    assert validated["latitude"] == 34.0522
    assert validated["longitude"] == -118.2437

def test_validate_report_fields_null_coordinates():
    data = {
        "hazard_type": "Flood",
        "latitude": None,
        "longitude": None
    }
    validated, errors = validate_report_fields(data)
    assert len(errors) == 0
    assert validated["latitude"] is None
    assert validated["longitude"] is None

def test_cluster_reports_centroid_calculation():
    now = datetime.now(timezone.utc)
    r1 = Report(
        source="USGS",
        source_record_id="rec-1",
        ingested_at=now,
        observed_at=now,
        hazard_type="Flood",
        latitude=10.0,
        longitude=20.0
    )
    r2 = Report(
        source="GDACS",
        source_record_id="rec-2",
        ingested_at=now,
        observed_at=now,
        hazard_type="Flood",
        latitude=10.02,
        longitude=20.02
    )
    candidates = cluster_reports([r1, r2])
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.centroid_latitude == pytest.approx(10.01)
    assert cand.centroid_longitude == pytest.approx(20.01)
    assert cand.location_precision == "POINT"

def test_cluster_reports_missing_coordinates():
    r1 = Report(
        source="LOCAL",
        source_record_id="rec-3",
        ingested_at=datetime.now(timezone.utc),
        hazard_type="Flood",
        latitude=None,
        longitude=None
    )
    candidates = cluster_reports([r1])
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.centroid_latitude is None
    assert cand.centroid_longitude is None
    assert cand.location_precision == "UNKNOWN"

def test_structured_report_output_schema_supports_coordinates():
    output = StructuredReportOutput(
        hazard_type="Flood",
        location="Downtown",
        latitude=34.05,
        longitude=-118.25,
        observed_at="2026-09-17T00:00:00Z",
        claims=[],
        entities=[],
        quantitative_facts=[],
        uncertainties=[],
        conflicts=[],
        source_text_summary="Summary"
    )
    assert output.latitude == 34.05
    assert output.longitude == -118.25
