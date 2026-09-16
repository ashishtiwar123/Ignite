import pytest
from unittest import mock
from app.db.supabase_assessment_repository import SupabaseAssessmentRepository
from app.api.schemas.internal import AssessmentRecord
from datetime import datetime, timezone

@pytest.fixture
def mock_supabase_client():
    client = mock.Mock()
    # Mock chain for insert, limit, execute
    client.table.return_value.insert.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock.Mock(data=[])
    return client

def test_save_assessment(mock_supabase_client):
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessment = AssessmentRecord(
        incident_id="inc123",
        idempotency_key="test_run_1",
        severity_status="supported",
        severity={"level": "HIGH"},
        severity_model_version="severity_v2"
    )
    repo.save(assessment)
    mock_supabase_client.table.assert_any_call("assessments")
    assert mock_supabase_client.table().insert.called

def test_save_assessment_duplicate_ignored(mock_supabase_client):
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessment = AssessmentRecord(
        incident_id="inc123",
        idempotency_key="test_run_2"
    )
    # Simulate Postgres unique constraint violation
    mock_supabase_client.table().insert().execute.side_effect = Exception("duplicate key value violates unique constraint 'idx_assessments_idempotency'")
    
    # Should not raise
    repo.save(assessment)
    assert mock_supabase_client.table().insert.called

def test_save_assessment_no_idempotency_key(mock_supabase_client):
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessment = AssessmentRecord(
        incident_id="inc123",
        idempotency_key=None,
        severity_status="supported"
    )
    # Simulate normal insert with no idempotency constraint triggered
    mock_supabase_client.table().insert().execute.side_effect = None
    repo.save(assessment)
    assert mock_supabase_client.table().insert.called

def test_get_assessment_not_found(mock_supabase_client):
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessment = repo.get("invalid_id")
    assert assessment is None

def test_get_latest_assessment(mock_supabase_client):
    row = {
        "assessment_id": "test_id",
        "incident_id": "inc123",
        "idempotency_key": "test_run_1",
        "verification_status": "VERIFIED",
        "severity_status": "unsupported_hazard",
        "severity": None,
        "trajectory_status": "not_calculated",
        "trajectory": None,
        "priority_level": None,
        "priority_score": None,
        "severity_model_version": "severity_v2",
        "verification_policy_version": "Operational Verification Policy v1",
        "trajectory_policy_version": None,
        "needs_policy_version": None,
        "priority_policy_version": None,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    mock_limit = mock.Mock()
    mock_limit.execute.return_value = mock.Mock(data=[row])
    mock_order = mock.Mock()
    mock_order.limit.return_value = mock_limit
    mock_eq = mock.Mock()
    mock_eq.order.return_value = mock_order
    mock_select = mock.Mock()
    mock_select.eq.return_value = mock_eq
    mock_supabase_client.table.return_value.select.return_value = mock_select
    
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessment = repo.get_latest_for_incident("inc123")
    
    assert assessment is not None
    assert assessment.incident_id == "inc123"
    assert assessment.severity_status == "unsupported_hazard"
    assert assessment.severity is None

def test_get_all_assessments(mock_supabase_client):
    row = {
        "assessment_id": "test_id",
        "incident_id": "inc123",
        "verification_status": "VERIFIED",
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    mock_order = mock.Mock()
    mock_order.execute.return_value = mock.Mock(data=[row, row])
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value = mock_order
    
    repo = SupabaseAssessmentRepository(mock_supabase_client)
    assessments = repo.get_all_for_incident("inc123")
    
    assert len(assessments) == 2
    assert assessments[0].incident_id == "inc123"
