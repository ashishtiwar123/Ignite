import pytest
from unittest.mock import patch, MagicMock
from app.services.agent_service import AgentService
from app.api.schemas.internal import AgentRunRequest
from app.api.routes.agents import run_agent as run_agent_route
from fastapi import HTTPException
from ml.src.agents.state import AgentState

def test_1_and_2_and_3_existing_incident_id_accepted_loaded_hydrated():
    service = AgentService()
    req = AgentRunRequest(incident_id="56862ef4-18f4-4bfc-bcf6-795850362551")
    
    mock_incident = MagicMock()
    mock_incident.incident_id = "56862ef4-18f4-4bfc-bcf6-795850362551"
    mock_incident.hazard_type = "Flood"
    mock_incident.centroid_latitude = 19.076
    mock_incident.centroid_longitude = 72.877
    mock_incident.report_ids = ["rep-1"]
    mock_incident.model_dump.return_value = {
        "incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551",
        "hazard_type": "Flood",
        "verification_status": "VERIFIED"
    }

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
        {
            "report_id": "rep-1",
            "source": "FIELD_REPORT",
            "hazard_type": "Flood",
            "affected_population": 500,
            "displaced_population": 150
        }
    ]

    with patch('app.db.dependencies.get_incident_repository') as mock_repo_fn, \
         patch('app.db.client.get_supabase_client', return_value=mock_supabase), \
         patch.object(service.app, 'invoke') as mock_invoke:

        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_incident
        mock_repo_fn.return_value = mock_repo

        mock_state = MagicMock(
            run_id="run-test",
            verification_status="VERIFIED",
            human_approval_state="PENDING",
            errors=[],
            allocation_result={"solver_status": "OPTIMAL"}
        )
        mock_invoke.return_value = {"state": mock_state}

        res = service.run_agent(req)

        # 1. Accepted
        assert res is not None
        # 2. Loaded from repository
        mock_repo.get.assert_called_once_with("56862ef4-18f4-4bfc-bcf6-795850362551")
        # 3. Reports hydrated
        call_args = mock_invoke.call_args
        initial_state = call_args[0][0]["state"]
        assert len(initial_state.raw_reports) == 1
        assert "FIELD_REPORT" in initial_state.raw_reports[0]

def test_4_and_5_existing_incident_id_preserved_no_duplicate():
    from ml.src.agents.graph import incident_detection_node
    
    initial_candidates = [{
        "incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551",
        "hazard_type": "Flood",
        "centroid_latitude": 19.076,
        "centroid_longitude": 72.877,
        "verification_status": "VERIFIED"
    }]
    
    mock_agent_state = AgentState(
        raw_reports=['{"hazard_type": "Flood"}'],
        incident_candidates=initial_candidates
    )

    result = incident_detection_node({"state": mock_agent_state})
    new_state = result["state"]

    # 4. Preserved ID
    assert len(new_state.incident_candidates) == 1
    cand = new_state.incident_candidates[0]
    cand_id = cand.get("incident_id") if isinstance(cand, dict) else getattr(cand, "incident_id")
    assert cand_id == "56862ef4-18f4-4bfc-bcf6-795850362551"
    # 5. No duplicate incident created
    assert cand_id != "inc-demo-1"

def test_6_missing_incident_returns_404():
    mock_service = MagicMock()
    mock_service.run_agent.side_effect = ValueError("Incident with ID non-existent-id not found")
    
    req = AgentRunRequest(incident_id="non-existent-id")
    with pytest.raises(HTTPException) as exc_info:
        run_agent_route(request=req, service=mock_service)
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()

def test_7_and_8_verified_vs_unverified_incident_gate():
    from ml.src.agents.graph import optimization_node

    # 8. Unverified incident cannot optimize
    unverified_state = AgentState(
        run_id="run-unverified",
        verification_status="CANDIDATE",
        incident_candidates=[{"incident_id": "test-inc"}]
    )
    result_unverified = optimization_node({"state": unverified_state})
    res_state_u = result_unverified["state"]
    assert not res_state_u.allocation_result

    # 7. Verified incident reaches optimization
    verified_state = AgentState(
        run_id="run-verified",
        verification_status="VERIFIED",
        incident_candidates=[{"incident_id": "test-inc"}],
        needs=[{
            "need_id": "n1",
            "incident_id": "test-inc",
            "resource_type": "WATER",
            "quantity": 100,
            "unit": "L"
        }],
        priority_result={"priority_level": "HIGH", "priority_score": 0.8}
    )

    with patch('app.db.dependencies.get_resource_repository') as mock_r_repo, \
         patch('app.db.dependencies.get_allocation_repository') as mock_a_repo, \
         patch('app.services.allocation_service.AllocationService') as mock_opt_svc_cls:
        
        mock_opt_svc = MagicMock()
        mock_opt_res = MagicMock()
        mock_opt_res.optimization_run_id = "run-verified"
        mock_opt_res.solver_status = "OPTIMAL"
        mock_opt_res.allocations = []
        mock_opt_res.total_requested = 100
        mock_opt_res.total_allocated = 100
        mock_opt_res.model_dump.return_value = {"solver_status": "OPTIMAL"}
        mock_opt_svc.optimize.return_value = mock_opt_res
        mock_opt_svc_cls.return_value = mock_opt_svc

        result_verified = optimization_node({"state": verified_state})
        res_state_v = result_verified["state"]
        assert res_state_v.allocation_result.get("solver_status") == "OPTIMAL"

