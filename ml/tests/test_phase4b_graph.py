import pytest
import json
import uuid
from ml.src.agents.graph import build_graph, GraphState
from ml.src.agents.state import AgentState
from ml.src.incident.schemas import Report, IncidentCandidate
from unittest.mock import patch

def test_genuine_provenance_preserved():
    app = build_graph()
    raw_gdacs = json.dumps({
        "source": "GDACS",
        "source_record_id": "EQ-12345",
        "location": "Japan",
        "hazard_type": "EQ"
    })
    
    # Mock Gemini to just return our inputs
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Japan",
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        initial_state = AgentState(run_id="run-prov", raw_reports=[raw_gdacs])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t1"}})
        state = result["state"]
        
        reports = state.structured_reports
        assert len(reports) == 1
        assert reports[0]["source"] == "GDACS"
        assert reports[0]["source_record_id"] == "EQ-12345"
        
        candidates = state.incident_candidates
        assert len(candidates) >= 1
        assert "GDACS" in candidates[0]["source_list"]

def test_manual_report_provenance():
    app = build_graph()
    raw = "User saw a fire in the forest"
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "WILDFIRE",
            "location": "Forest"
        }
        
        initial_state = AgentState(run_id=None, raw_reports=[raw])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": str(uuid.uuid4())}})
        state = result["state"]
        
        assert state.run_id is None # 16. absent run_id remains None
        
        reports = state.structured_reports
        assert reports[0]["source"] == "USER_REPORT"
        # source_record_id must be a UUID (internal entity), not None, since schema requires it
        assert isinstance(uuid.UUID(reports[0]["source_record_id"]), uuid.UUID)

def test_normalization_and_validation():
    app = build_graph()
    raw = json.dumps({"source": "TEST", "source_record_id": "1"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "HURRICANE", # should become Cyclone
            "location": "Florida"
        }
        
        initial_state = AgentState(raw_reports=[raw])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t"}})
        state = result["state"]
        
        assert state.structured_reports[0]["hazard_type"] == "Cyclone"

def test_deduplication():
    app = build_graph()
    raw1 = json.dumps({"source": "GDACS", "source_record_id": "1"})
    raw2 = json.dumps({"source": "GDACS", "source_record_id": "1"}) # Duplicate
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {"hazard_type": "Flood"}
        
        initial_state = AgentState(raw_reports=[raw1, raw2])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t"}})
        state = result["state"]
        
        # Deduplication should leave only 1
        assert len(state.structured_reports) == 1
        assert state.incident_candidates[0]["raw_report_count"] == 1

def test_multiple_candidates_first_selected():
    app = build_graph()
    raw1 = json.dumps({"source": "GDACS", "source_record_id": "1", "location": "Tokyo", "hazard_type": "Earthquake"})
    raw2 = json.dumps({"source": "GDACS", "source_record_id": "2", "location": "New York", "hazard_type": "Flood"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        # Mock extract needs to return different things for different inputs
        def side_effect(raw):
            d = json.loads(raw)
            return {"hazard_type": d["hazard_type"], "location": d["location"]}
        mock_extract.side_effect = side_effect
        
        initial_state = AgentState(raw_reports=[raw1, raw2])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t"}})
        state = result["state"]
        
        # Should cluster into 2 candidates because hazard_types differ
        assert len(state.incident_candidates) == 2
        
        # But verification_status of state is based on the first candidate
        # The first candidate has only 1 report, so it needs verification
        assert state.verification_status == "NEEDS_VERIFICATION"

def test_verification_uses_existing_engine():
    app = build_graph()
    raw1 = json.dumps({"source": "USGS", "source_record_id": "1"})
    raw2 = json.dumps({"source": "GDACS", "source_record_id": "2"})
    
    with patch("ml.src.agents.gemini_client.GeminiAdapter.extract_structured_report") as mock_extract:
        mock_extract.return_value = {
            "hazard_type": "Earthquake",
            "location": "Tokyo",
            "latitude": 35.6,
            "longitude": 139.6,
            "observed_at": "2026-09-17T00:00:00Z"
        }
        
        initial_state = AgentState(raw_reports=[raw1, raw2])
        result = app.invoke({"state": initial_state}, config={"configurable": {"thread_id": "t"}})
        state = result["state"]
        
        # 2 independent authoritative sources in the same cluster = VERIFIED
        assert state.verification_status == "VERIFIED"
        assert state.incident_candidates[0]["status"] == "VERIFIED"
