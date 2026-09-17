import pytest
import json
from datetime import datetime, timezone
import sys
import os

# Ensure backend is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from ml.src.agents.state import AgentState
from ml.src.agents.graph import build_graph, optimization_node
from unittest.mock import patch
from app.db.dependencies import (
    get_allocation_repository,
    get_needs_repository,
    get_resource_repository,
    get_assessment_repository
)
from app.api.schemas.internal import ResourceRecord
import uuid

@pytest.fixture(autouse=True)
def setup_repositories():
    # Clear and seed repositories
    resource_repo = get_resource_repository()
    # Assume it's in-memory, we can clear it if it has a _storage dict, or just add uniquely
    if hasattr(resource_repo, '_storage'):
        resource_repo._storage.clear()
        
    # Seed 1000 liters of water
    resource_repo.upsert(ResourceRecord(
        location_id="warehouse-alpha",
        resource_type="Water",
        category="WATER",
        quantity_available=1000.0,
        unit="Liters"
    ))
    # Seed 50 tarps
    resource_repo.upsert(ResourceRecord(
        location_id="warehouse-beta",
        resource_type="Tarpaulin",
        category="SHELTER",
        quantity_available=50.0,
        unit="Units"
    ))
    
    # We shouldn't need to clear other repos since they are populated by the graph logic per test
    yield
    
    if hasattr(resource_repo, '_storage'):
        resource_repo._storage.clear()

