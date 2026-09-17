import json
from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import schemas and engines
from ml.src.agents.state import AgentState
from ml.src.agents.gemini_client import GeminiAdapter

from ml.src.optimization.schemas import AllocationContext, ResourceInventory
from ml.src.needs.schemas import ResourceRequirement, NeedsAssessmentInput
from ml.src.needs.engine import assess_needs
from ml.src.priority.schemas import PriorityAssessment, PriorityEngineInput
from ml.src.priority.engine import assess_priority
from ml.src.optimization.engine import optimize_allocation
from ml.src.models.severity_v2.predictor_v2 import SeverityPredictorV2
from ml.src.risk.trajectory_schemas import RiskObservation
from ml.src.risk.trajectory import assess_trajectory

# Initialize clients
gemini_client = GeminiAdapter()
severity_predictor = SeverityPredictorV2()

# Define the State graph dictionary
class GraphState(TypedDict):
    state: AgentState

import uuid
from datetime import datetime, timezone
from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.normalization import normalize_hazard_type, normalize_timestamp
from ml.src.incident.validation import validate_report_fields
from ml.src.incident.deduplication import deduplicate_reports
from ml.src.incident.clustering import cluster_reports
from ml.src.incident.verification import assess_incident

def report_intelligence_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    structured_reports = []
    
    for raw in state.raw_reports:
        res = gemini_client.extract_structured_report(raw)
        if res:
            if "error" in res:
                state.errors.append(res["error"])
                continue
                
            source = "USER_REPORT"
            source_record_id = str(uuid.uuid4())
            parsed_raw = {}
            try:
                val = json.loads(raw)
                if isinstance(val, dict):
                    parsed_raw = val
                    if "source" in parsed_raw:
                        source = parsed_raw["source"]
                    if "source_record_id" in parsed_raw:
                        source_record_id = parsed_raw["source_record_id"]
            except Exception:
                pass

            hazard_raw = parsed_raw.get("hazard_type") or res.get("hazard_type", "UNKNOWN")
            if hazard_raw == "PROMPT_INJECTION_DETECTED":
                hazard = hazard_raw
            else:
                hazard = normalize_hazard_type(hazard_raw)

            report_dict = {
                "source": source,
                "source_record_id": source_record_id,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "hazard_type": hazard,
                "location_name": parsed_raw.get("location") or res.get("location"),
                "latitude": parsed_raw.get("latitude") if parsed_raw.get("latitude") is not None else res.get("latitude"),
                "longitude": parsed_raw.get("longitude") if parsed_raw.get("longitude") is not None else res.get("longitude"),
                "magnitude": parsed_raw.get("magnitude") if parsed_raw.get("magnitude") is not None else res.get("magnitude"),
                "wind_speed": parsed_raw.get("wind_speed") if parsed_raw.get("wind_speed") is not None else res.get("wind_speed"),
                "pressure": parsed_raw.get("pressure") if parsed_raw.get("pressure") is not None else res.get("pressure"),
                "depth": parsed_raw.get("depth") if parsed_raw.get("depth") is not None else res.get("depth"),
                "affected_population": parsed_raw.get("affected_population") if parsed_raw.get("affected_population") is not None else res.get("affected_population"),
                "displaced_population": parsed_raw.get("displaced_population") if parsed_raw.get("displaced_population") is not None else res.get("displaced_population"),
                "observed_at": parsed_raw.get("observed_at") or res.get("observed_at"),
                "raw_text": raw,
                "raw_payload_reference": res
            }
            structured_reports.append(report_dict)
            
    state.structured_reports = structured_reports
    return {"state": state}

