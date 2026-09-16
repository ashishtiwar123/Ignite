import pytest
from unittest import mock
from app.db.supabase_repository import SupabaseIncidentRepository
from ml.src.incident.schemas import IncidentCandidate, Report
from datetime import datetime, timezone

@pytest.fixture
def mock_supabase_client():
    client = mock.Mock()
    # Mock chain: client.table().upsert().execute()
    client.table.return_value.upsert.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock.Mock(data=[])
    return client

def test_save_report(mock_supabase_client):
    repo = SupabaseIncidentRepository(mock_supabase_client)
    report = Report(
        source="USGS",
        source_record_id="us123",
        hazard_type="EARTHQUAKE",
        ingested_at=datetime.now(timezone.utc)
    )
    repo.save_report(report)
    
    mock_supabase_client.table.assert_any_call("reports")
    # Verify upsert was called
    assert mock_supabase_client.table().upsert.called

def test_save_incident(mock_supabase_client):
    repo = SupabaseIncidentRepository(mock_supabase_client)
    incident = IncidentCandidate(
        hazard_type="EARTHQUAKE",
        status="CANDIDATE",
        report_ids=["rep1", "rep2"]
    )
    repo.save(incident)
    
    # incidents table upsert
    mock_supabase_client.table.assert_any_call("incidents")
    # incident_evidence table upsert
    mock_supabase_client.table.assert_any_call("incident_evidence")

def test_get_incident_not_found(mock_supabase_client):
    # Setup mock to return empty list
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    repo = SupabaseIncidentRepository(mock_supabase_client)
    incident = repo.get("invalid_id")
    assert incident is None

def test_get_incident_found(mock_supabase_client):
    # Setup mock to return a valid row
    row = {
        "incident_id": "test_id",
        "hazard_type": "FLOOD",
        "status": "VERIFIED",
        "centroid_latitude": None,
        "centroid_longitude": None,
        "first_observed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # We have to mock the .eq().execute() response differently based on the table name.
    # We'll just let it return the same data format for simplicity, but mock the evidence to return a report.
    def mock_execute(*args, **kwargs):
        resp = mock.Mock()
        resp.data = [row]
        return resp
        
    mock_eq = mock.Mock()
    mock_eq.execute.side_effect = mock_execute
    
    mock_select = mock.Mock()
    mock_select.eq.return_value = mock_eq
    
    mock_supabase_client.table.return_value.select.return_value = mock_select
    
    # For evidence it will also return `row` but we'll manually patch the behavior if we need.
    # Actually, the repo parses `report_id` from the evidence row, so let's make `row` have `report_id` to avoid KeyError.
    row["report_id"] = "rep1"
    
    repo = SupabaseIncidentRepository(mock_supabase_client)
    incident = repo.get("test_id")
    
    assert incident is not None
    assert incident.incident_id == "test_id"
    assert incident.hazard_type == "FLOOD"
    assert incident.status == "VERIFIED"
    assert incident.report_ids == ["rep1"]

def test_get_all_incidents(mock_supabase_client):
    # Mock select().execute()
    row = {
        "incident_id": "test_id",
        "hazard_type": "FLOOD",
        "status": "VERIFIED",
        "centroid_latitude": None,
        "centroid_longitude": None,
        "first_observed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = [row]
    
    repo = SupabaseIncidentRepository(mock_supabase_client)
    incidents = repo.get_all()
    
    assert len(incidents) == 1
    assert incidents[0].incident_id == "test_id"
    assert incidents[0].hazard_type == "FLOOD"
