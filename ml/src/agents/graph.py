import json
from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import schemas and engines
from ml.src.agents.state import AgentState
from ml.src.agents.gemini_client import GeminiAdapter

from ml.src.optimization.schemas import AllocationContext, ResourceInventory
from ml.src.needs.schemas import ResourceRequirement
from ml.src.priority.schemas import PriorityAssessment
from ml.src.optimization.engine import optimize_allocation

# Initialize clients
gemini_client = GeminiAdapter()

# Define the State graph dictionary
class GraphState(TypedDict):
    state: AgentState

def report_intelligence_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    structured_reports = []
    
    for raw in state.raw_reports:
        res = gemini_client.extract_structured_report(raw)
        if res:
            structured_reports.append(res)
            
    state.structured_reports = structured_reports
    return {"state": state}

def incident_detection_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    # We construct minimal Report instances to pass to Phase 2D
    # In a real system, we'd map StructuredReportOutput to the pipeline schema
    
    # Mocking the pipeline call for the demo graph, ensuring we use structured reports
    if not state.structured_reports:
        state.errors.append("No structured reports extracted.")
        return {"state": state}
        
    rep = state.structured_reports[0]
    candidate = {
        "verified_incident_id": "v_inc_001",
        "hazard_type": rep.get("hazard_type", "UNKNOWN"),
        "location": rep.get("location", "UNKNOWN"),
        "reports_count": len(state.raw_reports)
    }
    
    state.incident_candidates = [candidate]
    return {"state": state}

def verification_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if not state.incident_candidates:
        state.verification_status = "REJECTED"
        return {"state": state}
        
    cand = state.incident_candidates[0]
    
    # Fake verification logic based on extraction (mocking Phase 2E)
    # If Gemini detected prompt injection, it's rejected.
    if cand["hazard_type"] == "PROMPT_INJECTION_DETECTED":
        state.verification_status = "REJECTED"
    elif cand["reports_count"] >= 1 and cand["location"] != "UNKNOWN":
        state.verification_status = "VERIFIED"
    else:
        state.verification_status = "NEEDS_VERIFICATION"
        
    return {"state": state}

def situation_assessment_node(state_obj: GraphState) -> GraphState:
    state = state_obj["state"]
    if state.verification_status != "VERIFIED":
        return {"state": state}
        
    # 2C - Severity (Mocking the call)
    state.severity_score = 85.0
    
    # 2F - Trajectory
    state.trajectory = "RAPIDLY_WORSENING"
    
    # 2G - Needs
    state.needs = [{
        "requirement_id": "req_1",
        "verified_incident_id": "v_inc_001",
        "resource_type": "Water",
        "category": "WATER",
        "quantity": 1000.0,
        "unit": "Liters",
        "status": "CALCULATED",
        "rule_id": "WASH",
        "explanation": "Test"
    }]
    
    # 2H - Priority
    state.priority = {
        "priority_assessment_id": "pa_1",
        "verified_incident_id": "v_inc_001",
        "priority_score": 90.0,
        "priority_level": "CRITICAL",
        "explanation": "Critical priority"
    }
    
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
        
    alloc_str = json.dumps(state.allocation_result["allocations"])
    prior_str = json.dumps(state.priority)
    
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
