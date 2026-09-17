import pytest
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from ml.src.agents.state import AgentState
from ml.src.agents.graph import build_graph, situation_assessment_node
from unittest.mock import patch
from ml.src.models.severity_v2.predictor_v2 import SeverityPredictorV2

@pytest.fixture
def base_state():
    return {
        "run_id": "test-run-123",
        "verification_status": "VERIFIED",
        "incident_candidates": [{
            "incident_id": "INC-TEST",
            "hazard_type": "EARTHQUAKE",
            "status": "VERIFIED",
            "report_ids": ["rep1"],
            "canonical_attributes": {
                "magnitude": 7.5,
                "depth": 10.0,
                "country_population": 1000000.0,
                "population_density_sqkm": 50.0,
                "affected_population": 50000
            }
        }],
        "structured_reports": [{
            "report_id": "rep1",
            "source": "USGS",
            "source_record_id": "USGS-123",
            "hazard_type": "EARTHQUAKE",
            "magnitude": 7.5,
            "depth": 10.0,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "affected_population": 50000
        }]
    }

def test_verified_incident_enters_situation_assessment(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.assessment_status == "ASSESSMENT_COMPLETE"
    assert res.severity_score is not None

def test_needs_verification_bypasses(base_state):
    base_state["verification_status"] = "NEEDS_VERIFICATION"
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.assessment_status == "PENDING"

def test_rejected_bypasses(base_state):
    base_state["verification_status"] = "REJECTED"
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.assessment_status == "PENDING"

def test_severity_predictor_is_invoked(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.severity is not None
    assert res.severity["status"] == "success"
    assert "model_version" in res.severity
    assert res.severity_score == res.severity["severity_score"]

def test_unsupported_hazard(base_state):
    base_state["incident_candidates"][0]["hazard_type"] = "VOLCANO"
    base_state["structured_reports"][0]["hazard_type"] = "VOLCANO"
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    
    assert res.severity["status"] == "unsupported_hazard"
    assert res.severity_score is None
    # Assuming priority can handle missing severity
    assert res.assessment_status == "ASSESSMENT_COMPLETE"
    assert res.assessment_record["severity_status"] == "unsupported_hazard"

def test_trajectory_engine_invoked(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.trajectory_status == "CALCULATED"
    # Single report = INSUFFICIENT_EVIDENCE
    assert res.trajectory == "INSUFFICIENT_EVIDENCE"

def test_needs_engine_invoked(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.needs_status == "CALCULATED"
    assert len(res.needs) > 0
    # Check qualitative vs quantitative
    assert any(n["category"] == "WATER" and n["quantity"] is not None for n in res.needs)
    assert any(n["category"] == "MEDICAL" and n["quantity"] is None and n["urgency_category"] is not None for n in res.needs)
    assert res.needs[0]["rule_id"] is not None

def test_priority_engine_invoked(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.priority_status == "CALCULATED"
    assert res.priority is not None
    assert res.priority["priority_score"] >= 0
    assert res.priority["priority_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

def test_assessment_aggregation(base_state):
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    record = res.assessment_record
    assert record is not None
    assert record["verification_status"] == "VERIFIED"
    assert record["severity_status"] == "supported"
    assert record["idempotency_key"] == "test-run-123"
    assert record["severity_model_version"] is not None

def test_persistence_failure_semantics(base_state):
    state_obj = {"state": AgentState(**base_state)}
    with patch("app.services.assessment_service.AssessmentService.save_complete_assessment", side_effect=Exception("DB down")):
        res = situation_assessment_node(state_obj)["state"]
        assert res.assessment_status == "PERSISTENCE_FAILED: DB down"
        assert res.assessment_record is None

def test_missing_run_id_no_fallback(base_state):
    base_state["run_id"] = None
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.assessment_record["idempotency_key"] is None

def test_missing_affected_population_failure(base_state):
    # Needs should not fail but might return INSUFFICIENT_DATA status inside needs array
    base_state["incident_candidates"][0]["canonical_attributes"]["affected_population"] = None
    base_state["structured_reports"][0]["affected_population"] = None
    state_obj = {"state": AgentState(**base_state)}
    res = situation_assessment_node(state_obj)["state"]
    assert res.assessment_status == "ASSESSMENT_COMPLETE"
    assert any(n["status"] == "INSUFFICIENT_DATA" for n in res.needs)
