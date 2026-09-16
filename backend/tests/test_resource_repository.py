import pytest
from unittest import mock
from app.db.supabase_resource_repository import SupabaseResourceRepository
from app.api.schemas.internal import ResourceRecord

@pytest.fixture
def mock_supabase_client():
    client = mock.Mock()
    # Mock chain: client.table().upsert().execute()
    client.table.return_value.upsert.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.execute.return_value = mock.Mock(data=[])
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock.Mock(data=[])
    return client

def test_upsert_resource(mock_supabase_client):
    repo = SupabaseResourceRepository(mock_supabase_client)
    resource = ResourceRecord(
        location_id="loc1",
        resource_type="WATER",
        category="CONSUMABLES",
        quantity_available=1000.0,
        unit="liters"
    )
    repo.upsert(resource)
    mock_supabase_client.table().upsert.assert_called_once()
    
def test_get_all_resources(mock_supabase_client):
    row = {
        "resource_id": "res1",
        "location_id": "loc1",
        "resource_type": "WATER",
        "quantity_available": 1000.0,
        "unit": "liters",
        "updated_at": "2026-01-01T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z"
    }
    mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = [row]
    repo = SupabaseResourceRepository(mock_supabase_client)
    
    res = repo.get_all()
    assert len(res) == 1
    assert res[0].location_id == "loc1"

def test_get_resources_by_location(mock_supabase_client):
    row = {
        "resource_id": "res1",
        "location_id": "loc2",
        "resource_type": "WATER",
        "quantity_available": 1000.0,
        "unit": "liters",
        "updated_at": "2026-01-01T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z"
    }
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [row]
    repo = SupabaseResourceRepository(mock_supabase_client)
    
    res = repo.get_by_location("loc2")
    assert len(res) == 1
    assert res[0].location_id == "loc2"
