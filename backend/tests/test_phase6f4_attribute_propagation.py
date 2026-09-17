import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.repositories import InMemoryIncidentRepository
from app.services.incident_service import IncidentService

client = TestClient(app)

def test_incident_canonical_attributes_survive_process_report():
    repo = InMemoryIncidentRepository()
    service = IncidentService(repo)
    
    report_data = {
        "source": "USGS",
        "source_record_id": "test-prop-1",
        "hazard_type": "Flood",
        "affected_population": 500,
        "latitude": 34.05,
        "longitude": -118.25,
        "ingested_at": datetime.utcnow().isoformat()
    }
    report, incident = service.process_report(report_data)
    
    assert incident.canonical_attributes.get("affected_population") == 500
    retrieved = repo.get(incident.incident_id)
    assert retrieved is not None
    assert retrieved.canonical_attributes.get("affected_population") == 500

def test_flood_affected_population_reaches_assessment():
    rep_res = client.post("/reports", json={
        "source": "NOAA",
        "source_record_id": "flood-prop-test-1",
        "hazard_type": "Flood",
        "affected_population": 500
    })
    assert rep_res.status_code == 201
    incident_id = rep_res.json()["message"].split()[-1].strip(".")
    
    ass_res = client.get(f"/incidents/{incident_id}/assessment")
    assert ass_res.status_code == 200
    data = ass_res.json()
    
    sev = data["severity"]
    assert sev["status"] == "success"
    assert sev["hazard_type"] == "Flood"
    assert sev["assessment_method"] == "POLICY"
    assert sev["policy_version"] == "FLOOD_POLICY_V1"
    
    # Evidence coverage > 0
    coverage = sev["evidence_coverage"]
    assert coverage["available_factors_count"] == 1
    assert "affected_population" in coverage["available_factors"]
    
    # Check contributing factor value
    factors = sev["contributing_factors"]
    assert len(factors) == 1
    assert factors[0]["factor"] == "affected_population"
    assert factors[0]["value"] == 500
    
    # Check missing factors remain missing
    assert "displaced_population" in coverage["missing_factors"]
    assert "population_density_sqkm" in coverage["missing_factors"]
    assert "damage_estimate" in coverage["missing_factors"]
    assert "trajectory" in coverage["missing_factors"]

def test_earthquake_routes_to_severity_v2():
    rep_res = client.post("/reports", json={
        "source": "USGS",
        "source_record_id": "eq-prop-test-1",
        "hazard_type": "Earthquake",
        "magnitude": 6.8
    })
    incident_id = rep_res.json()["message"].split()[-1].strip(".")
    
    ass_res = client.get(f"/incidents/{incident_id}/assessment")
    assert ass_res.status_code == 200
    data = ass_res.json()
    
    sev = data["severity"]
    assert sev["status"] == "success"
    assert sev["assessment_method"] == "ML"
    assert data["verification_status"] in ["VERIFIED", "CANDIDATE"]

def test_cyclone_routes_to_severity_v2():
    rep_res = client.post("/reports", json={
        "source": "NOAA",
        "source_record_id": "cyc-prop-test-1",
        "hazard_type": "Cyclone",
        "wind_speed": 110.0
    })
    incident_id = rep_res.json()["message"].split()[-1].strip(".")
    
    ass_res = client.get(f"/incidents/{incident_id}/assessment")
    assert ass_res.status_code == 200
    data = ass_res.json()
    
    sev = data["severity"]
    assert sev["status"] == "success"
    assert sev["assessment_method"] == "ML"

def test_unknown_hazard_remains_unsupported():
    rep_res = client.post("/reports", json={
        "source": "NOAA",
        "source_record_id": "volc-prop-test-1",
        "hazard_type": "Tornado"
    })
    incident_id = rep_res.json()["message"].split()[-1].strip(".")
    
    ass_res = client.get(f"/incidents/{incident_id}/assessment")
    assert ass_res.status_code == 200
    data = ass_res.json()
    assert data["severity"]["status"] == "unsupported_hazard"
