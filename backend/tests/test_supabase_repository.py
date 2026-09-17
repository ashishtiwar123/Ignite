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


def test_supabase_assessment_repository(mock_supabase_client):
    from app.db.supabase_assessment_repository import SupabaseAssessmentRepository
    from app.api.schemas.internal import AssessmentRecord

    repo = SupabaseAssessmentRepository(mock_supabase_client)
    rec = AssessmentRecord(
        assessment_id="ass-1",
        incident_id="inc-1",
        idempotency_key="hash-123",
        verification_status="VERIFIED",
        severity_status="CALCULATED",
        severity={"status": "CALCULATED", "score": 7.5},
        assessed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    repo.save(rec)
    mock_supabase_client.table.assert_any_call("assessments")
    assert mock_supabase_client.table().insert.called


def test_supabase_needs_repository(mock_supabase_client):
    from app.db.supabase_needs_repository import SupabaseNeedsRepository
    from app.api.schemas.internal import NeedRecord

    repo = SupabaseNeedsRepository(mock_supabase_client)
    need = NeedRecord(
        need_id="need-1",
        incident_id="inc-1",
        assessment_id="ass-1",
        resource_type="Potable Water",
        category="WATER",
        quantity=5000.0,
        unit="Liters",
        created_at=datetime.now(timezone.utc)
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    repo.save_all([need])
    mock_supabase_client.table.assert_any_call("needs")


def test_supabase_resource_repository(mock_supabase_client):
    from app.db.supabase_resource_repository import SupabaseResourceRepository
    from app.api.schemas.internal import ResourceRecord

    repo = SupabaseResourceRepository(mock_supabase_client)
    res = ResourceRecord(
        resource_id="res-1",
        location_id="LOC-1",
        resource_type="Potable Water",
        category="WATER",
        quantity_available=10000.0,
        unit="Liters",
        updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    repo.upsert(res)
    mock_supabase_client.table.assert_any_call("resources")
    assert mock_supabase_client.table().upsert.called


def test_supabase_allocation_repository(mock_supabase_client):
    from app.db.supabase_allocation_repository import SupabaseAllocationRepository
    from app.api.schemas.internal import AllocationRecord

    repo = SupabaseAllocationRepository(mock_supabase_client)
    alloc = AllocationRecord(
        allocation_id="alloc-1",
        optimization_run_id="run-1",
        incident_id="inc-1",
        source_location_id="LOC-1",
        resource_type="Potable Water",
        unit="Liters",
        quantity_allocated=5000.0,
        quantity_requested=5000.0,
        quantity_unmet=0.0,
        created_at=datetime.now(timezone.utc)
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    repo.save_allocations([alloc])
    mock_supabase_client.table.assert_any_call("allocations")


def test_supabase_approval_repository(mock_supabase_client):
    from app.db.supabase_approval_repository import SupabaseApprovalRepository
    from app.api.schemas.internal import ApprovalRecord

    repo = SupabaseApprovalRepository(mock_supabase_client)
    appr = ApprovalRecord(
        approval_id="appr-1",
        incident_id="inc-1",
        optimization_run_id="run-1",
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase_client.table.return_value.upsert.return_value.execute.return_value.data = [appr.model_dump()]
    res = repo.upsert(appr)
    mock_supabase_client.table.assert_any_call("approvals")
    assert res.approval_id == "appr-1"


def test_supabase_action_repository(mock_supabase_client):
    from app.db.supabase_action_repository import SupabaseActionRepository
    from app.api.schemas.internal import ActionRecord

    repo = SupabaseActionRepository(mock_supabase_client)
    act = ActionRecord(
        action_id="act-1",
        incident_id="inc-1",
        optimization_run_id="run-1",
        action_type="RESOURCE_ALLOCATION_EXECUTION",
        status="EXECUTED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_supabase_client.table.return_value.upsert.return_value.execute.return_value.data = [act.model_dump()]
    res = repo.save(act)
    mock_supabase_client.table.assert_any_call("actions")
    assert res.action_id == "act-1"


def test_supabase_dependency_selection_and_fail_loud():
    from app.db.dependencies import (
        get_incident_repository,
        get_assessment_repository,
        get_needs_repository,
        get_resource_repository,
        get_allocation_repository,
        get_approval_repository,
        get_action_repository
    )
    from app.db.supabase_repository import SupabaseIncidentRepository

    mock_client = mock.Mock()

    # When client is provided and backend is supabase -> Supabase repos returned
    mock_settings_obj = mock.Mock()
    mock_settings_obj.PERSISTENCE_BACKEND = "supabase"
    with mock.patch("app.db.dependencies.get_settings", return_value=mock_settings_obj):
        with mock.patch("app.db.client.get_supabase_client", return_value=mock_client):
            assert isinstance(get_incident_repository(), SupabaseIncidentRepository)

        # When client is None and backend is supabase -> Loud failure, no fallback
        with mock.patch("app.db.client.get_supabase_client", return_value=None):
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_incident_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_assessment_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_needs_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_resource_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_allocation_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_approval_repository()
            with pytest.raises(RuntimeError, match="Supabase configuration is invalid or missing."):
                get_action_repository()