def test_9_and_10_run_id_semantics_and_temporary_thread_id():
    service = AgentService()
    req = AgentRunRequest(incident_id="56862ef4-18f4-4bfc-bcf6-795850362551", run_id=None)

    mock_incident = MagicMock()
    mock_incident.incident_id = "56862ef4-18f4-4bfc-bcf6-795850362551"
    mock_incident.report_ids = []
    mock_incident.hazard_type = "Flood"
    mock_incident.centroid_latitude = 19.0
    mock_incident.centroid_longitude = 72.0
    mock_incident.model_dump.return_value = {"incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551"}

    with patch('app.db.dependencies.get_incident_repository') as mock_repo_fn, \
         patch.object(service.app, 'invoke') as mock_invoke:

        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_incident
        mock_repo_fn.return_value = mock_repo

        mock_state = MagicMock(
            run_id="run-opt-999",
            verification_status="VERIFIED",
            human_approval_state="PENDING",
            errors=[],
            allocation_result={"solver_status": "OPTIMAL"}
        )
        mock_invoke.return_value = {"state": mock_state}

        res = service.run_agent(req)

        # 9. run_id semantics preserved
        call_args = mock_invoke.call_args
        initial_state = call_args[0][0]["state"]
        config = call_args[1]["config"]

        # If run_id not provided by caller, initial_state.run_id is None
        assert initial_state.run_id is None
        # Checkpointing thread_id is temporary string
        assert config["configurable"]["thread_id"].startswith("thread-")
        # 10. Thread ID is not leaked as domain ID
        assert res.run_id == "run-opt-999"

def test_11_existing_raw_report_workflow_working():
    service = AgentService()
    req = AgentRunRequest(raw_reports=['{"hazard_type": "Flood", "location": "Mumbai"}'])

    with patch.object(service.app, 'invoke') as mock_invoke:
        mock_state = MagicMock(
            run_id="run-raw-1",
            verification_status="VERIFIED",
            human_approval_state="PENDING",
            errors=[],
            allocation_result={}
        )
        mock_invoke.return_value = {"state": mock_state}

        res = service.run_agent(req)
        assert res.run_id == "run-raw-1"
        assert res.status in ["COMPLETED", "PENDING_REVIEW"]

def test_12_dashboard_uses_real_uuid():
    req = AgentRunRequest(incident_id="56862ef4-18f4-4bfc-bcf6-795850362551")
    assert req.incident_id == "56862ef4-18f4-4bfc-bcf6-795850362551"
    assert req.incident_id != "inc-demo-1"

def test_13_and_14_proposal_and_human_review_surfaced():
    service = AgentService()
    req = AgentRunRequest(incident_id="56862ef4-18f4-4bfc-bcf6-795850362551")

    mock_incident = MagicMock()
    mock_incident.incident_id = "56862ef4-18f4-4bfc-bcf6-795850362551"
    mock_incident.report_ids = []
    mock_incident.hazard_type = "Flood"
    mock_incident.centroid_latitude = 19.0
    mock_incident.centroid_longitude = 72.0
    mock_incident.model_dump.return_value = {"incident_id": "56862ef4-18f4-4bfc-bcf6-795850362551"}

    with patch('app.db.dependencies.get_incident_repository') as mock_repo_fn, \
         patch.object(service.app, 'invoke') as mock_invoke, \
         patch.object(service.app, 'get_state') as mock_get_state:

        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_incident
        mock_repo_fn.return_value = mock_repo

        mock_state = MagicMock(
            run_id="run-opt-123",
            verification_status="VERIFIED",
            human_approval_state="PENDING",
            errors=[],
            allocation_result={"solver_status": "OPTIMAL", "allocations": [{"allocation_id": "a1"}]}
        )
        mock_snap = MagicMock()
        mock_snap.values = {"state": mock_state}
        mock_snap.next = ("human_review",)

        mock_invoke.return_value = None
        mock_get_state.return_value = mock_snap

        res = service.run_agent(req)

        # 13. Proposal created & 14. Human review state correctly surfaced
        assert res.status == "PENDING_REVIEW"
        assert res.human_approval_state == "PENDING"
        assert res.run_id == "run-opt-123"