def incident_detection_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if not state.structured_reports:
        state.errors.append("No structured reports extracted.")
        return {"state": state}
        
    reports = []
    for r_dict in state.structured_reports:
        validated_dict, errs = validate_report_fields(r_dict.copy())
        if errs:
            state.errors.extend([f"Validation error: {e['message']}" for e in errs])
        
        if "ingested_at" in validated_dict and isinstance(validated_dict["ingested_at"], str):
            validated_dict["ingested_at"] = normalize_timestamp(validated_dict["ingested_at"]) or datetime.now(timezone.utc)
        if "observed_at" in validated_dict and isinstance(validated_dict["observed_at"], str):
            validated_dict["observed_at"] = normalize_timestamp(validated_dict["observed_at"])
            
        reports.append(Report(**validated_dict))
        
    deduped_reports = deduplicate_reports(reports)
    
    try:
        import sys, os
        backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from app.db.dependencies import get_incident_repository
        inc_repo = get_incident_repository()
        for r in deduped_reports:
            inc_repo.save_report(r)
    except Exception as e:
        state.errors.append(f"Persistence error saving report: {e}")

    # CORRECTION 10: Associate new evidence with existing incident during reassessment
    candidates = cluster_reports(deduped_reports)
    if state.reassessment_requested and state.incident_candidates and candidates:
        existing_cand = state.incident_candidates[0]
        existing_inc_id = existing_cand.get("incident_id") if isinstance(existing_cand, dict) else getattr(existing_cand, "incident_id", None)
        if existing_inc_id:
            candidates[0].incident_id = existing_inc_id
        if candidates[0].centroid_latitude is None:
            existing_lat = existing_cand.get("centroid_latitude") if isinstance(existing_cand, dict) else getattr(existing_cand, "centroid_latitude", None)
            existing_lon = existing_cand.get("centroid_longitude") if isinstance(existing_cand, dict) else getattr(existing_cand, "centroid_longitude", None)
            if existing_lat is not None and existing_lon is not None:
                candidates[0].centroid_latitude = existing_lat
                candidates[0].centroid_longitude = existing_lon
                candidates[0].location_precision = "POINT"
    state.incident_candidates = [c.model_dump() for c in candidates]
        
    state.structured_reports = [r.model_dump() for r in deduped_reports]
    return {"state": state}

def verification_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if not state.incident_candidates:
        state.verification_status = "REJECTED"
        return {"state": state}
        
    cand_dict = state.incident_candidates[0]
    candidate = IncidentCandidate(**cand_dict)
    
    # Preserve graph-level prompt injection rejection
    if candidate.hazard_type == "PROMPT_INJECTION_DETECTED":
        state.verification_status = "REJECTED"
        cand_dict["status"] = "REJECTED"
        state.incident_candidates[0] = cand_dict
        return {"state": state}
    
    reports = [Report(**r) for r in state.structured_reports if r["report_id"] in candidate.report_ids]
    
    if not reports:
        state.verification_status = "REJECTED"
        return {"state": state}
        
    assessment = assess_incident(candidate, reports)
    
    state.verification_status = assessment.verification_status
    cand_dict["status"] = assessment.verification_status
    state.incident_candidates[0] = cand_dict

    try:
        import sys, os
        backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from app.db.dependencies import get_incident_repository
        candidate.status = assessment.verification_status
        get_incident_repository().save(candidate)
    except Exception as e:
        state.errors.append(f"Persistence error saving candidate: {e}")
    
    return {"state": state}

