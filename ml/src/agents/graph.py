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
            try:
                parsed_raw = json.loads(raw)
                if isinstance(parsed_raw, dict):
                    if "source" in parsed_raw:
                        source = parsed_raw["source"]
                    if "source_record_id" in parsed_raw:
                        source_record_id = parsed_raw["source_record_id"]
            except Exception:
                pass

            hazard_raw = res.get("hazard_type", "UNKNOWN")
            if hazard_raw == "PROMPT_INJECTION_DETECTED":
                hazard = hazard_raw
            else:
                hazard = normalize_hazard_type(hazard_raw)

            report_dict = {
                "source": source,
                "source_record_id": source_record_id,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "hazard_type": hazard,
                "location_name": res.get("location"),
                "latitude": res.get("latitude"),
                "longitude": res.get("longitude"),
                "magnitude": res.get("magnitude"),
                "observed_at": res.get("observed_at"),
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
    candidates = cluster_reports(deduped_reports)
    
    # Store candidates and update the state's structured reports with their generated IDs
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
        
    from backend.app.api.schemas.internal import AssessmentRecord
    from backend.app.db.dependencies import get_assessment_repository, get_needs_repository
    from backend.app.services.assessment_service import AssessmentService
    from backend.app.services.needs_service import NeedsService
    
    idempotency_key = state.run_id
    
    assessment_service = AssessmentService(get_assessment_repository())
    needs_service = NeedsService(get_needs_repository())
    
    record = AssessmentRecord(
        incident_id=candidate.incident_id,
        idempotency_key=idempotency_key,
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

def optimization_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if not state.priority:
        return {"state": state}
        
    # Convert dicts back to Pydantic for Phase 2I engine
    req = ResourceRequirement(**state.needs[0])
    pa = PriorityAssessment(**state.priority)
    
    inv = [ResourceInventory(
        location_id="wh_1",
        resource_type="Water",
        category="WATER",
        quantity_available=500.0,
        unit="Liters"
    )]
    
    ctx = AllocationContext(
        optimization_run_id=state.run_id,
        incidents=[pa],
        requirements=[req],
        inventory=inv
    )
    
    res = optimize_allocation(ctx)
    state.allocation_result = res.model_dump()
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
    # This node acts as a no-op checkpoint where the graph stops.
    # The state is updated from the outside before resuming.
    return state_obj

def route_after_verification(state_obj: GraphState) -> str:
    status = state_obj["state"].verification_status
    if status == "VERIFIED":
        return "situation_assessment"
    elif status == "NEEDS_VERIFICATION":
        return "human_review"
    else:
        return "end"

def route_after_optimization(state_obj: GraphState) -> str:
    res = state_obj["state"].allocation_result
    if not res:
        return "end"
    if res["solver_status"] == "INFEASIBLE":
        return "human_review"
    return "coordination"

def route_after_human(state_obj: GraphState) -> str:
    decision = state_obj["state"].human_approval_state
    if decision == "APPROVE":
        # Resume the workflow logic depending on where we paused.
        # For simplicity in this demo, if approved, we assume it's resuming coordination.
        return "end"
    elif decision == "REJECT":
        return "end"
    return "end"

def build_graph() -> StateGraph:
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("report_intelligence", report_intelligence_node)
    workflow.add_node("incident_detection", incident_detection_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("situation_assessment", situation_assessment_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("coordination", coordination_node)
    workflow.add_node("human_review", human_review_node)
    
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
    
    workflow.add_edge("situation_assessment", "optimization")
    
    workflow.add_conditional_edges(
        "optimization",
        route_after_optimization,
        {
            "coordination": "coordination",
            "human_review": "human_review",
            "end": END
        }
    )
    
    workflow.add_edge("coordination", "human_review")
    
    workflow.add_conditional_edges(
        "human_review",
        route_after_human,
        {
            "end": END
        }
    )
    
    # Setup checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_review"])
    
    return app