def test_optimization_rejected_bypassed():
    app = build_graph()
    
    # Send a prompt injection to get rejected
    raw1 = json.dumps({"source": "USGS", "source_record_id": "1", "hazard_type": "PROMPT_INJECTION_DETECTED"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "PROMPT_INJECTION_DETECTED"
        }
        
        initial_state = AgentState(raw_reports=[raw1])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t1"}})
        
        state = result["state"]
        
        # Verification should be REJECTED
        assert state.verification_status == "REJECTED"
        
        # Optimization should not have run
        assert state.allocation_result is None

def test_optimization_needs_verification_bypassed():
    app = build_graph()
    
    raw1 = json.dumps({"source": "TWITTER", "source_record_id": "1", "hazard_type": "Flood"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Flood",
            "location": "Unknown",
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        with patch("ml.src.agents.graph.assess_incident") as mock_verify:
            # Mock verification so it needs verification
            from ml.src.incident.verification import VerificationAssessment
            mock_verify.return_value = VerificationAssessment(incident_candidate_id="dummy", verification_status="NEEDS_VERIFICATION", confidence_score=0.4)
            
            initial_state = AgentState(raw_reports=[raw1])
            result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t1_needs_ver"}})
            
            state = result["state"]
            
            # Verification should be NEEDS_VERIFICATION
            assert state.verification_status == "NEEDS_VERIFICATION"
            
            # Optimization should not have run
            assert state.allocation_result is None

def test_optimization_runs_for_verified_incident():
    app = build_graph()
    
    raw1 = json.dumps({"source": "USGS", "source_record_id": "123", "hazard_type": "Earthquake"})
    run_id = str(uuid.uuid4())
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Tokyo",
            "latitude": 35.6,
            "longitude": 139.6,
            "magnitude": 7.5,
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        with patch("ml.src.agents.graph.assess_incident") as mock_verify:
            # Mock verification so it passes
            from ml.src.incident.verification import VerificationAssessment
            mock_verify.return_value = VerificationAssessment(incident_candidate_id="dummy", verification_status="VERIFIED", confidence_score=0.9)
            
            with patch("ml.src.models.severity_v2.predictor_v2.SeverityPredictorV2.predict_severity") as mock_severity:
                mock_severity.return_value = {"status": "success", "severity_score": 8.0, "severity_class": "EXTREME", "model_version": "v2"}
                
                with patch("ml.src.agents.graph.assess_trajectory") as mock_traj:
                    from ml.src.risk.trajectory_schemas import TrajectoryAssessment
                    mock_traj.return_value = TrajectoryAssessment(incident_candidate_id="dummy", trajectory="RAPIDLY_WORSENING", confidence=0.9, policy_version="v1")
                    
                    with patch("ml.src.agents.graph.assess_needs") as mock_needs:
                        from ml.src.needs.schemas import ResourceRequirement
                        mock_needs.return_value = [
                            ResourceRequirement(verified_incident_id="dummy", resource_type="Water", category="WATER", quantity=1500.0, unit="Liters", urgency="HIGH", status="CALCULATED", rule_id="r1", explanation="test"),
                            ResourceRequirement(verified_incident_id="dummy", resource_type="Tarpaulin", category="SHELTER", quantity=20.0, unit="Units", urgency="HIGH", status="CALCULATED", rule_id="r2", explanation="test"),
                        ]
                        
                        initial_state = AgentState(raw_reports=[raw1], run_id=run_id)
                        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t2"}})
                        
                        state = result["state"]
                        
                        # Verification should be VERIFIED
                        assert state.verification_status == "VERIFIED"
                        
                        # Optimization must have run
                        assert state.allocation_result is not None
                        alloc_res = state.allocation_result
                        
                        # Check run_id mapping
                        assert alloc_res.get("optimization_run_id") == run_id
                        
                        allocations = alloc_res.get("allocations", [])
                        
                        # Water request: 1500. Inventory: 1000. -> allocated: 1000, unmet: 500
                        water_alloc = next((a for a in allocations if a.get("resource_type") == "Water"), None)
                        assert water_alloc is not None
                        assert water_alloc["quantity_requested"] == 1500.0
                        assert water_alloc["quantity_allocated"] == 1000.0
                        assert water_alloc["quantity_unmet"] == 500.0
                        
                        tarp_alloc = next((a for a in allocations if a.get("resource_type") == "Tarpaulin"), None)
                        assert tarp_alloc is not None
                        assert tarp_alloc["quantity_allocated"] == 20.0
                        assert tarp_alloc["quantity_unmet"] == 0.0

                        # Ensure inventory was not mutated
                        resource_repo = get_resource_repository()
                        water_inv = next((r for r in resource_repo.get_all() if r.resource_type == "Water"), None)
                        assert water_inv.quantity_available == 1000.0

def test_missing_run_id_propagates_none():
    app = build_graph()
    
    raw1 = json.dumps({"source": "USGS", "source_record_id": "123", "hazard_type": "Earthquake"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Tokyo",
            "latitude": 35.6,
            "longitude": 139.6,
            "magnitude": 7.5,
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        with patch("ml.src.agents.graph.assess_incident") as mock_verify:
            from ml.src.incident.verification import VerificationAssessment
            mock_verify.return_value = VerificationAssessment(incident_candidate_id="dummy", verification_status="VERIFIED", confidence_score=0.9)
            
            with patch("ml.src.models.severity_v2.predictor_v2.SeverityPredictorV2.predict_severity") as mock_severity:
                mock_severity.return_value = {"status": "success", "severity_score": 8.0, "severity_class": "EXTREME", "model_version": "v2"}
                
                with patch("ml.src.agents.graph.assess_trajectory") as mock_traj:
                    from ml.src.risk.trajectory_schemas import TrajectoryAssessment
                    mock_traj.return_value = TrajectoryAssessment(incident_candidate_id="dummy", trajectory="RAPIDLY_WORSENING", confidence=0.9, policy_version="v1")
                    
                    with patch("ml.src.agents.graph.assess_needs") as mock_needs:
                        from ml.src.needs.schemas import ResourceRequirement
                        mock_needs.return_value = [
                            ResourceRequirement(verified_incident_id="dummy", resource_type="Tarpaulin", category="SHELTER", quantity=20.0, unit="Units", urgency="HIGH", status="CALCULATED", rule_id="r1", explanation="test"),
                        ]
                        
                        # run_id = None
                        initial_state = AgentState(raw_reports=[raw1], run_id=None)
                        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t3"}})
                        
                        state = result["state"]
                        
                        # Verification should be VERIFIED
                        assert state.verification_status == "VERIFIED"
                        
                        # Optimization must have run
                        assert state.allocation_result is not None
                        alloc_res = state.allocation_result
                        
                        # run_id must be None!
                        assert alloc_res.get("optimization_run_id") is None

def test_optimization_empty_inventory():
    # Re-setup without inventory
    resource_repo = get_resource_repository()
    if hasattr(resource_repo, '_resources'):
        resource_repo._resources.clear()
        
    app = build_graph()
    
    raw1 = json.dumps({"source": "USGS", "source_record_id": "123", "hazard_type": "Earthquake"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Tokyo",
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        with patch("ml.src.agents.graph.assess_incident") as mock_verify:
            from ml.src.incident.verification import VerificationAssessment
            mock_verify.return_value = VerificationAssessment(incident_candidate_id="dummy", verification_status="VERIFIED", confidence_score=0.9)
            
            with patch("ml.src.models.severity_v2.predictor_v2.SeverityPredictorV2.predict_severity") as mock_severity:
                mock_severity.return_value = {"status": "success", "severity_score": 8.0, "severity_class": "EXTREME", "model_version": "v2"}
                
                with patch("ml.src.agents.graph.assess_trajectory") as mock_traj:
                    from ml.src.risk.trajectory_schemas import TrajectoryAssessment
                    mock_traj.return_value = TrajectoryAssessment(incident_candidate_id="dummy", trajectory="RAPIDLY_WORSENING", confidence=0.9, policy_version="v1")
                    
                    with patch("ml.src.agents.graph.assess_needs") as mock_needs:
                        from ml.src.needs.schemas import ResourceRequirement
                        mock_needs.return_value = [
                            ResourceRequirement(verified_incident_id="dummy", resource_type="Water", category="WATER", quantity=1500.0, unit="Liters", urgency="HIGH", status="CALCULATED", rule_id="r1", explanation="test"),
                        ]
                        
                        initial_state = AgentState(raw_reports=[raw1], run_id=None)
                        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t4"}})
                        
                        state = result["state"]
                        
                        assert state.allocation_result is not None
                        allocations = state.allocation_result.get("allocations", [])
                        
                        water_alloc = next((a for a in allocations if a.get("resource_type") == "Water"), None)
                        assert water_alloc is not None
                        assert water_alloc["quantity_requested"] == 1500.0
                        assert water_alloc["quantity_allocated"] == 0.0
                        assert water_alloc["quantity_unmet"] == 1500.0

def test_qualitative_needs_excluded_from_optimization():
    app = build_graph()
    
    raw1 = json.dumps({"source": "USGS", "source_record_id": "123", "hazard_type": "Earthquake"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Tokyo",
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        with patch("ml.src.agents.graph.assess_incident") as mock_verify:
            from ml.src.incident.verification import VerificationAssessment
            mock_verify.return_value = VerificationAssessment(incident_candidate_id="dummy", verification_status="VERIFIED", confidence_score=0.9)
            
            with patch("ml.src.models.severity_v2.predictor_v2.SeverityPredictorV2.predict_severity") as mock_severity:
                mock_severity.return_value = {"status": "success", "severity_score": 8.0, "severity_class": "EXTREME", "model_version": "v2"}
                
                with patch("ml.src.agents.graph.assess_trajectory") as mock_traj:
                    from ml.src.risk.trajectory_schemas import TrajectoryAssessment
                    mock_traj.return_value = TrajectoryAssessment(incident_candidate_id="dummy", trajectory="RAPIDLY_WORSENING", confidence=0.9, policy_version="v1")
                    
                    with patch("ml.src.agents.graph.assess_needs") as mock_needs:
                        from ml.src.needs.schemas import ResourceRequirement
                        mock_needs.return_value = [
                            ResourceRequirement(verified_incident_id="dummy", resource_type="Helicopter", category="EVACUATION", quantity=None, unit="Unknown", urgency="HIGH", status="CALCULATED", rule_id="r1", explanation="test qualitative"),
                        ]
                        
                        initial_state = AgentState(raw_reports=[raw1], run_id=None)
                        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t5"}})
                        
                        state = result["state"]
                        
                        assert state.allocation_result is not None
                        allocations = state.allocation_result.get("allocations", [])
                        
                        # Helicopter qualitative need should not produce an allocation record since its quantity is None
                        heli_alloc = next((a for a in allocations if a.get("resource_type") == "Helicopter"), None)
                        assert heli_alloc is None