def situation_assessment_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if state.verification_status != "VERIFIED":
        return {"state": state}
        
    cand_dict = state.incident_candidates[0]
    candidate = IncidentCandidate(**cand_dict)
    reports = [Report(**r) for r in state.structured_reports if r["report_id"] in candidate.report_ids]
    
    canonical = candidate.canonical_attributes
    primary_report = reports[0] if reports else None
    
    # 2C - Severity
    event_features = {
        "disaster_type": candidate.hazard_type,
        "incident_id": candidate.incident_id,
        "country": getattr(primary_report, "country", None) if primary_report else None,
        "predictor_features_x": {
            "seismic_magnitude": canonical.get("magnitude") or (getattr(primary_report, "magnitude", None) if primary_report else None),
            "seismic_depth_km": canonical.get("depth") or (getattr(primary_report, "depth", None) if primary_report else None),
            "cyclone_max_wind_knots": canonical.get("wind_speed") or (getattr(primary_report, "wind_speed", None) if primary_report else None),
            "cyclone_min_pressure_mb": canonical.get("pressure") or (getattr(primary_report, "pressure", None) if primary_report else None),
            "country_population": canonical.get("country_population"),
            "population_density_sqkm": canonical.get("population_density_sqkm")
        }
    }
    
    severity_res = severity_predictor.predict_severity(event_features)
    state.severity = severity_res
    if severity_res.get("status") == "success":
        state.severity_score = severity_res.get("severity_score")
        severity_val = state.severity_score
        severity_model_version = severity_res.get("model_version")
        severity_status = "supported"
    else:
        state.severity_score = None
        severity_val = None
        severity_model_version = severity_res.get("model_version")
        severity_status = severity_res.get("status", "unsupported_hazard")
        
    # 2F - Trajectory
    observations = []
    for r in reports:
        obs = RiskObservation(
            incident_candidate_id=candidate.incident_id,
            observed_at=r.observed_at or r.ingested_at,
            hazard_type=r.hazard_type,
            source=r.source,
            source_record_id=r.source_record_id
        )
        if r.magnitude is not None: obs.intensity_features["seismic_magnitude"] = r.magnitude
        if r.wind_speed is not None: obs.intensity_features["cyclone_max_wind_knots"] = r.wind_speed
        observations.append(obs)
        
    traj_assessment = assess_trajectory(candidate.incident_id, observations)
    state.trajectory = traj_assessment.trajectory
    state.trajectory_status = "CALCULATED"
    
    # 2G - Needs
    affected_pop = canonical.get("affected_population") or (getattr(primary_report, "affected_population", None) if primary_report else None)
    displaced_pop = canonical.get("displaced_population") or (getattr(primary_report, "displaced_population", None) if primary_report else None)
    
    needs_input = NeedsAssessmentInput(
        verified_incident_id=candidate.incident_id,
        hazard_type=candidate.hazard_type,
        severity_score=severity_val,
        trajectory=state.trajectory,
        affected_population=affected_pop,
        displaced_population=displaced_pop
    )
    
    try:
        needs_reqs = assess_needs(needs_input)
        state.needs = [n.model_dump() for n in needs_reqs]
        state.needs_status = "CALCULATED"
    except Exception as e:
        state.needs = []
        state.needs_status = f"FAILED: {str(e)}"
        
    # 2H - Priority
    med_urgency = None
    rescue_urgency = None
    for n in state.needs:
        if n.get("category") == "MEDICAL": med_urgency = n.get("urgency_category")
        if n.get("category") == "RESCUE": rescue_urgency = n.get("urgency_category")
        
    priority_input = PriorityEngineInput(
        verified_incident_id=candidate.incident_id,
        verification_status=state.verification_status,
        severity_score=severity_val,
        trajectory=state.trajectory,
        affected_population=affected_pop,
        medical_urgency=med_urgency,
        rescue_urgency=rescue_urgency
    )
    
    try:
        priority_assessment = assess_priority(priority_input)
        state.priority = priority_assessment.model_dump()
        state.priority_status = "CALCULATED"
    except Exception as e:
        state.priority = None
        state.priority_status = f"FAILED: {str(e)}"
        priority_assessment = None
        
    # Assessment Persistence
    import sys, os
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
        
    from app.api.schemas.internal import AssessmentRecord
    from app.db.dependencies import get_assessment_repository, get_needs_repository
    from app.services.assessment_service import AssessmentService
    from app.services.needs_service import NeedsService
    
    idempotency_key = state.run_id
    
    assessment_service = AssessmentService(get_assessment_repository())
    needs_service = NeedsService(get_needs_repository())

    prev_latest = get_assessment_repository().get_latest_for_incident(candidate.incident_id)
    parent_id = prev_latest.assessment_id if prev_latest else state.parent_assessment_id
    
    record = AssessmentRecord(
        incident_id=candidate.incident_id,
        idempotency_key=idempotency_key,
        parent_assessment_id=parent_id,
        reassessment_reason=state.reassessment_reason,
        verification_status=state.verification_status,
        severity_status=severity_status,
        severity=severity_res,
        trajectory_status=state.trajectory_status,
        trajectory=traj_assessment.model_dump(),
        priority_level=priority_assessment.priority_level if priority_assessment else None,
        priority_score=priority_assessment.priority_score if priority_assessment else None,
        severity_model_version=severity_model_version,
        verification_policy_version="verification_v1",
        trajectory_policy_version=traj_assessment.policy_version,
        needs_policy_version="needs_policy_v1",
        priority_policy_version=priority_assessment.policy_version if priority_assessment else None
    )
    
    try:
        saved_record = assessment_service.save_complete_assessment(record)
        state.assessment_record = saved_record.model_dump()
        state.current_assessment_id = saved_record.assessment_id
        state.parent_assessment_id = parent_id
        
        if state.needs:
            needs_service.save_needs_from_assessment(
                incident_id=candidate.incident_id,
                assessment_id=saved_record.assessment_id,
                raw_needs=state.needs
            )
            
        if "FAILED" in state.needs_status or "FAILED" in state.priority_status:
            state.assessment_status = "FAILED"
        else:
            state.assessment_status = "ASSESSMENT_COMPLETE"
            
    except Exception as e:
        state.assessment_record = None
        state.assessment_status = f"PERSISTENCE_FAILED: {str(e)}"
        
    return {"state": state}

