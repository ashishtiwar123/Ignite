import pytest
from app.services.allocation_service import AllocationService
from app.api.schemas.internal import OptimizationRequest
from app.db.allocation_repository import InMemoryAllocationRepository
from app.db.needs_repository import InMemoryNeedsRepository
from app.db.resource_repository import InMemoryResourceRepository
from app.db.assessment_repository import InMemoryAssessmentRepository
from app.api.schemas.internal import NeedRecord, ResourceRecord

def test_optimization_service_workflow():
    alloc_repo = InMemoryAllocationRepository()
    needs_repo = InMemoryNeedsRepository()
    res_repo = InMemoryResourceRepository()
    assess_repo = InMemoryAssessmentRepository()
    
    # 1. Setup mocks
    # Need
    n1 = NeedRecord(
        incident_id="inc1",
        resource_type="WATER",
        quantity=100.0,
        unit="liters",
        status="CALCULATED"
    )
    needs_repo.save_all([n1])
    
    # Resource
    r1 = ResourceRecord(
        location_id="warehouse1",
        resource_type="WATER",
        quantity_available=150.0,
        unit="liters"
    )
    res_repo.upsert(r1)
    
    # Qualitative Need (should be skipped by numeric optimization but mapped correctly)
    n2 = NeedRecord(
        incident_id="inc1",
        resource_type="MEDICAL",
        quantity=None, # Qualitative
        unit=None,
        status="CALCULATED"
    )
    needs_repo.save_all([n2])
    
    service = AllocationService(alloc_repo, needs_repo, res_repo, assess_repo)
    
    req = OptimizationRequest(incident_ids=["inc1"])
    response = service.optimize(req)
    
    assert response.solver_status == "OPTIMAL"
    assert response.total_requested == 100.0
    assert response.total_allocated == 100.0
    assert response.total_unmet == 0.0
    
    # Only the WATER need should be mapped in allocations
    assert len(response.allocations) == 1
    alloc = response.allocations[0]
    assert alloc.resource_type == "WATER"
    assert alloc.quantity_allocated == 100.0
    assert alloc.quantity_unmet == 0.0
    
    # Check persistence
    saved = alloc_repo.get_by_incident("inc1")
    assert len(saved) == 1

def test_unmet_demand():
    alloc_repo = InMemoryAllocationRepository()
    needs_repo = InMemoryNeedsRepository()
    res_repo = InMemoryResourceRepository()
    assess_repo = InMemoryAssessmentRepository()
    
    n1 = NeedRecord(
        incident_id="inc1",
        resource_type="WATER",
        quantity=200.0, # Need 200
        unit="liters",
        status="CALCULATED"
    )
    needs_repo.save_all([n1])
    
    r1 = ResourceRecord(
        location_id="warehouse1",
        resource_type="WATER",
        quantity_available=50.0, # Only 50 available
        unit="liters"
    )
    res_repo.upsert(r1)
    
    service = AllocationService(alloc_repo, needs_repo, res_repo, assess_repo)
    req = OptimizationRequest(incident_ids=["inc1"])
    response = service.optimize(req)
    
    assert response.total_allocated == 50.0
    assert response.total_unmet == 150.0
    
    # The solver produces 1 allocation with quantity_unmet = 150.0
    assert len(response.allocations) == 1
    
    alloc = response.allocations[0]
    assert alloc.quantity_allocated == 50.0
    assert alloc.quantity_unmet == 150.0

def test_null_run_id_is_preserved():
    alloc_repo = InMemoryAllocationRepository()
    needs_repo = InMemoryNeedsRepository()
    res_repo = InMemoryResourceRepository()
    assess_repo = InMemoryAssessmentRepository()
    
    service = AllocationService(alloc_repo, needs_repo, res_repo, assess_repo)
    req = OptimizationRequest(incident_ids=["inc1"]) # optimization_run_id defaults to None
    response = service.optimize(req)
    
    assert response.optimization_run_id is None
    # No fallback UUID generated
    
    saved = alloc_repo.get_by_incident("inc1")
    if saved:
        assert saved[0].optimization_run_id is None

def test_explicit_run_id_is_preserved():
    alloc_repo = InMemoryAllocationRepository()
    needs_repo = InMemoryNeedsRepository()
    res_repo = InMemoryResourceRepository()
    assess_repo = InMemoryAssessmentRepository()
    
    service = AllocationService(alloc_repo, needs_repo, res_repo, assess_repo)
    req = OptimizationRequest(incident_ids=["inc1"], optimization_run_id="custom-run-123")
    response = service.optimize(req)
    
    assert response.optimization_run_id == "custom-run-123"
