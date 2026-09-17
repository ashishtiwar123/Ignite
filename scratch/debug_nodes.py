import sys, os
sys.path.insert(0, os.path.abspath("backend"))

from app.db.dependencies import get_incident_repository, get_resource_repository, get_needs_repository
from ml.src.agents.state import AgentState
from ml.src.agents.graph import situation_assessment_node, optimization_node

inc_repo = get_incident_repository()
inc = inc_repo.get("56862ef4-18f4-4bfc-bcf6-795850362551")

print("Incident:", inc.incident_id, "Hazard:", inc.hazard_type)

state = AgentState(
    run_id=None,
    raw_reports=[],
    incident_candidates=[inc.model_dump()],
    verification_status="VERIFIED"
)

print("\n--- Running situation_assessment_node ---")
res_sit = situation_assessment_node({"state": state})
st1 = res_sit["state"]
print("Severity:", st1.severity)
print("Trajectory:", st1.trajectory)
print("Needs:", st1.needs)
print("Needs Status:", st1.needs_status)
print("Priority:", st1.priority)
print("Priority Status:", st1.priority_status)
print("Errors:", st1.errors)

print("\n--- Running optimization_node ---")
res_opt = optimization_node({"state": st1})
st2 = res_opt["state"]
print("Allocation Result:", st2.allocation_result)
print("State Run ID:", st2.run_id)
print("Errors:", st2.errors)