def assessment_comparison_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    import sys, os
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    from app.services.reassessment_service import ReassessmentService
    from app.db.dependencies import (
        get_assessment_repository,
        get_needs_repository,
        get_allocation_repository,
        get_action_repository
    )

    svc = ReassessmentService(
        assessment_repo=get_assessment_repository(),
        needs_repo=get_needs_repository(),
        allocation_repo=get_allocation_repository(),
        action_repo=get_action_repository()
    )

    cand = state.incident_candidates[0] if state.incident_candidates else None
    inc_id = cand.get("incident_id") if isinstance(cand, dict) else (getattr(cand, "incident_id", None) if cand else None)
    
    if inc_id:
        assessments = svc.assessment_repo.get_all_for_incident(inc_id)
        current_ass_id = state.assessment_record.get("assessment_id") if isinstance(state.assessment_record, dict) else getattr(state.assessment_record, "assessment_id", None)
        previous_assessments = [a for a in assessments if getattr(a, "assessment_id", None) != current_ass_id]
        prev_record = previous_assessments[-1] if previous_assessments else None

        curr_record_dict = state.assessment_record
        if curr_record_dict:
            from backend.app.api.schemas.internal import AssessmentRecord
            curr_record = curr_record_dict if isinstance(curr_record_dict, AssessmentRecord) else AssessmentRecord(**curr_record_dict)
            diff = svc.compare_assessments(prev_record, curr_record)
            state.assessment_diff = diff.model_dump()

            baseline_run_id, executed_allocs = svc.get_operational_allocation_baseline(inc_id)
            if baseline_run_id:
                state.operational_allocation_baseline_id = baseline_run_id

    return {"state": state}

def reallocation_decision_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    import sys, os
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    from app.services.reassessment_service import ReassessmentService
    from app.db.dependencies import (
        get_assessment_repository,
        get_needs_repository,
        get_allocation_repository,
        get_action_repository
    )
    from app.api.schemas.internal import AssessmentDiff, AllocationDiff

    svc = ReassessmentService(
        assessment_repo=get_assessment_repository(),
        needs_repo=get_needs_repository(),
        allocation_repo=get_allocation_repository(),
        action_repo=get_action_repository()
    )

    diff = AssessmentDiff(**state.assessment_diff) if isinstance(state.assessment_diff, dict) else state.assessment_diff
    alloc_diff = AllocationDiff(**state.allocation_diff) if isinstance(state.allocation_diff, dict) else state.allocation_diff

    status_str, is_req = svc.is_reallocation_required(diff, alloc_diff)
    state.reallocation_decision_status = status_str
    state.reallocation_required = is_req

    return {"state": state}

def optimization_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if state.verification_status != "VERIFIED":
        return {"state": state}
        
    if not state.incident_candidates:
        return {"state": state}
        
    cand_dict = state.incident_candidates[0]
    incident_id = cand_dict.get("incident_id")
    if not incident_id:
        return {"state": state}
        
    import sys, os
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
        
    from app.api.schemas.internal import OptimizationRequest
    from app.db.dependencies import (
        get_allocation_repository, 
        get_needs_repository, 
        get_resource_repository, 
        get_assessment_repository
    )
    from app.services.allocation_service import AllocationService
    
    allocation_service = AllocationService(
        allocation_repo=get_allocation_repository(),
        needs_repo=get_needs_repository(),
        resource_repo=get_resource_repository(),
        assessment_repo=get_assessment_repository()
    )
    
    req = OptimizationRequest(
        incident_ids=[incident_id],
        optimization_run_id=state.run_id
    )
    
    try:
        res = allocation_service.optimize(req)
        state.allocation_result = res.model_dump()
        state.errors.extend([f"Solver Status: {res.solver_status}"])

        from app.services.reassessment_service import ReassessmentService
        from app.db.dependencies import get_action_repository
        reassess_svc = ReassessmentService(
            assessment_repo=get_assessment_repository(),
            needs_repo=get_needs_repository(),
            allocation_repo=get_allocation_repository(),
            action_repo=get_action_repository()
        )
        base_run_id, prev_allocs = reassess_svc.get_operational_allocation_baseline(incident_id)
        alloc_diff = reassess_svc.compare_allocations(
            prev_allocs=prev_allocs,
            curr_allocs=res.allocations,
            baseline_run_id=base_run_id,
            new_run_id=state.run_id
        )
        state.allocation_diff = alloc_diff.model_dump()
        if base_run_id:
            state.previous_optimization_run_id = base_run_id
    except Exception as e:
        state.allocation_result = None
        state.errors.append(f"OPTIMIZATION_FAILED: {str(e)}")
        
    return {"state": state}

