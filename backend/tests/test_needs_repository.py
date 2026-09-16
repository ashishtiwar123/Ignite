import pytest
from unittest import mock
from app.db.supabase_needs_repository import SupabaseNeedsRepository
from app.api.schemas.internal import NeedRecord

@pytest.fixture
def mock_supabase_client():
    client = mock.Mock()
    # Mock chain: client.table().insert().execute()
    client.table.return_value.insert.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock.Mock(data=[])
    return client

def test_save_needs(mock_supabase_client):
    repo = SupabaseNeedsRepository(mock_supabase_client)
    # Simulate empty check for idempotency
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    
    needs = [
        NeedRecord(
            incident_id="inc1",
            assessment_id="ass1",
            resource_type="WATER",
            quantity=100.0,
            unit="liters",
            urgency="HIGH"
        )
    ]
    repo.save_all(needs)
    assert mock_supabase_client.table().insert.called

def test_save_needs_idempotent_duplicate_ignored(mock_supabase_client):
    repo = SupabaseNeedsRepository(mock_supabase_client)
    # Simulate existing needs for assessment
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"need_id": "test"}]
    
    needs = [
        NeedRecord(
            incident_id="inc1",
            assessment_id="ass1",
            resource_type="WATER"
        )
    ]
    repo.save_all(needs)
    # Insert should NOT be called because they exist
    assert not mock_supabase_client.table().insert.called

def test_get_by_incident(mock_supabase_client):
    row = {
        "need_id": "n1",
        "incident_id": "inc1",
        "resource_type": "WATER",
        "quantity": None, # Testing nullable quantity
        "unit": None,
        "created_at": "2026-01-01T00:00:00Z"
    }
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [row]
    repo = SupabaseNeedsRepository(mock_supabase_client)
    
    res = repo.get_by_incident("inc1")
    assert len(res) == 1
    assert res[0].quantity is None
