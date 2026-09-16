import pytest
from unittest.mock import Mock
from app.db.supabase_allocation_repository import SupabaseAllocationRepository
from app.db.allocation_repository import InMemoryAllocationRepository
from app.api.schemas.internal import AllocationRecord

def test_in_memory_save_and_get():
    repo = InMemoryAllocationRepository()
    alloc = AllocationRecord(
        optimization_run_id="run1",
        incident_id="inc1",
        source_location_id="loc1",
        resource_type="WATER",
        unit="liters",
        quantity_allocated=100.0,
        quantity_requested=100.0,
        quantity_unmet=0.0
    )
    
    repo.save_allocations([alloc])
    res = repo.get_by_incident("inc1")
    assert len(res) == 1
    assert res[0].quantity_allocated == 100.0

def test_in_memory_idempotency():
    repo = InMemoryAllocationRepository()
    alloc1 = AllocationRecord(
        optimization_run_id="run1",
        incident_id="inc1",
        source_location_id="loc1",
        resource_type="WATER",
        unit="liters",
        quantity_allocated=100.0,
        quantity_requested=100.0,
        quantity_unmet=0.0
    )
    
    repo.save_allocations([alloc1])
    
    # Try to save another batch with the same run_id
    alloc2 = AllocationRecord(
        optimization_run_id="run1",
        incident_id="inc1",
        source_location_id="loc2",
        resource_type="FOOD",
        unit="meals",
        quantity_allocated=50.0,
        quantity_requested=50.0,
        quantity_unmet=0.0
    )
    
    repo.save_allocations([alloc2])
    
    # Should only have the first one because of idempotency check on run_id
    res = repo.get_by_incident("inc1")
    assert len(res) == 1
    assert res[0].resource_type == "WATER"

def test_supabase_idempotency_check():
    mock_client = Mock()
    repo = SupabaseAllocationRepository(mock_client)
    
    alloc1 = AllocationRecord(
        optimization_run_id="run1",
        incident_id="inc1",
        source_location_id="loc1",
        resource_type="WATER",
        unit="liters",
        quantity_allocated=100.0,
        quantity_requested=100.0,
        quantity_unmet=0.0
    )
    
    # Simulate run1 already exists
    mock_client.table().select().eq().limit().execute.return_value.data = [{"allocation_id": "existing-id"}]
    
    repo.save_allocations([alloc1])
    
    # Insert should NOT have been called
    mock_client.table().insert.assert_not_called()

def test_in_memory_null_run_id_no_idempotency():
    repo = InMemoryAllocationRepository()
    alloc1 = AllocationRecord(
        optimization_run_id=None,
        incident_id="inc1",
        source_location_id="loc1",
        resource_type="WATER",
        unit="liters",
        quantity_allocated=100.0,
        quantity_requested=100.0,
        quantity_unmet=0.0
    )
    repo.save_allocations([alloc1])
    
    alloc2 = AllocationRecord(
        optimization_run_id=None,
        incident_id="inc1",
        source_location_id="loc2",
        resource_type="FOOD",
        unit="meals",
        quantity_allocated=50.0,
        quantity_requested=50.0,
        quantity_unmet=0.0
    )
    repo.save_allocations([alloc2])
    
    # Should have BOTH because None run_id means NO idempotency
    res = repo.get_by_incident("inc1")
    assert len(res) == 2

def test_supabase_null_run_id_no_idempotency():
    mock_client = Mock()
    repo = SupabaseAllocationRepository(mock_client)
    
    alloc1 = AllocationRecord(
        optimization_run_id=None,
        incident_id="inc1",
        source_location_id="loc1",
        resource_type="WATER",
        unit="liters",
        quantity_allocated=100.0,
        quantity_requested=100.0,
        quantity_unmet=0.0
    )
    
    repo.save_allocations([alloc1])
    
    # Select should NOT have been called because run_id is None
    mock_client.table().select.assert_not_called()
    # Insert SHOULD have been called
    mock_client.table().insert.assert_called_once()
