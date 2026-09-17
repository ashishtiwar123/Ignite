from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_create_report():
    response = client.post("/reports", json={
        "source": "USGS",
        "source_record_id": "us1000",
        "hazard_type": "EARTHQUAKE",
        "latitude": 34.0,
        "longitude": -118.0
    })
    assert response.status_code == 201
    data = response.json()
    assert "report_id" in data
    assert data["status"] == "processing"

def test_create_invalid_report():
    response = client.post("/reports", json={
        "source": "USGS"
        # missing source_record_id
    })
    assert response.status_code == 422

def test_get_incidents():
    response = client.get("/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_incident_assessment_not_found():
    response = client.get("/incidents/nonexistent/assessment")
    assert response.status_code == 404

def test_get_incident_assessment_unsupported_hazard():
    # Create incident first via report
    rep = client.post("/reports", json={
        "source": "NOAA",
        "source_record_id": "flood1",
        "hazard_type": "VOLCANO"
    })
    incident_id = rep.json()["message"].split()[-1].strip(".")
    
    response = client.get(f"/incidents/{incident_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    # Check that unsupported hazard is handled safely and returned as such
    assert data["severity"]["status"] == "unsupported_hazard"

def test_reassess_not_implemented():
    # Create incident
    rep = client.post("/reports", json={
        "source": "NOAA",
        "source_record_id": "eq1",
        "hazard_type": "EARTHQUAKE"
    })
    incident_id = rep.json()["message"].split()[-1].strip(".")
    
    response = client.post(f"/incidents/{incident_id}/reassess", json={"reason": "new data"})
    assert response.status_code == 501

def test_optimization():
    response = client.post("/allocations/optimize", json={
        "incident_ids": ["test_id"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["solver_status"] in ["OPTIMAL", "INFEASIBLE", "FEASIBLE", "UNKNOWN"]
    assert "allocations" in data

def test_optimization_invalid():
    response = client.post("/allocations/optimize", json={})
    assert response.status_code == 422