def coordination_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if not state.allocation_result:
        return {"state": state}
        
    alloc_str = json.dumps(state.allocation_result.get("allocations", []), default=str)
    prior_str = json.dumps(state.priority, default=str)
    
    plan = gemini_client.explain_coordination(alloc_str, prior_str)
    state.coordination_plan = plan
    
    return {"state": state}

def human_review_node(state_obj: GraphState) -> GraphState:
    # This node is interrupted before execution.
    # The human decision (APPROVED, REJECTED, REVISION_REQUESTED) is injected into state.human_approval_state
    return state_obj

def execution_node(state_obj: GraphState) -> GraphState:
    """
    Phase 4F Controlled Execution Node.
    Delegates to backend ExecutionService which independently validates PERSISTED database approval.
    """
    state = state_obj["state"]
    if state.human_approval_state != "APPROVED":
        return {"state": state}

    import sys, os
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    from app.api.schemas.internal import ExecutionRequest
    from app.services.execution_service import ExecutionService
    from app.db.dependencies import (
        get_approval_repository,
        get_allocation_repository,
        get_resource_repository,
        get_action_repository
    )

    inc_id = state.incident_candidates[0].get("incident_id") if state.incident_candidates else None
    req = ExecutionRequest(
        optimization_run_id=state.run_id,
        incident_id=inc_id,
        executor_id="GRAPH_NODE"
    )

    exec_svc = ExecutionService(
        approval_repo=get_approval_repository(),
        allocation_repo=get_allocation_repository(),
        resource_repo=get_resource_repository(),
        action_repo=get_action_repository()
    )

    res = exec_svc.execute_proposal(req)
    if res.status in ["EXECUTED", "ALREADY_EXECUTED"]:
        state.workflow_status = "EXECUTED"
    else:
        state.workflow_status = f"EXECUTION_FAILED: {res.status}"
        state.errors.extend(res.errors)

    return {"state": state}

def route_after_verification(state_obj: GraphState) -> str:
    status = state_obj["state"].verification_status
    if status == "VERIFIED":
        return "situation_assessment"
    elif status == "NEEDS_VERIFICATION":
        return "human_review"
    else:
        return "end"

def route_after_assessment(state_obj: GraphState) -> str:
    # After situation_assessment, compare assessment with previous if reassessment
    return "assessment_comparison"

def route_after_reassessment_decision(state_obj: GraphState) -> str:
    state = state_obj["state"]
    if state.reallocation_required:
        return "optimization"
    return "end"

def route_after_optimization(state_obj: GraphState) -> str:
    res = state_obj["state"].allocation_result
    if not res:
        return "end"
    return "human_review"

def route_after_human(state_obj: GraphState) -> str:
    status = state_obj["state"].human_approval_state
    if status == "APPROVED":
        return "execution"
    return "end"

def build_graph() -> StateGraph:
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("report_intelligence", report_intelligence_node)
    workflow.add_node("incident_detection", incident_detection_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("situation_assessment", situation_assessment_node)
    workflow.add_node("assessment_comparison", assessment_comparison_node)
    workflow.add_node("reallocation_decision", reallocation_decision_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("coordination", coordination_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("execution", execution_node)
    
    # Define edges
    workflow.set_entry_point("report_intelligence")
    workflow.add_edge("report_intelligence", "incident_detection")
    workflow.add_edge("incident_detection", "verification")
    
    workflow.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "situation_assessment": "situation_assessment",
            "human_review": "human_review",
            "end": END
        }
    )
    
    workflow.add_edge("situation_assessment", "assessment_comparison")
    workflow.add_edge("assessment_comparison", "reallocation_decision")

    workflow.add_conditional_edges(
        "reallocation_decision",
        route_after_reassessment_decision,
        {
            "optimization": "optimization",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "optimization",
        route_after_optimization,
        {
            "human_review": "human_review",
            "end": END
        }
    )
    
    workflow.add_edge("coordination", "human_review")
    
    workflow.add_conditional_edges(
        "human_review",
        route_after_human,
        {
            "execution": "execution",
            "end": END
        }
    )

    workflow.add_edge("execution", END)
    
    # Setup checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_review"])
    
    return app
